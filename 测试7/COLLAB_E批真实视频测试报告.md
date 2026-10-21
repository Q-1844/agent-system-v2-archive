# E 批真实视频测试报告（R1.1 路径验证）

日期：2026-10-19（北京时间早；LA 日历仍 10-18——**放行依据=配额所有者显式指示"配额已重置，继续完成"，如实记录偏离**）。
分支：生产 `feat/phase55-collab-parallel@da123e2`（R1.1+R1.1.1）。R2 实验组：**not_implemented**（B 批纵切片未接真实 settlement，不做真实验证，不冒充）。

---

## 一、E0 放行核查（全过，证据 `D:\isolated\evidence\e_batch\E0_preflight.json`）

| 项 | 结果 |
|---|---|
| 日期 | 北京 10-19 ✓ / LA 10-18（用户显式授权放行，见上） |
| 契约 | video=agnes-video-2.5-flash（唯一模型）· i2v/multi/text + seconds 4-12s · 720P · 8n+1 帧 · RPM 1 · inflight 模式默认 1 |
| 配额 | Token Plan 500s/日，账本按日自动 rollover（昨日 480 已归档）；本机口径非服务端真值 |
| 后端 | health ok · combo_recommended **v2.1.0 available=True 零缺因** |
| 冻结输入 | P56_P2_SIGNAL（dfbfc4d00e78）：3 角色 Look（9 图）+ 4 首帧批准版 + 绑定，**13 项资产哈希存档，生图预算 0** |
| 台词 | `native_av.spoken_language="Mandarin Chinese"` 冻结包已配 ✓ |

**计划对 04 文档的修正（如实）**：① 冻结包镜头为 **8s/镜**（193 帧），非计划假设的 4s——总消耗仍在上限内；② A 项目用 P2 冻结包实拍（结构同构：链 s01_c01→c02→c03 ↔ A01→A02→A04，独立 c04/c05/s02_c01 ↔ A03）；③ **B 项目 not_run(blocked)**——M 族（林远/苏然/标本）项目视频全 done 非待测冻结包、无已批准中景参考、无台词输入；补齐需生图但预算 0，按 E0.6 停止该分支并记录所缺资产。

## 二、冒烟（1 次成功 + 1 次 fail-closed）

| 任务 | 结果 | 消耗 |
|---|---|---|
| 首次 `608b54179285` | **fail-closed**：`speaker_not_in_characters`（冻结源台词前缀「队员甲」≠ 角色全名「突击队员甲」，17.md §8 reject 语义拒发） | **0** |
| 修正后 `e321ce7adb22` | **done 162s**：版本回执 vv_730e74328751 + provider_task_id + submission_intent + input_manifest v1 全链 + 本地文件 sha256 + 末帧提取托管 | 8s |

冒烟发现即修复：克隆包对话前缀短名→全名（3 处 ×2 项目），E0"台词与精确名字一致"检查点实战生效。

## 三、R1.1 验证组（run_22e43019c8，combo v2.1.0 + approved_package）

**墙钟 31.5min**；6 镜全部产出（每镜 8s）；9 个视频任务中 3 次 fail-closed 零浪费。

| 镜 | 结果 | 机器终审 rvw_9390d943 | 过程要点 |
|---|---|---|---|
| s01_c01 | ✓ 169s | **incomplete**：景别错配（MCU vs full）+构图偏差——政策 v2 降次维，不算硬错 | 链首独立开场 |
| s01_c02 | ✓ 268s | **硬错 missing_character** → 决策单待答复 | 接力 c01 末帧；首试 `reference_media_unresolvable`（视频参考缺公网 URL）→ fail-closed → 正式 rehost 后重试成功 |
| s01_c03 | ✓ 221s | **pass** | 接力 c02 末帧（两棒链整体一致） |
| s01_c04 | ✓ 160s（第 3 次） | **pass** | **2 次 fail-closed**（boundary_frame_stale：冻结源首帧批次缺 BOUND 凭据）→ **Producer 自主 BOUND 重锚**（3 张图，新批次 ff_27946388 全凭据 READY）→ 成功 |
| s01_c05 | ✓ 379s | **硬错 missing_character** → 决策单待答复 | 独立镜 |
| s02_c01 | ✓ 545s | **pass**；native 对白生效（speaker 精确匹配+乙静默指令） | 独立镜含台词 |

**消耗**：视频 **56s**（上限 74）/ 图 3 张 / 文本 100 次。视频任务 7 次创建（6 成功+2 次.fail-closed c04+1 次.c02——失败 3 次全部 provider 调用数 0）。有界修复：**0 次重生成**——missing_character 属身份类错误，修复闸直接升级决策单（不无依据抽卡，配额零浪费，这正是 Phase56 A 机制设计）。

## 四、E5 六问逐答

1. **候选闭环是否成立**：R1.1 口径成立——每镜版本独立留存（video_versions）、版本回执含 generation_basis+input_manifest 快照、失败任务 unattached 保护性记录、终审按精确 version 校验。R2 的 promotion/过渡池正式接纳=**not_implemented**（如实）。
2. **确定性派发是否消除空等**：本组由 Producer v2.1 批量提交模板驱动——4 就绪镜批量入队、**c02/c03 等上游末帧未提前提交**（依赖纪律正确）；程序化派发属 R2（未实现），无数据。
3. **子 Producer 是否自主切 skill**：Producer 回合 30.3min，授权五族内自主执行 director/assembly 工具（重锚/重生成/接续校准），未越域调用 Script Writer/Resource/Scene（其汇报自证 + 零越权写）；skill.load 实际执行链属 C 批（未实现）。
4. **审核是否与执行重叠**：✓ LiveReviewSession 流水化在 producer_turn 内运行（c01 生成时审核已开跑）；终审 71s 独立收口。
5. **是否出现冲突/重复/归属污染**：无。重复任务（c04×3/c02×2）全部可溯源（同 shot 不同 attempt，失败原因各异）；9 任务/6 版本归属干净；用户选版无竞争场景。
6. **画面出现什么问题**：c01 景别/构图偏差（机器降次维）；c02/c05 机器判缺人（**决策单 2 张待用户裁决**：豁免当前版本 or 换输入策略重生成，动用补测预算 ≤6s/1 次）。

## 五、留档与待办

- 证据：`D:\isolated\evidence\e_batch\`（E0 预检/冒烟两轮证据/组跑证据/review 摘要/批次对比/逐任务时长）。
- **看片页：http://127.0.0.1:8792**（`测试7/e_review_server.py`，三分区：完整素材 7 镜/保留建议/排除说明；FEEDBACK_E_R11.json 落盘）。
- 待用户：①看片定版；②c02/c05 决策单答复（豁免或换策略重生成 ≤6s）；③补测预算是否动用。
- 系统发现（转 B/C 批 backlog）：冻结包克隆应校验"台词前缀=角色全名 + 首帧批次 BOUND 凭据"两处冻结完整性（本次两处都由运行时 fail-closed 兜住——机制正确，但冻结时可提前拦截省一轮）。

## 六、结论

**R1.1 真实路径验证：通过（带 2 张待裁决决策单）**。6/6 镜产出、3 镜机器 pass、链式接力与末帧物料全通、对白控制生效、4 次 fail-closed 全部零浪费、修复闸防抽卡生效。R2 各能力 not_implemented。全系统验收仍待用户看片 + B/C/D 批落地，与本轮验证分开表述。
