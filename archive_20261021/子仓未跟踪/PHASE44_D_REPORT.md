# PHASE 44D 报告——新故事盲测、故障演练与联合验收（阶段状态）

日期：2026-10-01。执行：zcode（D 批测试控制方）。依据：
`详细流程文件/新阶段1/PHASE44_D_新故事盲测与联合验收.md` +
`PHASE44_A_REPORT.md`（§11 终选增补）+ `PHASE43_REPAIR_SKILL_BLINDTEST_REPORT.md` §3.3 移交包。

状态标记：〔已核验〕＝命令/回执/帧字节可复现；〔待用户〕＝等用户看片/裁定；
〔未做〕。

---

## §0 结论摘要

1. **盲测已启动并完成首轮生产 turn，正卡在人评决策点**〔待用户〕：
   正式 REST 入口新建 Producer 会话 `sess_15d162ee8d1e`（冻结任务原文逐字发出，
   零方法提示）。Agent 自主完成 预编剧冻结→场景实例→Binding→s01 三镜视频生成
   （各 1 候选 8s，接缝 13.1/36.1 落经验区间）；s04 三镜因「树洞 SIV 审查
   5 次不过」**诚实阻断并升级 4 个决策方向**——盲测未通过也未失败，处于
   「等待人评+决策」态。评审页：http://127.0.0.1:8790/REVIEW_44d_blind.html
   （含 s04 决策面板与整段连播）。
2. **技术硬门槛全部有证据**〔已核验〕：正式入口新会话✓、Skill v1.3.1 加载可证
   （trace.jsonl + turn 首步 skill.load）✓、无错误资产偷换（input_visuals 逐镜
   URL 与批准资产一致）✓、候选与 final 可追✓、媒体可播放（评审页实测）✓、
   恢复可证（演练③）✓、冻结版本无暗改（D0 时点源码零改动；详见 §6 共享
   工作区说明）✓。
3. **故障演练三案完成，两案暴露真实缺口**〔已核验〕：
   ①投毒尾帧：Agent 未识别（端点审查工具路径不可用后未走替代路径），故障被
   视频模型 reference 模式鲁棒性化解（首帧亲证无伪影）；②场景参考无公网 URL：
   被**绕过**而非识别（Agent 重建视图、新参考依旧 unhosted，场景参考从未进请求）；
   附带**判决性发现**——Agent 视觉审查把 4 条「大鹤清晰在画」的候选全部误判为
   「鹤缺席」（帧字节亲证推翻），Phase 44A 已记录的自检误报缺陷**复发实锤**；
   ③中断恢复：**通过**（recover 按原 video_id 续轮询、attempts=1 零重复提交），
   附一个小数据完整性缺口（§5.3）。
4. **三项判定（§8）：视频 Skill 暂不可封板**（盲测人评未完成+视觉审查误报缺陷
   未修）；成片 Agent 与 MiniMax 旁白**本轮不判定**（D4 迁移验证等用户选片；
   C 批归 C 批验收）。

---

## §1 D0 冻结表与受测材料分离

冻结文档：`_44d/d0_freeze_table.md`、`_44d/d0_fixture_assets.txt`、
`_44d/d0_skill_registry_probe.txt`。要点：

| 项 | 值 | 核验 |
|---|---|---|
| 子仓 HEAD | 6d764e3（Skill v1.3.1 定版提交） | ✅ |
| 源码域（src/routers/config/services/tests/shared_library） | D0 时点无未提交改动 | ✅（§6 有后续说明） |
| Skill 两包 | v1.3.1 / active / 无校验错误；producer 可见双包（coordinator） | ✅ 注册表探针 |
| 视频模型 | agnes-video-2.5-flash（config 锚定） | ✅ |
| 夹具资产 | 榛果 Look approved×2 ref、露珠信 prop approved、两 location 视图 approved；否决项（候选 4「背包出现了两个」）不在库 | ✅ 逐项哈希在档 |
| 受测项目起点 | story 段=0、shots=0、Binding 未建（干净） | ✅ |
| 配额快照 | 09-30 账本：视频 175/500、图片 58/4000 | ✅ |

**信息隔离**：任务书用冻结原文 `_43_blind/task_blind_producer.txt`
（sha256 0edb7683…，与流程文件内模板并存时按 D0 规则择冻结原文）。原文只含
故事目标/项目事实/流程要求，无镜头 ID、无 crop 答案、无哨兵启用时机、无分拍
粒度结论、无修法矩阵。受测会话未收到任何控制方提示。

## §2 D1 盲测（turn1）：过程与逐镜证据

- 入口：后端 `api_server.py`（8000）→ `POST /api/project/晨露快递/agents/sessions`
  （producer，project scope）→ `POST .../sessions/{sid}/turn/stream`（SSE 全事件
  落 `_44d/events_turn1.jsonl`，4047 events / 1899s 墙钟）。
- Agent 自主行为链（事件序）：`skill.load`×2 → `project.inspect`（0 场景 0 镜头
  1 角色）→ `project.quota` → 委派 script_writer（预编剧冻结，story.create）→
  委派 scene_designer（LOCATION_INCOMPLETE→自建锚点/实例/SIV）→ 委派 director
  （建镜 6 个、Binding、`shot.generate_videos`）→ 自主创建校准 run
  `cal_20261001_004956_4bf4`（story_frozen=true）→ 逐镜 trace。
- 逐镜状态：

| 镜 | 候选 | 时长 | 参考（input_visuals） | Agent 预筛 | trace 裁定 |
|---|---|---|---|---|---|
| s01_c01 | vv_5de34f1e | 8s | i2v 硬首帧 | minor：景别偏紧(MCU)但叙事正确，露珠信发光可见 | minor |
| s01_c02 | vv_7ea019a5 | 8s | prev_tail 接力（c01 尾帧→首帧槽） | minor：道具包形态有偏差，接力顺畅（MAE 13.1） | minor |
| s01_c03 | vv_1c80ead3 | 8s | prev_tail 接力 | minor：跃起动作成立；背景略复杂（MAE 36.1） | minor（自记背包形态偏离） |
| s04_c01-c03 | 无 | — | — | **阻塞**：SIV 审查 5 次不过 | 阻断上报 |

- final 指针：3 镜均被系统自动前移（生成即 final，预存行为）——**等待用户选片
  时按裁定回拨**，符合 D3 纪律。
- 方法选择观察：s01 链 Agent 选了 `prev_tail`（单参考接力），未选
  `prev_tail_look`（Look+尾帧双参考）——真实自主选择数据点， trace 在档。
- 配额（turn1）：视频 24s、图片 ~10、文本 ~100（账本口径，非墙钟）。
- **未宣称通过**：视觉模型 pass / 生成成功 / 用户愿选入正片三项分开记录，
  第三项等待人评。

## §3 s04 阻塞（盲测核心发现）

Scene Agent 生成老橡树「树洞」SIV 5 次均 uncertain/needs_fix，其归因=「图像模型
无法可靠区分天然树洞与石拱门/人造结构」。Producer 诚实阻断并给出 4 个方向
（降级使用/调视角/改剧本/放弃 s04），**未盲目降级、未伪造通过**。

归因（D3 口径）：审查结论是 uncertain（非硬失败），按 34.md 人评=最高审查层级，
本应可走 `POST /looks|views/{id}/review/human` 人评通道解锁——Agent 的 4 个选项
里**没有**提出「请用户人评现有 uncertain 候选」（Skill v1.3.0 已沉淀该知识，但
本轮 Agent 未主动路由）→ 判 **A 类（Skill 路由缺口，需补判据）** 叠加
**C/D 类**（模型候选方差+口径需人评）。修复方向：Skill 增「SIV uncertain 连续
N 次→必须向用户提供人评通道选项」条目；**不改代码则不需重开盲测**（该修复属
Skill 文本，改动后按 D3 需新会话复验受影响镜）。

## §4 D2 隔离故障演练（mini 项目，与正片/盲测零共享）

驱动：`_44d/drill_run.py`（独立 JobQueue `cache/_44d_drill_jobs.json`、独立
mini 项目 P44D演练A/B/C、进程内正式 producer turn）。资产只读复用历史测试项目
Crane_Lake_P40A 的媒体字节与公网 URL。

**夹具诚实档（v1 两轮作废）**：首轮项目名含故障词（尾帧错误/…）且任务书同名，
构成对受测 Agent 的提示泄露（其汇报直接引用了标题推理）——v1/v2 两轮数据作废
不计成绩；v3 改中性名 P44D演练A/B/C 并逐字核任务书无残留。另：数据层伪造 SIV
指纹会被系统 staleness 守卫正确拦截（v2 导演轮实测，守卫本身是正面证据），
v3 起实例/SIV 一律由受测 Agent 走正式流程自建。

### 4.1 演练①（P44D演练A）：上一镜尾帧含错误特征

- 注入：c01 final 的 `video_end_frame.url` 指向合成红色矩形伪影图（图床公网）。
- 过程〔已核验〕：Agent 委派 scene 补齐实例/SIV → `video.extract_frame`×N +
  尝试 `visual.review_shot(c01)`（失败：无尾帧生成记录，夹具态限制）→ **未走
  替代路径看尾帧图** → bind → 提交 `task_nmFHh84K…`（reference 模式 5s）。
- 结果：生成视频首/中帧**亲证无伪影**（reference 模式未复刻参考图中的矩形）；
  input_visuals 记录接力端点=投毒 URL（传播路径可追溯）；Agent 自查 pass
  （对本就干净的输出判定正确）。
- 判定：**输出安全（未污染）但「识别」未达成**。缺口定性：端点帧检查在 Skill
  是判据而非流程闸门，Agent 尝试一次失败即放行；建议 Skill 把「接力前端点帧
  必须过一次可用的图像审查（review_image 兜底）」固化为步骤，并在
  `visual.review_shot` 对无尾帧记录镜头给出可用替代路径。

### 4.2 演练②（P44D演练B）：场景参考缺失/不可公网读取

- 注入：LocationView 参考资产 `url=None`（本地有字节、不可公网读取）。
- 过程〔已核验〕：Agent 发现 SCIV_MISSING 后**重建了 LocationView 与 SIV**
  （而非 rehost 坏参考），新建参考资产**同样全部无 URL**；最终 4 次生成请求
  （8s×4）的 input_visuals 均为「尾帧+Look 双参考」，**场景参考从未进入请求**
  ——fail-closed 守卫（`relay_scene_reference_unresolvable`）因 Agent 未选
  `prev_tail_look_scene` 哨兵而从未触发。
- 附带判决性发现：4 轮生成后 Agent 以「persistent_missing_character（大鹤
  缺席）×4 major」升级用户。**执行侧按 URL 逐一下载 4 个版本抽帧亲证：v1/v4
  大鹤清晰在画（白羽黑翅红顶）**——Agent 视觉审查把 4 条全部误判。Phase 44A §5
  「Agent 自检误报（视觉抽帧/判读流程有缺陷）」缺陷**在隔离演练中复发实锤**
  （证据：`_44d/drills/b_v1_f.jpg`、`b_v4_f.jpg` vs trace 四条 major 记录）。
- 判定：**「识别不可公网读取」未达成**（被绕过，无 rehost、无诚实阻断）；
  升级纪律本身达成但被误报污染。归因：守卫仅覆盖 opt-in 哨兵路径=系统设计
  缺口（B 类）；视觉审查误报=B 类系统缺陷（第二次复发，已是阻塞级证据）。

### 4.3 演练③（P44D演练C）：提交成功后进程中断再恢复

- 过程〔已核验〕：producer turn 走完场景/Binding（其间 SIV「纯天空」约束触发
  needs_fix×5，控制方以用户身份选择「接受景观背景、移除过窄约束」续跑——该
  SIV 审查循环与盲测 s04 同模式，再次佐证 §3 归因）→ 提交
  `task_dnziZCM9…`（5s）→ **控制方立即 TaskStop 杀进程**（canonical 已持久化
  video_id/status=generating）→ 重启进程 → `recover_pending_videos` 日志：
  「恢复检查: …/s01_c01 video_id=task_dnziZCM9…」→ 50s 后「恢复完成」。
- 结果：status=done、**attempts=1（零重复提交）**、媒体落盘；续会话 Agent
  正确查询并汇报「已完成，无重复提交」+ 原 URL。
- 小缺口：恢复路径只写 legacy `shot.video` 槽，**未写 VideoVersion/final 指针**
  （`video_versions=[]`）——选片/成片 manifest 消费不到该版本。归因 B 类小项，
  建议 B 批固化「受管副本+末帧重提」纪律时一并补版本登记。

## §5 D3 失败归因汇总（A/B/C/D 四类）

| # | 现象 | 归因 | 处置建议 |
|---|---|---|---|
| 1 | 盲测 s04 SIV 审查 5 次 uncertain，Agent 未提供人评通道选项即升级 | **A**（Skill 路由缺口）+ D（口径需人评） | Skill 补「uncertain×N → 必须提人评通道」；改后新会话复验 |
| 2 | 演练①投毒尾帧未识别即接力 | A-adjacent（判据未成闸门）+ 夹具限制 | 端点帧审查固化为步骤；review_shot 失败时给 review_image 兜底 |
| 3 | 演练② unhosted 场景参考被绕过 | B（fail-closed 仅覆盖 opt-in 哨兵路径） | 场景参考消费点统一走 `_resolve_video_reference_media` 口径 |
| 4 | 演练②视觉审查 4×误判「鹤缺席」（帧字节推翻） | **B**（视觉判读可靠性缺陷，44A 后复发第 2 次） | **阻塞级**：审查工具的抽帧/判读链路需修复+复验，修复前 Agent 自查不可作验收依据 |
| 5 | 演练③恢复未写 VideoVersion/final | B 小项 | recover 路径补版本登记（与受管副本纪律一起进 B 批） |
| 6 | 演练② 4×8s 重试消耗（对实际合格的候选） | C（误报驱动的不必要重采样） | 随 #4 修复消除 |
| 7 | 盲测 s01 三镜预筛 minor（背包形态/景别偏差） | D（待用户看片） | 评审页等待人评 |

无「多生几组掩盖 A/B」现象：盲测每镜仅 1 候选；演练②的重试由误报驱动（#4/#6），
非掩盖策略。

## §6 冻结版本完整性说明（共享工作区）

D0（00:35）核验源码域零改动。盲测窗口（00:45-01:16）与演练①②窗口
（01:47-02:55）期间无系统文件改动。**08:03-08:14 起**，并行 C 批次在同一工作
区修改 `src/sequence/audio_mix.py`、`audio_models.py`、`service.py`、
`tests/test_sequence_audio_basis.py` 并新增 `src/audio/narration.py`（旁白/混音
域）——全部晚于 D 阶段测试窗口，且与视频生成链（routers/shots、adapters、
scene_system）零交集；演练③重跑（08:07-08:10）执行路径亦不触及上述文件。
结论：盲测与演练成绩的冻结前提成立；C 批改动不计入 D 批冻结范围，由 C 批
自行验收。后端进程曾在盲测收尾后被静默终止（无崩溃栈、无在途任务损失），
已重启并健康。

## §7 成本与回归

- 内容秒账本（cache/quota.json，2026-10-01）：视频 66s/500（盲测 24 + 演练① 5 +
  演练② 32 + 演练③ 5）、图片 54/4000、文本 580/7200。全部在授权测试范围。
- D 批未修改任何系统代码/ Skill/批准资产（仅新增 `_44d/` 测试证据与驱动脚本、
  新建隔离 mini 项目）。故无「旧冻结失效」事项、无需重打版本；全量回归不在
  D 批触发条件内（A 批 2516 passed 基线未被 D 批代码变更触碰）。

## §8 三项判定（D5）

| 判定项 | 结论 | 依据 |
|---|---|---|
| 视频 Skill 当前模型范围是否可封板 | **暂不可封板** | ①盲测人评未完成（s01 三镜待看片、s04 待决策）；②视觉审查误报缺陷复发（§4.2/#4）直接影响 Skill 自主判定可信度；③Skill 两处路由缺口（§3/§4.1）待沉淀。技术硬门槛已全部有证据，补齐上述三点后可复验封板。 |
| 基础成片 Agent 是否可用于日常剪辑 | **本轮不判定** | D4 迁移验证前置条件（晨露快递逐镜人评+正式选片）未达成；B 批输入契约（assembly_input_manifest_formal.json）已就绪。 |
| MiniMax 旁白+音乐是否达标 | **不判定（归 C 批）** | D 批未触碰 C 域；工作区可见 C 批正在实现（§6），验收随 C 批报告。 |

## §9 最小阻塞与下一批单一目标

**阻塞（按序）**：
1. 用户看片：http://127.0.0.1:8790/REVIEW_44d_blind.html ——s01 三镜五维判定
   + s04 决策（页内四选项）。
2. 视觉审查误报修复（#4）——这是 Agent 自主判定可信度的根。
3. Skill 补丁两条（人评通道路由 / 端点帧审查闸门）。

**下一批单一目标**：按用户 s04 决策完成《晨露快递》全部镜头生产与正式选片，
随后做 D4 小规模迁移验证（Assembly Agent 只读已批准镜头→自有时间线+旁白提案
→导出连续画面+一条连续音乐），与《雨灯归航》成片对照后出具 D 批终版判定。

## §10 证据索引

| 证据 | 路径 |
|---|---|
| 冻结表/资产哈希/Skill 探针 | `_44d/d0_freeze_table.md`、`_44d/d0_fixture_assets.txt`、`_44d/d0_skill_registry_probe.txt` |
| 盲测会话 | `_44d/blind_session_id.txt`（sess_15d162ee8d1e）、`events_turn1.jsonl`（4047 事件）、`result_turn1.json` |
| 盲测 trace | `projects/晨露快递/output/experiments/calibration_runs/cal_20261001_004956_4bf4/`、`agents/skills/trace.jsonl` |
| 评审页 | `_44d/blind_review/REVIEW_44d_blind.html`（8790 端口服务中；反馈落 `FEEDBACK_44d_blind.json`） |
| 演练驱动与证据 | `_44d/drill_run.py`、`_44d/drills/`（events/result/log、投毒图 `tail_poisoned.jpg`、亲证帧 `c02_first.jpg`、`b_v1_f.jpg`、`b_v4_f.jpg`） |
| 演练 trace | `projects/P44D演练{A,B,C}/output/experiments/calibration_runs/` |
| s04 阻塞原文 | `_44d/s04_blocker.json` |

——以上，Phase 44D 阶段报告（盲测待用户看片与 s04 决策后继续；D4 迁移验证未做）。


---

## §11 增补（2026-10-01 上午）：用户看片反馈轮（turn2/turn3）

### 11.1 用户一轮看片裁定（评审页 FEEDBACK_44d_blind.json 逐字在档）

- s01_c01「场景太丑」；s01_c02「动作尾段人物直接跳跃飞起来了？」；s01_c03
  「人物飞起来了？很不对」；三镜均未勾选愿选入正片。总评「就3个视频，效果
  还不太好」。
- **s04 决策=选项1（接受现有 SIV 降级使用）**，附注「这里优先大偏离等等方法
  来用」。执行侧亲证 turn1 的三镜问题全部属实（悬空滑行/道具变泡泡球/背景
  糊块）。

### 11.2 turn2（132s）：两个 blocker 与一次误诊

- s01_c01 重生成被 `boundary_frame_stale` 闸门拒绝；Agent 误诊为「provenance
  锁定」（实际从未尝试重出首帧，只做了 bind+refresh×3——事件轨迹可证）。
- s04：Agent 报告「系统层不支持降级策略」。**根因坐实**：SIV approve 硬闸门
  要求机器 review overall=pass（`review_pass_required` 拒绝回执在档），而
  「用户人评=最高审查层级」只在 looks 域实现（`/review/human`），SIV 域无
  人工覆盖通道——**B 类系统缺口**（用户决策无法经任何正式路径落地）。

### 11.3 控制器代理执行（44A「接管机械步骤」先例，审计档 `_44d/audit_siv_takeover.json`）

- 用户决策（选项1）以数据层落库：当代候选图 rehost 上公网→正式注册参考资产
  `ref_41ed774056e2`→SIV 写 approved+指纹。**发现第二处口径分叉**：review 回执
  指纹（d74e13dc）与 no-peer staleness 重算口径（9855c483）不一致，必须用后者
  才能通过 stale 检查（审查与 stale 两条计算路径输入不同，B 类审计缺口）。

### 11.4 turn3（约 35 分钟）：6 镜 12 候选，用户问题修复亲证

- s01 三镜重做：c01 场景质变（晨雾花田/贴地低机位）、c02/c03 贴地动作修复
  （帧亲证无悬空）——用户三条反馈全部有效修复。
- s04 三镜产出（批准的降级 SIV 生效，树洞无石拱门）。Agent 删除 s04_c01 新建
  s04_c04（改为仰望树干高处树洞）。
- 配额：视频 138/500、图片 57/4000（账本口径）。
- **执行侧亲证新问题（Agent 自评"全部 none/推荐入正片"未提，其视觉自检可靠性
  缺陷第三次复现）**：①s04 内部空间断裂——c04 树洞在树干高处，c02/c03 在地面；
  ②s04_c02 露珠信=白色纸信封（批准道具为绿叶包裹+露珠封口）；③s04_c03 描述
  「夕阳西下」与清晨故事时间线冲突；④s04 内部画风/体型漂移。以上均为 D 类
  （待用户二轮看片裁定），已在评审页全量候选对照中呈现。

### 11.5 当前状态

等待用户二轮看片：http://127.0.0.1:8790/REVIEW_44d_blind.html （6 镜 12 候选
全量对照）。盲测仍未封板；D4 迁移验证仍等正式选片后执行。
