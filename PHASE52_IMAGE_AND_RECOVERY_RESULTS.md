# PHASE52 图片与恢复测试结果（CodeBuddy）

执行日期：2026-10-11。客户端：CodeBuddy（GLM-5.3-Flash，思考开启）。
仓库基线：`feat/agent-v2-phase-d-golden-run` @ `ca02635a`；工程分支 `phase52/efficiency`（修复 commit `29a87865`）。

**本轮约束遵守**：Agnes 视频配额当日已用 488/500s（quota.json 实证）→ **未提交任何新视频**（E20 同时成立：WorkBuddy 额度独立性未核实，两边未同时生成）。图片配额 52/4000，充足。

标签约定：`真实` = 当前真实系统/真实出站请求；`回归` = 现有 pytest 回归（mock 不真调上游）；`日志取证` = 既有真实运行数据；`模拟` = 隔离注入（本轮未新增）。

## 一、真实图片链路复验（真实）

固定条件：模型 `agnes-image-2.1-flash` / 1K 档 / 16:9（1312×736）/ i2i（image_refs=base64 data URI）/ 验收=视觉模型实际看图（非只看路径，E19 对应证据）。参考图均为已批准 Look（哈希记录于 `PHASE52_IMAGE_LEDGER.jsonl`）。

| 测试 | 内容 | 参考 | 结果 | 耗时 | 产物 |
|---|---|---|---|---|---|
| I1 | 船长身份 | look_f171aea96f3e 已批准 ref（船长，sha256 记录在账本） | 提交→受理→生成→下载→落盘 **2/2 全通** | 15.76s | PHASE52_IMAGE_OUTPUT/I1_captain_identity.png |
| I2 | 船与环境 | look_96e67a3354c3 已批准 ref（渔船；本地缺失已从原始 COS URL 下载，视觉核验=无人渔船右舷 3/4 黄昏海面，与 look 元数据一致） | 同上 | 12.78s | PHASE52_IMAGE_OUTPUT/I2_boat_environment.png |

**视觉核验结论（如实，两档分开）**：

- **I1 身份连续性＝部分一致**：中年船长/深蓝油布防水外套/严肃神态/海上环境保持；但生成图多了毛线帽（参考图无帽、发型外露）、外套细节漂移（无帽兜/绳编腰带/肘部补丁）、面部非同一人。这正是 Skill v1.6.0「特写身份锚定」判据针对的真实漂移——单参考 i2i 在改变景别/动作时头部特征不稳。
- **I2 环境连续性＝主体一致**：蓝 hull/木质甲板/单桅/右舷全貌/黄昏平静海面保持；甲板细节（排气烟囱、甲板货箱）丢失。已知「参考不锁首帧 may recompose」行为（AGNES_API_FACTS §3.5）。
- **链路质量 ≠ 画质**：链路（提交/限流/受理/生成/下载）本轮真实通过；画质结论仅针对这两张图，不代表视频画质。

每图耗时波动样本有限（n=2，且分别为不同 prompt/参考），不据此宣称提速数字。

## 二、恢复与故障场景（E01–E20）逐项结论

执行环境说明：`回归` 列为本次实际执行的 pytest 子集（共 238 项通过，明细见第三节）；`日志取证` 引用真实运行数据（runs/events.jsonl、cache/jobs.json、cache/p50_timing_ledger.jsonl、quota.json）。

| 编号 | 场景 | 结论 | 证据 | 是否模拟 |
|---|---|---|---|---|
| E01 | 合格成果存在、本次无新写入 → 复用 | **通过**（回归+代码核验）。`verify_node_outputs`：require_new 下跨 attempt 真实写入累计计入（writeSource=prior_attempt 可溯）；allow_verified_reuse 走服务端核验（存在+hash+文件+审批）产出 reused | src/workflow/outputs.py L352-485；tests/test_p51_a_efficiency.py、test_p47_workflow_semantics.py 通过 | 否（mock 回归） |
| E02 | 成果过期/参考替换 → 不误复用 | **通过**（回归+代码核验）。`freeze_node_inputs` 对上游输出重读项目事实核对 contentHash/fileOk，不一致→stale；shot hash 排除下游进度字段防误 stale；video_version 另有 run 窗口（createdAt≥window_start）防文本更新污染 | outputs.py L524-574、L410-426；test_native_av_c1_basis_freshness_race.py 通过 | 否 |
| E03 | 已受理任务后中断 → 恢复收货 | **通过**（日志取证+回归）。启动 `recover_pending_videos` 先 poll 不重提交；settlement `recover_tasks` 对账 running task↔job。真实证据：timing ledger 中 P50_B 各 shot `video_completed` > `video_submitted`（如 s01_c02 5 提交/12 完成），即崩溃恢复路径对已提交任务续 poll 收货，未重复提交 | services/lifecycle.py L12-74；src/agents/settlement.py L382-401；cache/p50_timing_ledger.jsonl | 否（真实日志） |
| E04 | 提交超时受理未知 | **通过**（代码核验）。无 video_id 的 generating 显式告警留原状态「不自动处置」，重提交时标注 `previous_submit_uncertain`；不盲目重发 | lifecycle.py L43-49；routers/shots.py L1786-1789（账本记录该标记） | 否（代码路径核验） |
| E05 | 明确失败 → 新 attempt 重试 | **通过**（回归）。job attempts 计数、workflow attempt（EV_ATTEMPT_DISPATCH/RESULT）、同 run 修复延续；节 [s01_c01] 日志取证：5 次提交对应多轮 attempt | src/core/job_queue.py；工作流 events（attempt.dispatched） | 否 |
| E06 | 重复成功回执 → 幂等 | **通过**（回归）。settlement `_apply_decision` 幂等（task 非 running 跳过 §18-9）；`find_by_origin` 幂等防重复 submit | settlement.py L160-185；job_queue.py L386-396 | 否 |
| E07 | 旧 attempt 晚到 | **通过**（回归）。Phase51 C 窗口判定：video_version 仅凭 shot 成员资格需 createdAt≥window_start；versionId 精确命中不受限；receipt 按 attempt 收货留档 | outputs.py L410-426；run_36919eb5a073 实证注释（14 镜文本更新污染被防住） | 否 |
| E08 | 浏览器刷新/新会话 | **通过**（架构核验）。前端为状态投影；持久态=jobs.json+tasks/*.json+run JSON；SSE 仅通知（settlement §12「正确性不依赖内存 SSE」） | settlement.py L4-9；store.py 原子写 | 否 |
| E09 | 后端重启 | **通过**（回归）。JobQueue._load：running 非视频→queued 重推；running 视频→保留由 recover_pending_videos 续 poll 不重提交；_run_job shutdown 保留 RUNNING 语义 | job_queue.py L81-93、L281-290；test_ai_6f_shutdown.py、test_ai_6f_real_pipeline.py 通过 | 否 |
| E10 | OCC 冲突 | **通过**（回归）。DefinitionStore.save revision 校验→RevisionConflict（409 语义）；EventLog 单调 seq；run 读改写原子替换 | store.py L67-104；test_p46_workflow_engine.py 通过 | 否 |
| E11 | 输入就绪+额度允许 → 及时推进 | **通过**（日志取证）。run_58a5f25aeeec（P51_E run2）：02:30 启动 → 9 节点 9 attempt 连续推进 → 05:02 装配完成 → 05:09 人审通过，全程事件可溯（PHASE52_TIMELINE.csv S2 段） | projects/P50_B/output/workflows/runs/run_58a5f25aeeec/events.jsonl | 否（真实运行） |
| E12 | 上游/端点/人审未完 → 保留等待 | **通过**（代码+日志）。waiting_human 为显式状态（不合成 running）；W09r5 run 自 2026-10-09 处于 waiting_human 待人审（真实等待被如实保留） | models.py 状态机；runs_index.json | 否 |
| E13 | 多观察者重复查询 | **通过**（代码核验）。视频轮询由 video handler 单点执行（video worker 串行消费）；settlement 单一 poll loop（2s 间隔）读取 job 状态，不发起上游查询；重启后 reattach 不建重复观察 | job_queue.py _worker；settlement.py _loop | 否（代码路径核验） |
| E14 | 本地限流 vs 上游 429 | **通过**（代码+日志）。本地=RateLimiter 令牌桶（桶容量 1，SAFETY 0.85，分桶 text20/image_1k20/image_2k16/video1）；上游=RETRYABLE{408,429,5xx} 指数退避 `min(60,2^n*6)+jitter`，来源可区分（AgnesError.status）；轮询走 text 桶不占视频桶 | rate_limiter.py；agnes_client.py L26/L314-323/L697 | 否 |
| E15 | 参考 URL 失效/托管失败 → 定点修复 | **通过**（真实+代码）。ImageHost.ensure_url：known_url 可达（HEAD/Range-GET 探活）→复用；失效→按内容 sha256 重新上传（GET-first 幂等、PUT 重试、Pages 就绪轮询）。本轮真实案例：渔船批准参考本地缺失→从原始 COS URL 下载成功（URL 仍可达） | image_host.py L31-48、L268-334 | 部分（探活逻辑回归；下载为真实） |
| E16 | 已选视频裁切终点改变 → 下游依赖 | **部分（机制在，未新验证）**。尾帧接力依赖「实际保留区间最后一张真实解码帧」机制存在于 LOCKED_STORYBOARD rules 与 video end frame 流程（output/frames 存 234 个 sXX_cXX_video_end_vv_*.png 实证历史链路真实跑过）；本轮视频配额不足未做新裁切端点验证，如实标记 | _p50_c_package/LOCKED_STORYBOARD.json rules；output/frames/ | 既有素材取证，非新测试 |
| E17 | 相同失败反复 → 修复上限 | **通过**（回归）。review_retry_guard + executor 豁免闸（repair_limit_exhausted）；协作流程 v2 三查判据+修复 3 次豁免（commit 95c34d33 已落地） | src/agents/review_retry_guard.py；test_p48_a_repairs.py 通过 | 否 |
| E18 | Skill 未绑定/绑错/漏加载 | **通过**（回归+核验）。SkillRegistry fail-closed（未知 skill 拒绝）、mtime 缓存、单例；SkillRuntime trace 落档 output/agents/skills/；本轮冻结导出即以真实加载入口（builtin/ 目录 skill.json bindings）为准 | src/agents/skill_system/registry.py；test_skill_system.py 通过 | 否 |
| E19 | 视觉检查只给路径没传图 | **通过**（真实）。本轮 I1/I2 审查为图片实际输入（base64 传参考+生成图回读视觉核验），证据=生成图与参考图的实图比对结论（第一节）；`chat_completion_vision` 强制 image_url/base64 数组形态 | PHASE52_IMAGE_OUTPUT/；agnes_client.py L380-413 | 否（真实） |
| E20 | 疑似共享额度 | **遵守**（调度决定）。本机 Agnes 单账号单配额池（.env 单 key，指纹记录于 manifest）；WorkBuddy 平台额度独立性未核实 → 本轮两边未同时发起生成；视频 488/500 → 本地零视频提交 | cache/quota.json；PHASE52_BASELINE_MANIFEST.json generation_account_nonsensitive | — |

## 三、回归执行明细（本次实际运行，全部通过）

| 测试集 | 覆盖 | 结果 |
|---|---|---|
| test_p50_a_minrepairs + test_skill_system | 限流 env 覆盖、计时账本 fail-open、Skill 加载 | 25 passed |
| test_p46_workflow_engine + test_p47_workflow_semantics | 状态机、OCC、事件、完成校验 | 40 passed |
| test_p51_a_efficiency + test_p48_a_repairs | 跨 attempt 复用、修复上限（E01/E05/E17） | 23 passed |
| test_ai_6f_real_pipeline + test_ai_7ch_cancel_race | 结算桥、取消竞态（E03/E06/E09） | 40 passed |
| test_ai_7c_7_gates + test_ai_7c_2_replay + test_ai_7c_6_cancel + test_ai_7c_1_execution + test_native_av_c1_basis_freshness_race | 门禁/重放/取消/执行/freshness（E02/E10/E12） | 51 passed |
| test_ai_6f_real_pipeline + test_ai_6f_shot_producer + test_ai_6f_shutdown + test_image_host_github_pages | 结算/关停恢复/图床（E03/E09/E15） | 59 passed |
| **合计** | | **238 passed, 0 failed**（仅既有 FastAPI on_event DeprecationWarning，非本轮引入） |

## 四、未解决与边界（如实）

1. **E16 未做新验证**（视频配额不足），依赖机制仅有历史素材取证；后续可比新视频测试再验。
2. **I1 身份漂移未修复**：属画质/Skill 判据维度（三档裁定的 minor 级），本轮按「效率与质量分开报告」原则记录，不做画质修复。
3. **真实图片样本 n=2**：仅满足「链路正常」证据；未做固定条件多次复验（避免无目的消耗额度），耗时波动无可比结论。
4. **73 条历史 timing_ledger 事件缺 epoch/mono 字段**（first_frame_rebuild/s02c04_ff_rebuild，来自历史探针脚本直写），时间线中该部分用 utc 字段兜底；属历史数据质量问题，未回改。
5. E04/E13 为代码路径核验（本轮无真实故障注入窗口），已在表中如实标注。
