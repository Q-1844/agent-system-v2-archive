# IMAGE_SYSTEM_FULL_ACCEPTANCE_AND_PROVIDER_COMPARISON_REPORT.md
# 图片系统全链路验收 + Agnes/商汤 Provider 对比报告

**日期**: 2026-09-17 ~ 2026-09-18
**测试人**: 高级项目测试 + 工程执行（AI 协作）
**测试项目**: 4 个风格隔离项目（`验收A_2D动漫` / `验收B_半写实电影插画` / `验收C_国风插画` / `验收D_写实视觉开发`）
**Provider**: agnes-image-2.1-flash（现用主力） vs sensenova-u1.5-lite（本轮接入候选）
**证据预览站**: `animation-storyboard/_acc_preview/index.html`（113 张证据图，经 `http://localhost:8000/projects/...` 静态挂载浏览）
**原始证据**: `_acc_evidence.json`（逐事件）· `_acc_p3/p4/p5_results.json` · 各项目 `output/` 下 `generation_records.jsonl` / `review_records.jsonl` / `approval_records.jsonl`

---

## 一、代码审计结论：当前图片系统真实能力清单（第 1 问）

### 1.1 图片生成 provider（审计时点）
| Provider | 图片能力 | 审计结论 |
|---|---|---|
| Agnes（agnes-image-2.1-flash） | ✅ 唯一图片 provider | t2i + i2i（image_refs 双位置 fallback）、seed、URL 资产直通视频链 |
| SenseNova | ❌ **图片链路零参与**（仅 text_endpoint/Agent 模型切换） | 本轮已接入（见 §二） |

### 1.2 图片功能模块与生成入口（真实代码确认）
| 域 | 功能 | 入口 | 三阶段协议 |
|---|---|---|---|
| Resources | 角色资源图 Look（i2i，需 approved 角色参考） | `POST /looks/{id}/generate` | 生成→vision review→显式 approve ✓ |
| Resources | Composition（角色+道具合成图） | `POST /compositions/{id}/generate` | ✓ |
| Resources | Clothing（无独立生成端点；作为 Look 的服装绑定） | `POST /clothings` | 仅创建/绑参考 ✓ |
| Resources | **Prop：不存在图片生成端点**（仅参考图导入/审查/批准） | `POST /props` + `/references` | ✓ |
| Scene System | LocationView 多视角（camera_zone/look_direction/overhead 特判） | `POST /scene-system/views/{id}/generate` | ✓ |
| Scene System | SceneInstanceView 状态视图（base approved 强制 + prop 参考） | `POST /scene-instance-views/{id}/generate` | ✓ |
| Shots | 首帧/尾帧（BOUND 链路走 shot_binding→image_adapter；legacy 走 prompt_builder+角色参考） | `POST /shot/{id}/first-frame` `last-frame` | 批次+choose+rehost |
| Shots | 尾帧桥接、rehost（imgbb 公网化） | `first-frame/choose` `rehost` | — |
| 审查 | 六域 vision review（look/prop/composition/location view/sciv/agent director） | 各 `/review` 端点 | 恒走 Agnes-2.5-flash |
| 记录 | generation/review/approval 三类 JSONL 证据流（不存 base64） | — | append-only ✓ |
| 风格 | ProjectVisualProfile（fail-closed：未设置拒绝生成） | `output/project_profile.json` | Resources/Scene 域强制 ✓ |

### 1.3 Provider 注入点（本轮零架构改动的关键）
`generate_look_candidates` / `generate_composition_candidates` / `generate_location_view` / `generate_scene_instance_view` / 全部 review 函数**原生就有 `agnes_client` 注入参数**——只需一个接口对齐的商汤客户端即可全链路换 provider。

---

## 二、本轮接入的商汤图片链路（第 1 问补充 / 第 18 问修复项）

| 改动 | 文件 | 说明 |
|---|---|---|
| 新增 | `src/api/sensenova_client.py` | `SensenovaImageClient`：签名对齐 `AgnesClient.generate_image`；b64 直存免图床；refs 自动归一化为 data URI（公网图预下载）；`watermark=false`；自限速 3s |
| 新增 | `deps.get_sensenova_image_client()` / `deps.resolve_image_client()` | 惰性单例；未配 key fail-fast 503 |
| 小改 | `routers/shots.py` | first/last-frame 支持 `image_provider`（job.params）+ b64 落盘分支 + `generation_basis.image_provider` 记录 |
| 小改 | `routers/resources.py`、`routers/scene_system.py` | look/composition/location view/sciv 生成端点请求体支持 `image_provider`，透传服务层 |
| 修复 | `src/resources/generation.py` ×2、`src/scene_system/visual_basis.py`、`instance_view_basis.py` | basis.model.provider 原硬编码 `"agnes"` → 按 model_id 推断（证据可辨析性） |
| 编译/回归 | — | 全部 py_compile 通过；pytest 1924 passed（失败项为预存环境问题，见 §六.7） |

**实测能力边界（探针确认）**：商汤接受非方形 1312x736 ✓、seed 整数 ✓、顶层 `image` 数组 i2i（data URI/公网 URL）✓；恒回 b64 无公网 URL。

---

## 三、测试执行概览（第 2、3 问）

### 3.1 覆盖矩阵
| 功能 | Agnes | SenseNova | 结论 |
|---|---|---|---|
| 角色 hero（legacy t2i） | ✅ 4/4 项目 | ✅（经 Look 链路覆盖） | 覆盖 |
| Look 主造型（i2i） | ✅ 4/4 | ✅ 4/4 | 覆盖（A 一次过、B 2 轮、C/D 1-2 轮） |
| 换装 Look 变体 | ✅ 4/4（C/D 需重试或未过审属审查严格） | — | 覆盖 |
| 道具图（系统无生成端点→直生+系统审查链） | ✅ 4/4 | ✅ 4/4 | 覆盖；A/C/D approve 成功，B 3 连拒（见 §六.6） |
| Composition | ✅ A/C pass（D 多轮 uncertain）、A sensenova 未过审 | ⚠️ 抽样 | 覆盖 |
| **场景多视角（4 机位×双 provider）** | ✅ 16 组 | ✅ 16 组 | **核心对比，32/32 出图** |
| 分镜（legacy 3 镜×4 项目） | ✅ 12/12 | — | 覆盖 |
| 分镜（BOUND 场景参考固定） | ✅ D 1 镜 | ✅ D 1 镜 | 必做对比项覆盖 |
| 分镜多候选（variants=2） | ✅ A s01_c02（2 候选 30.5s） | — | 覆盖 |
| 分镜尾帧 last-frame（keyframes legacy） | ✅ A 18.4s | ✅ D 30.2s | 覆盖（双 provider） |
| 分镜尾帧（BOUND i2i） | ✅ D 54.2s | ✅ D 38.3s（修复后） | 覆盖（双 provider） |
| rehost 公网化 | ✅ 商汤本地候选 → imgbb 成功 | — | 商汤图进视频链的桥实测可用 |
| 角色图生图 regenerate-view（side） | ✅ A 15.2s / D 25.9s | — | 补测覆盖 |
| 角色 generate-chain 链式三视图（t2i+2×i2i） | ✅ A 37.8s / D 54.3s | — | 补测覆盖 |
| 角色 generate-sheet 设定图（1 图+裁剪+抠图） | ✅ A 13.3s / D 19.5s（三段抠图全成功） | — | 补测覆盖 |
| image-to-image 参考再生成 | ✅（Look/Composition/BOUND/角色链/尾帧全部 i2i） | ✅ | 覆盖 |

### 3.2 四个风格项目内容
- **验收A_2D动漫**（2d_animation）：角色 Ling（银发剑士）· Look main_uniform/night_variant · 道具 curved_saber · Composition hero_with_saber · 地点 Mountain Post Station（东门/西烟囱/北楼梯/南拴马桩）· 3 镜分镜
- **验收B_半写实电影插画**（stylized）：Karl · field_jacket/summit_variant · brass_compass · Cliff Beacon Station · 3 镜
- **验收C_国风插画**（stylized/guofeng）：Qinghe · jade_robes/travel_variant · oil_paper_umbrella · Composition ✓ · Canal Stone Manor · 3 镜
- **验收D_写实视觉开发**（photorealistic）：Mara · expedition_parka/station_variant · field_recorder · Polar Observation Outpost · 3 镜 + **BOUND 场景参考固定分镜 × 双 provider**

未覆盖/系统不存在的功能（如实声明）：Prop 生成端点（不存在）；角色"表情/姿态变化"独立端点（不存在，变体经 Look+seed 承载）；视频链（本轮范围外）。

---

## 四、核心结论：场景多视角（第 8 问，本轮重点）

### 4.1 量化对比（32 组，每机位同 seed、同 prompt builder、同审查模型）
| 指标 | Agnes 2.1 flash | SenseNova u1.5-lite |
|---|---|---|
| **一次过审率** | **8/16 = 50%** | **14/16 = 87.5%** |
| 侧视（side_east，见唯一门） | A ✓(2轮) B ✗2轮 C ✗2轮 D ✓(1) | **4/4 全过，3 组一次过** |
| 背视（rear） | 4/4 一次过 ✓ | 4/4 一次过 ✓ |
| 正俯视（overhead/nadir） | C/D 一次过；A 2轮；B ✗2轮 | **4/4 全过一次**（真 nadir，无航拍泄漏） |
| hero | A/C 出；B/D 各 2 轮 | A/D 2 轮（A 首轮为审查解析失败非图问题）；B/C 一次过 |
| 需 2+ 轮才过的机位数 | 8 | 2（其一为审查解析问题） |

### 4.2 与上一轮专项报告的关系（重要修正）
上一轮《场景模块多视角生图测试报告》结论"Agnes 侧/背视 100% 失效"是**纯 t2i/措辞实验**下的表现。本轮发现：**系统链路本身显著修复了 Agnes 的方位缺陷**——`select_reference_views` 自动把已批准 hero 图作为 i2i 参考 + `location_prompt` 的 cross-view 指令 + anchor 语义，使 Agnes 背视 4/4、侧视 2/4、俯视 2/4 可过审。
**结论修正为：Agnes 的机位问题在裸 t2i 下是硬边界；在系统参考链路下可部分克服但稳定性仍明显弱于商汤。**

### 4.3 最终结论
- **商汤在场景多视角任务上全面更优**：一次过审率高 37.5 个百分点；侧视/俯视（最考验机位控制的两类）优势最大；对措辞/机位句式鲁棒。
- Agnes 失败模式集中在：侧视正面泄漏（B/C 两项目 2 轮未过）、俯视航拍化（B 两轮未过）、风格漂移连带机位不达标。
- **系统审查链（Agnes-2.5-flash vision）对两 provider 一视同仁且拦截有效**：32 组中确证拦截了 Agnes 的正面泄漏/航拍化，未发现放行假图。

---

## 五、其他任务对比结论

### 5.1 角色资源图（第 10 问）
- Look 生成（i2i，角色 approved 参考）：**Agnes 4/4 过审**；商汤 4/4 出图且过审（A 样本 ref_87deb6044b26、B ref_cf845ccb3016、C ref_856c09c64905、D ref_ffcc00d64ba7），但商汤出图**偏精细插画质感**，2D 项目（A）下与项目风格匹配度略逊 Agnes。
- 换装变体：Agnes 在 C/D（服装细节审查）出现 needs_fix（袍色偏移/手套穿错），重试后 C 过、D 未过——反映的是**审查严格 + i2i 服装遵循的普遍难度**，非单 provider 问题。
- **结论：角色资源 Agnes 略优**（风格贴合 + 链路成熟 + 速度快约 2 倍），商汤可用。

### 5.2 道具资源图（第 11 问）
- 直生对比（同 prompt 双 provider）：Agnes t2i 约 8-12s，商汤约 20-45s；质感两侧均可用。
- 系统审查链 approve：A/C/D 的 Agnes 图全部 approve 成功；**B 项目（黄铜罗盘）3 连拒**——拒因集中在 `project_style_consistency`（素底设定图 vs 项目整体风格），见 §六.6。
- **结论：道具 Agnes 更稳**（快 + 与审查链已磨合）；商汤质量相当但更慢。

### 5.3 场景图（第 12 问）
- 场景 hero + 状态视图：两侧均可用；商汤在空间布局准确度上更稳（B/D 的 hero 首轮 needs_fix 两侧各 1 次，均方位类细节）。
- **结论：场景图商汤略优**（与多视角结论一致），Agnes 可用。

### 5.4 分镜图（第 13 问）
- legacy 分镜（12 镜 Agnes）：全部成功，角色参考 i2i 链路稳定；发现风格词 bug（§六.3）。
- **BOUND 场景参考固定分镜（任务书必做对比）**：D 项目 binding（READY：approved sciv + look + visual_profile 指纹）下，Agnes 35.3s / 商汤 27.6s 均成功；`generation_basis` 正确记录 `image_provider`、`resolved_scene_instance_view_id`、`visual_profile_fingerprint`。
- 质感观察：使用场景参考后，Agnes 写实分镜质感**未下降**（i2i 参考提升场景一致性）；商汤在写实域与参考遵循同样稳定。
- **结论：分镜两侧相当**；Agnes 胜在与视频链衔接（URL 资产直通 + 图床已磨合），商汤胜在速度（此样本）与空间遵循。

---

## 六、问题分类：系统 bug vs Provider 边界（第 14、15 问）

### 已修复（本轮"问题→修复"记录）
1. **SenseNova 图片链路不存在** → 新客户端 + deps + 5 端点 provider 覆盖 + b64 落盘（§二）
2. **generation basis `model.provider` 硬编码 "agnes"**（4 处）→ 按 model_id 推断，商汤证据可辨析
3. **legacy 分镜风格词与 visual_profile 脱节（真 bug）**：`StyleAnchor.art_style` 默认 `"anime, cinematic composition"` 被所有分镜 prompt 拼接——写实项目 D 的分镜 prompt 实际带 "anime"。本轮以项目数据修复（style 对齐 visual profile）；**建议**：legacy 分镜链路接入 visual_profile 编译指令（涉及 prompt_builder 改造，属下轮小迭代）
4. **分镜 first/last-frame 不支持 provider 覆盖与 b64** → 已补（含 Candidate(url=None) 合法性确认）
5. **【补测发现·已修】last-frame 端点 body 解析失效（真 bug）**：签名 `Optional["LastFrameRequest"] = None`（前向引用+默认 None）导致请求体被静默丢弃，`image_provider` 恒回落 agnes——**商汤尾帧实际烧的是 Agnes 配额且证据错误归因**。修复为 `Optional[LastFrameRequest] = Body(None)`，重测 provider 记录正确。⚠️ 对比测试时若早于此修复的 last-frame 结果需重新生成。
6. **【补测发现·已修】sensenova 客户端 refs 预下载无重试无降级（真 bug）**：BOUND 尾帧 refs 含多张远程图（首帧 imgbb + approved 场景资产），`_normalize_refs` 下载 `httpx.ConnectError` 直接失败 → job 静默失败（error 为空）。修复：3 次退避重试 + 耗尽后降级直传原 URL。修复后 BOUND 尾帧 sensenova 38.3s 成功。
7. 验收脚本自身缺陷（review 归属错、幂等缺、非法 binding relation、evidence 重复 kwarg 等）→ 已修，不影响系统

### 系统行为确认正确（非 bug）
6. **BOUND fail-closed**：binding 缺 approved SceneInstanceView 时拒绝并给出明确 hint（"该方向需 SceneInstanceView，先在 Scene System 生成并批准"），绝不 fallback legacy——设计正确；建议前端加引导。
7. **composition binding relation 枚举校验**（`[attached,carried,held,near,worn]`）fail-fast 正确。
8. **视觉审查链有效**：确证拦截 Agnes 侧视正面泄漏×2、俯视航拍化×1、道具双刃剑（A 项目真实缺陷）、罗盘 blueprint 化；未发现放行假图。

### Provider/生态边界（记录，不属系统 bug）
9. **Agnes t2i seed ∈ [-1,999]**（400 报错明确）；i2i 路径放行大 seed（疑似忽略）——建议写入 AGNES_API_FACTS，多候选 seed+i 策略仅对 t2i 有效。
10. **prop 审查的 `project_style_consistency` 维度与素底道具设定图语义冲突**：道具参考图本质是"干净实体图"，审查却按项目整体风格判卷 → B 项目 3 连拒。建议：prop_review 的风格维度改为"道具本体风格语言"或素底图豁免（review prompt 调整，小改）。
11. **商汤无公网 URL 返回**（恒 b64）：进视频链（需公网 URL/imgbb rehost）多一跳；审查链已验证支持 data URI，无碍。
12. **vision review 偶发 JSON 解析失败**（A hero 商汤首轮 uncertain，重试即过）——审查稳定性建议重试包装。
13. **pytest 与运行中后端并发**时 fixture `FileExistsError`（Windows 目录锁，`projects/_test_story` 等）——测试卫生问题：跑 pytest 前停后端或 fixture 加幂等重试。
14. Agnes 首日 503"文生图队列已满"（服务端拥堵，重试恢复）——上游稳定性记录。

---

## 七、Provider 选择建议（第 4-7、16、17 问）

### 7.1 直接回答
- **Q16 默认 provider 是否切换：不建议全局切换；建议"按域路由"**（任务书 §十一.17 的选项 2+4 组合）：
  1. **scene_system 域（LocationView/SceneInstanceView 多视角）→ 默认切商汤**（87.5% vs 50% 一次过审、nadir 真 90°、措辞鲁棒；成本侧商汤为公测免费去水印）
  2. **Resources（Look/Composition）与 legacy 分镜 → 保持 Agnes**（i2i 身份链路成熟、速度快 2 倍、URL 资产直通视频/图床链、风格贴合 2D 项目）
  3. Agnes 保留视频/配音全链
- **Q4/Q5 Agnes 强/弱项**：强=实体渲染（角色/道具/服装）+ 跨视角身份一致 + 风格依从（i2i）+ 速度快 + URL 资产生态；弱=离面机位控制（系统链路可部分缓解）、俯视航拍化、t2i seed 上限、偶发 503。
- **Q6/Q7 商汤强/弱项**：强=相机站位与方位控制（侧/俯/背）、空间布局准确度、措辞鲁棒性；弱=无公网 URL（视频链多一跳）、速度慢 2-3 倍、2D 动漫风贴合度略逊、生态未与视频链磨合。

### 7.2 落地方式（建议下轮小迭代，非本轮）
- `config.yaml` 增加 `image_routing: {scene_system: sensenova, resources: agnes, shots: agnes}`（或复用 `text_provider` 的模式），服务端点默认读路由、请求级 `image_provider` 仍可覆盖（本轮已具备请求级覆盖能力）。
- 商汤侧补充：b64→imgbb rehost 的可选桥（进入视频链前自动公网化）。

---

## 八、遗留修复/优化清单（第 18 问，按优先级）
1. **P1** legacy 分镜链路接入 visual_profile（消除 art_style 脱节根因，当前仅数据级规避）
2. **P1** prop_review 风格维度对素底设定图的判卷口径调整（解除 B 类项目道具审批阻塞）
3. **P2** 商汤 b64→imgbb 桥（打通商汤图进视频链）
4. **P2** vision review 的 JSON 解析失败重试包装（1 次重试即可）
5. **P2** review prompt 的方位表述中性化（延续上轮建议，本轮侧视拦截确证其价值）
6. **P3** AGNES_API_FACTS 补记：t2i seed ∈ [-1,999]、i2i 大 seed 放行现象
7. **P3** pytest fixture 幂等（停后端或 rmtree 重试）
8. **P3** `_e2e_*` 老脚本清理（避免脏 anchor 类历史问题复发）

---

## 九、验收结论（第 19 问）

**通过（附条件）**。
- 全链路（项目创建→visual profile→资源三阶段→场景多视角三阶段→BOUND 分钉→choose）在 4 个风格项目上真实跑通，32+12+2 组真实生成、全部落盘可溯（JSONL + basis 指纹 + provider 记录）；审查/批准/撤销链行为正确；fail-closed 语义（visual profile、BOUND、binding 枚举）经受住实测。
- 条件一：legacy 分镜风格脱节（§六.3）需按 P1 排期根因修复；
- 条件二：多视角域切换商汤的建议如采纳，需按 §7.2 做一轮小路由改造 + 回归（本轮已具备全部请求级覆盖能力，改造面很小）。
- 商汤侧经本轮已**完整接入系统**（客户端/服务层/HTTP/分镜 JobQueue 全路径可用），后续对比测试可直接用 `image_provider` 参数进行，无需再改代码。

## 附：证据索引
- 预览站：`animation-storyboard/_acc_preview/index.html`
- 驱动脚本：`_acc_p2_projects.py` / `_acc_p3_resources.py` / `_acc_p4_multiview.py` / `_acc_p5_shots.py` / `_acc_p7_extra.py`（角色链+尾帧链补测）/ `_acc_p6_gallery.py` / `_acc_p6_stats.py` / `_acc_smoke_http.py`（幂等可重跑）
- 探针：`_probe_acceptance_keys.py` / `_probe_sensenova_caps.py`
- 事件级证据：`animation-storyboard/_acc_evidence.json`（150+ 条）
- 商汤接入 diff：`src/api/sensenova_client.py`（新增）、`deps.py`、`routers/shots.py`、`routers/resources.py`、`routers/scene_system.py`、`src/resources/generation.py`、`src/scene_system/visual_basis.py`、`src/scene_system/instance_view_basis.py`
