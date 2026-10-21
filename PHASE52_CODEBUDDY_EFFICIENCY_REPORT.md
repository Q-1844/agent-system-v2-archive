# PHASE52 CodeBuddy 系统效率专项报告

执行日期：2026-10-11。默认智能体：GLM-5.3-Flash（思考开启），CodeBuddy 客户端。
仓库：`C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard`。

## 1. 执行概要

| 阶段 | 状态 |
|---|---|
| A. 核验与冻结交接 | **完成**。独立分支已建，正式 Skill 逐字导出，剧本/分镜/合格素材冻结，manifest+status 已交付 |
| B. 可解释时间线 | **完成**。PHASE52_TIMELINE.csv（700 行，三真实数据源合并，时区口径已校正并标注） |
| C. 有效成果/重试/恢复 | **核验通过**（机制完整，238 项回归通过）；修复 1 个证据确凿缺陷 |
| D. 已确定步骤及时推进 | **核验通过**（P51_E run2 真实事件链证明连续推进） |
| E. 查询与限流 | **核验通过**（自适应轮询已在 Phase51 A 落地；分桶限流与上游 429 来源可区分） |
| F. 图片与恢复测试 | **完成**（真实图片 2/2 链路通 + E01-E20 逐项结论，见 PHASE52_IMAGE_AND_RECOVERY_RESULTS.md） |
| G. WorkBuddy 建议 | **已评估**（5 条 WB-EFF 建议逐项裁定，见 §6） |

**本轮不扩大生成并发**（AGNES_VIDEO_INFLIGHT 默认 1 未动）；**未提交任何新视频**（配额 488/500s 实证不足）；保留了六 Agent、canonical/OCC、receipts、truth gates、锁与正式 Skill。

## 2. 冻结交接（A 项）交付

- 交接目录：`PHASE52_FROZEN_INPUTS\`（44 个文件全部只读冻结，逐文件 SHA-256 见 manifest）
- `PHASE52_BASELINE_MANIFEST.json`：3 个 Skill 包（full-story-relay-calibration v1.6.0 / keyframes-bridge-repair v1.4.0 / candidate agnes-production-craft v0.9.0）逐字副本+哈希；Skill 绑定清单（director=primary_executor 100 / producer=coordinator 80 / script_writer=contributor 60 / character_designer=conditional 40 / scene_designer=conditional 40）；基线 commit `ca02635a`；配置指纹（config.yaml sha256 `9f2286a1…`，.env 仅哈希不导出内容）；生成账号非敏感标识
- `PHASE52_INPUTS_STATUS.md`：剧本+锁定分镜（20 镜，frozen_from run_b25f5b900c3b）+ 4 个角色 Look 已批准参考齐备 → WorkBuddy 主测试为**同分镜冻结输入测试**
- 缺失项如实记录：渔船批准参考本地缺失 → 已从原始 COS URL 下载导出并**实图视觉核验通过**（无人渔船、右舷 3/4、黄昏海面，与 look 元数据一致）；海怪 look generation_status=failed 但有 1 张已批准参考，以批准参考为准
- 导出为读取复制，未改写 Skill 任何内容（哈希可对账）
- **交接完整性已实测**：WorkBuddy 工作副本（PHASE52_WORKBUDDY_TEST\skill_copy）与冻结基线逐文件哈希对账 **19/19 一致**（含 13 个 Skill 文件与 6 个素材/分镜文件），未见中途改写。其 frames/videos/trace/适配文档为 WorkBuddy 自有产物，不在基线清单属正常
- 勘误：manifest 初版 files 数组漏列 23 个 Skill 文件条目（导出脚本 `copy_tree_verbatim` 未把条目写入数组；磁盘文件本身始终正确）。已重建 files 数组为冻结目录完整实际清单（43 项，逐项实算 SHA-256，`manifest_rebuild_note` 字段留痕）

## 3. 效率机制核验结论（B–E 项）

八项机制在仓库中**均已实现且有回归覆盖**（这是此前 50+ 轮的成果；本轮逐文件读码核验而非重建）：

| 机制 | 实现位置 | 本轮核验 |
|---|---|---|
| 有效成果复用 | `src/workflow/outputs.py` verify_node_outputs：require_new 跨 attempt 真实写入累计（writeSource=prior_attempt）、allow_verified_reuse 服务端核验（存在+hash+文件+审批）、excludeVersionIds 防旧产物绕过修复目标 | 读码+回归 23 项通过 |
| 完成判定 | 节点成功=真实结果+receipt+产物+完成校验（AGENT_EXPECTED_DOMAINS 域命中 + 目标级 outputs 核对）；fail-closed（项目事实不可读=诚实缺项） | 读码+回归 |
| 已知任务恢复 | `recover_pending_videos`（先 poll 不重提交）+ `AgentTaskSettler.recover_tasks`（task↔job 对账，exact video_id 才 fallback 结算，不 falsely complete） | 读码+真实日志取证（completed>submitted 即恢复路径实证）+回归 |
| 未知提交核对 | 无 video_id 显式留原状态+告警，重提交标 `previous_submit_uncertain`，不盲目重发 | 读码 |
| 晚到回执 | Phase51 C run 窗口（video_version createdAt≥window_start），旧版本不得借 shot 成员资格冒充本 run 产出（run_36919eb5a073 实证防住 14 镜污染） | 读码+注释内实证记录 |
| 及时推进 | 顺序调度权威+scope 闸+attempt 连续派发；P51_E run2：02:30→05:02 九节点连续推进（TIMELINE S2 段） | 真实事件链取证 |
| 轮询与限流 | poll_video 自适应（前 60s 每 5s→之后 20s，Phase51 A 已修 24req/min 超 text 桶问题）；RateLimiter 分桶令牌桶（容量 1 无突发）；上游 429 指数退避 min(60,2^n·6)+jitter；轮询走 text 桶不占视频桶 | 读码；本轮未发现新缺陷 |
| 参考图托管 | GithubPagesHost：内容寻址 sha256 命名+GET-first 幂等+PUT 重试+409 幂等核对+Pages 就绪轮询；ensure_url 探活后定点重托管 | 读码+回归 59 项含图床 |

## 4. 本轮修复（含 diff/commit/回滚）

### 4.1 已修复：workflow 时间戳时区缺陷

**证据**：`src/workflow/store.py` `_now_iso()` 原实现 `time.strftime(..., time.localtime())` 拼 `"Z"` 后缀——把 UTC+8 本地时间误标成 UTC（差 8 小时）。交叉验证：run_58a5f25aeeec 事件 ts=05:09Z，若为真 UTC 则换算本地 13:09，晚于记录该次复盘定版的 commit（12:23+0800），矛盾；按本地时间解读则自洽。timing_ledger 用真 UTC（+00:00），两源相差 8 小时，直接污染跨源时间线对账。

**修复**：改为 `datetime.now(timezone.utc)` 真 UTC，保持 "Z" 后缀与既有数据形态一致。核实无消费方解析该 ts（仅写出、排序、展示），修复无行为面影响。

**diff/commit**：分支 `phase52/efficiency`，commit `29a878653db91c88f6d568e24d536f1b5d3617fc`（1 file, +7/−1）。

**回滚点**：
- 回滚本修复：`git revert 29a87865`（基线 `ca02635a` 不受影响）
- 回滚到冻结基线：`git checkout ca02635a -- src/workflow/store.py`
- 历史数据注记：修复前落盘的工作流事件/run 时间戳为 local-as-Z，跨源对账需 −8h 换算（TIMELINE.csv 已按此换算并在 source 列标注 `tz_corrected_local_as_Z`）

### 4.2 记录未修（理由）

| 发现 | 处置 | 理由 |
|---|---|---|
| image_2k 限流口径差异：config.yaml=16（生效值），rate_limiter.py DEFAULT_RPM=4 且注释称"Phase D 实测保守值" | **不改值**，仅报告 | config 为显式来源（api_server 传入生效）；改小会拖慢图片链路、改大有 429 风险；两者分歧属历史校准文档未同步，建议下轮用真机探针定版后同步注释 |
| jobs.json 累计 11820 个历史 job（8.8MB，failed 954/cancelled 463） | **不改** | 它是 durable 执行真相（settlement 依赖），已有 purge_orphans/clear_finished 手动工具；自动清理可能破坏 task↔job 对账链，需专门设计+回归，超出"小范围改动"边界 |
| timing_ledger 混合 schema（73 条历史探针事件缺 epoch/mono） | **不改** | 历史探针脚本直写所致，观测件 fail-open 设计下无害；时间线已用 utc 字段兜底 |
| shared_library.py `_now_iso()` 无时区标记（裸本地时间） | **不改** | 仅 used_at/imported_at 展示字段，不与跨源对账；改动收益低 |

## 5. 时间线说明（B 项）

`PHASE52_TIMELINE.csv`（700 行）三源合并：
- S1 runs_index（18 行，run 级起止与终态）
- S2 两个 P51_E run 的 events.jsonl（250 行，节点/attempt/审核级）
- S3 timing_ledger 的 P50_B 视频链事件（432 行，video_ready/submitted/completed/downloaded/failed）

等待原因标注：等待人审 25 行、服务端处理中 151 行，其余为即时事件。**口径声明**：墙钟=时间戳差；S3 的 video_ready 为 handler 进入信号，数量大于提交数属恢复/重入路径正常现象，不据此计耗时。未宣称任何提速倍数（无同口径修复前后对照，本轮不建立虚假基线）。

## 6. WB-EFF 建议评估（G 项，已评估）

WorkBuddy 交付：7/20 镜完成（额度 429 中断，非能力缺陷）、全程 0 次视频返工、粗剪 70.9s、Skill 副本哈希 19/19 对账一致、逐镜 trace 与时间线齐备。其 5 条建议逐项裁定如下：

| 编号 | 建议 | 裁定 | 理由与证据 |
|---|---|---|---|
| WB-EFF-01 | 5s 段接力拼 10s；官方有 8-10s 直出档可省一半调用 | **采纳（10-12 修订，原判"不适用"）** | **修订依据（10-12 实测，PHASE52_VIDEO_RETEST_RESULTS.md）**：同输入 10s i2v 直出 2/2 复现"凭空添加元素"型场景漂移（整场景替换/前景插入），keyframe 仅钉住第 0 帧——10s 直出恰是缺陷高发区。WorkBuddy 的 5s 段+真实末帧接力是对该模型缺陷的正确规避（其 7 镜 0 返工与 5s 段强相关）。生产策略修订：空旷固定长镜头优先 5s×2 接力，动作密集镜可保留直出；另存候选执行策略版本，不动冻结基线 |
| WB-EFF-02 | 多参考融合>单参考>纯文生图；把每镜首帧参考清单写入分镜冻结数据 | **采纳为候选（试验）** | 多图融合与 我方 multi mode（reference 1-5 图）一致，方向成立。真实缺口：锁定分镜已有 `first_frame_reference` 字段但 20 镜均为 null，参考绑定靠运行时决策。做法：数据补全（预填各镜 approved look ref 清单），**另存候选数据版本+独立哈希，不污染冻结基线**；最小验证：下轮 2-3 镜对比"预绑定 vs 运行时决策"的首帧一次通过率与决策耗时 |
| WB-EFF-03 | 审查点前置到首帧作为强制门禁 | **已具备（不适用）** | 协作流程 v2（commit 95c34d3，2026-10-11 定版）已落地审核三查判据+前置卡自动放行+修复 3 次豁免闸；我方 P50_B/P51-E 流程即首帧审查先行。其"0 次视频返工"实证反向印证我方判据方向正确 |
| WB-EFF-04 | 接缝 MAE 改走 ffmpeg rawvideo+纯 Python，绕开沙箱 pip 断网 | **暂缓（备用留档）** | 本机 PIL/numpy 可用，接缝测量已在 calibration 流程内实现，无迁移收益。留档：未来在隔离容器/无 pip 环境跑探针时可复用该口径 |
| WB-EFF-05 | 全片前按"每镜 2 段+1 首帧"预估额度并分批推进；状态落档可续作 | **采纳（待实现，下轮轻量改动）** | 我方已有 QuotaLedger 每日账本+提交前 `quota.can` 预检（不足即拒、fail-fast），但**缺 run 级预估**：开工前"20 镜×10s=200s vs 账本余量"的显式比对与分批提示。其 7 镜即耗尽额度中断，实证预估必要性（我方 P51-E 亦有 488/500 逼近上限经历）。实现草图：run 启动校验中按定义的视频节点汇总预估秒数与账本余量比对，仅告警不阻断（不改并发、不改完成判定）；需配套回归，本轮不改码 |

**裁定汇总（10-12 修订后）**：采纳 3（WB-EFF-01 依据实测修订为采纳、WB-EFF-02 候选试验、WB-EFF-05 待实现）、已具备 1（03）、暂缓 1（04）。无一条触及冻结基线；候选改动均另存编号版本。

### E20 后记（额度共享核实，证据落定）

WorkBuddy 的 14 段视频+8 张图生成**未经过我方 Agnes 配额池**：`cache/quota.json` 在其生产时段（18:17–20:47）无任何写入（mtime 停留在 19:17:54=我方图片测试时刻，video_seconds 保持 488.0）。其 429 来自其平台自带生成能力的独立额度；Flova 账号（100 积分）亦经其核验与 Agnes 独立。**结论：本轮三方额度相互独立，E20 风险解除；后续若任一边改用共享账号/Key，须重新按调度方串行约束执行。**

## 7. 交付物清单（逐份）

| 文件 | 说明 |
|---|---|
| `PHASE52_FROZEN_INPUTS\PHASE52_BASELINE_MANIFEST.json` | 冻结清单（全部文件 SHA-256） |
| `PHASE52_FROZEN_INPUTS\PHASE52_INPUTS_STATUS.md` | WorkBuddy 输入状态 |
| `PHASE52_FROZEN_INPUTS\01_skill\` | Skill 逐字副本 ×3（含绑定与加载机制源码） |
| `PHASE52_FROZEN_INPUTS\02_project\` | 剧本/分镜/意图/receipts 证据/工作流定义 |
| `PHASE52_FROZEN_INPUTS\03_approved_materials\` | 4 个已批准参考图 + 22 个首帧哈希清单 |
| `PHASE52_FROZEN_INPUTS\04_baseline\` | git 基线 + 配置指纹 |
| `PHASE52_TIMELINE.csv` | 700 行可解释时间线 |
| `PHASE52_IMAGE_AND_RECOVERY_RESULTS.md` | 真实图片链路 + E01-E20 逐项结论 |
| `PHASE52_IMAGE_OUTPUT\I1_captain_identity.png`、`I2_boat_environment.png` | 真实生成图 |
| `PHASE52_IMAGE_LEDGER.jsonl` | 图片测试账本（模型/耗时/哈希/URL） |
| commit `29a87865`（分支 phase52/efficiency） | 时区修复 + 回滚说明（§4.1） |

## 8. 工程通过性自评（对照验收条件）

| 条件 | 结论 |
|---|---|
| 被证实的重复生产/推进问题已有修复证据 | **部分**：未发现新的重复生产/推进缺陷（机制完整+回归通过）；已证实的跨源计时缺陷（时区）已修复并给出回滚点 |
| 复用、重启、未知提交、晚到回执不破坏项目真相 | **通过**（238 项回归 + 真实日志取证） |
| 真实图片链路正常 | **通过**（2/2 真实生成+视觉核验；不代表视频画质） |
| 同口径计时解释优化前后差异 | **不适用（如实报告）**：本轮无同口径前后对照运行；按验收书要求不宣称提速倍数，机制改善以核验+回归为证 |
| 完整视频提速 | **本轮不作声明**（未提交新视频，符合配额约束） |
