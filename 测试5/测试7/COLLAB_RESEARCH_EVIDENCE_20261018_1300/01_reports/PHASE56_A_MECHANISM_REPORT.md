# PHASE56 A 机制收口与实验默认——实施报告

日期：2026-10-18。任务书：`测试5/测试6/PHASE56_01_MECHANISM_AND_DEFAULT.md`（00 开工提示词授权工程收口）。
分支：`feat/phase55-collab-parallel`（延续 Phase55；本轮改动见提交索引）。

## 0. 执行摘要

A 批围绕 Phase55 已报告的缺口做最小修复（不重建存储/框架），7 项机制收口全部落地，定向测试 20/20 通过；P55 定向 42 项中 1 项按语义变更显式更新（fail-open→fail-closed）。后端（8000）在收口后重启载入新代码后进入 B 批。

上轮（Phase55）看片不通过定性「bind 已强制/接续链未强制」的直接修复=**A2 reference_policy v2（baseline_equiv_chain）**：`context_only` 不再冒充已消费、同场景相邻镜 independent 须显式声明切镜依据、豁免须显式登记。

## 1. 先核验结论（01 文件要求的核验依据，最小版）

| 项 | 真实路径核验 | 判定 → 处置 |
| --- | --- | --- |
| 额度 | `/api/system/limits`：2026-10-18 账本已滚动归零（video 0/500s、images 0/4000、text 0/7200）；本地账本口径，真值以 B 批首次真实提交被接受为准 | ✓ 已核 |
| 后端 vs 代码 | 后端进程 10-17 20:07 启动 < c3bba9f（21:16 主控租约修复）——运行中后端缺最新代码 | A 收口后重启 |
| A2 缺口实锤 | `video_contract.py:145` `srm in ("full","context_only")`→via_first_frame（context_only 冒充消费）；策略枚举无接续链 | 本轮修复 |
| A3 缺口实锤 | `master_lease._load` 损坏→None→verify 放行（fail-open）；`collab_modes.py` 接力上限后仍标 completed；UNKNOWN 提交=标注后仍自动重发 | 本轮修复 |
| A3 已满足项 | watchdog 延长用尽→FAILED→retry 走 `shots.py:1698` 续轮询分支（不新提交）；收货幂等（同 video_id 单版本）| 补定向测试确认 |
| A4 缺口实锤 | run 的 `media_inflight` 只记在快照、未接线到队列；worker 数仅 `start()` 时解析（env > config） | 本轮修复（单一解析+结算后重配） |
| A4 已满足项 | 限流（rpm.video 桶）与在途（worker 数）两维度分开；`shot.generate_videos` 批量先入队后统一等待（不逐镜等确认） | 记录在案 |
| A1 | 五预设注册表+run 快照+快照哈希已在位（P55）；combo ⑤ 缺修复复审装配闭环与默认机制 | 本轮补齐 |
| D1 零件 | 终审 `review_pipeline.run_independent_review`、repairRequireNew、assembly 均在位；闭环编排缺失 | 本轮补齐（combo v2 执行器） |

## 2. 改动清单

| # | 文件 | 内容 |
| --- | --- | --- |
| A2-1 | `src/generation/video_contract.py` | **reference_policy v2（baseline_equiv_chain）**：①策略枚举+`policy_requires_binding()`（基线等价家族都要求 BOUND）；②`scene_reference_consumed` 五态——`context_only`→`exempted_context_only`（不再冒充已消费），full→via_first_frame，absent/unknown 如实；③豁免清单（`set_project_reference_policy(exemptions=)` + `read_policy_exemptions()`）；④接续语义三分 `continuity_semantics()`（same_action_continuation/declared_cut/undeclared_independent；开场镜 independent=自动 scene_change 依据）；⑤`find_prev_scene_shot()` 同场景前驱（播放顺序=canonical 顺序，不造第二份排序）；⑥`validate_video_submission` v2 检查：`scene_reference_not_consumed`（豁免登记可放行）+`opening_cut_undeclared`；⑦manifest `upstream.continuity` 落档；⑧VIDEO_JOB_PARAM_KEYS 增 `confirm_uncertain_resubmit`/`repair_of_review`/`repair_attempt` |
| A2-2 | `src/core/models.py` | Shot 增 `opening_cut_reason: Optional[str]`（additive；intentional cut 显式声明落点） |
| A2-3 | `src/storyboard/structure_service.py` | 白名单增 `opening_cut_reason`（值校验：非法值=StructureError fail-closed，不静默忽略）——producer `shot.update` 的声明通道 |
| A2-4 | `routers/shots.py` | ①REST `opening-source` 端点增 `cut_reason`（校验+落库）；②`activate_planned_shot` 落 Plan 的 `cut_reason`（非法→activate 即报错）；③REST 视频提交：活动策略=v2 时同受契约约束（无策略文件/旧策略维持 REST legacy 行为） |
| A2-5 | `src/ai/production_planner.py` | PlannedShot 增 `cut_reason`（Plan→activate→shot 链路） |
| A2-6 | 三入口接线 | `director_visual.py`（require_binding 改 policy 家族判定+复用 validate 内 scene_ref）、`shot_producer_capability.py`（同）、REST（见 A2-4③） |
| A3-1 | `src/agents/master_lease.py` | **损坏租约 fail-closed**：`_load` 损坏→损坏标记（≠无租约）；`verify`→verified=False 拒写；`acquire`→拒绝接管（权限未核明不双主）；`transfer`→拒绝；新增 `diagnose()`（只读恢复读/查询独立路径）+`recover()`（显式重建，仅损坏态可走，审计标记 rebuilt_from=corrupt）；`handoff.py` 租约读数改 diagnose（损坏如实落交接包） |
| A3-2 | `src/agents/collab_modes.py` | **接力上限→待接力**：relay 循环提取为 `_producer_turn_with_relays()`（start/resume 共用）；达上限仍 handoff→`status="awaiting_relay"`+`relay_pending`（不再仅加字段后标 completed）；新增 `resume_collab_run()`（同一逻辑 run：授权续接[活跃 grant 检查/过期按原快照重建]→producer_last 会话 relay 新会话→继续 turn+循环；非 awaiting_relay 拒绝） |
| A3-3 | `routers/shots.py` | **UNKNOWN 提交暂停**：generating 无 video_id 且无显式确认→handler 拒绝新提交（待核验错误，注明 previous_submit_uncertain 不是自动重发许可）；显式 `confirm_uncertain_resubmit=true`（operator 对账后人工通道）放行+仍标注 |
| A4-1 | `src/core/job_queue.py` | ①`resolve_video_inflight()` 单一解析（env AGNES_VIDEO_INFLIGHT > config concurrency.video_inflight > 默认 1；非法值跳层不谎报来源；返回覆盖来源）；②`reconfigure_video_workers(target)` 结算后热重配（幂等/在途拒绝[wait_settle=False]/等结算后应用[上限 2h]；缩容 cancel 空闲 worker，在途任务由独立 inner task 承载不受影响）；③`start()` 走统一解析并记录 `video_inflight_source`；worker 任务命名 |
| A4-2 | `src/api/agnes_client.py` | 429 解析 `Retry-After`（服务端窗口优先，有界 ≤120s；无头/不可解析回落既有指数退避）——不因并发调大制造重试风暴 |
| A4-3 | `src/agents/collab_modes.py` | `_apply_run_concurrency()`：run 的 `media_inflight`（params 显式 > 模式默认）→ `reconfigure_video_workers` → `concurrency_effect` 落 run（requested/applied/workers/source——**不把快照数字当作已生效**） |
| A1-1 | `src/agents/collab_modes.py` | **combo_recommended v2（mode_version 2.0.0，实验默认）**：reference_policy=baseline_equiv_chain+repair_policy（每镜上限 3/actor=mode_run_executor）+experimental 标记；`DEFAULT_EXPERIMENTAL_MODE_ID`+`start_collab_run(mode_id=None)` 用默认（旧预设显式回退路径不变）；run 增 `authorization`（scope/machine_review/bounded_repair/granted_by/**user_acceptance=pending_user_review**）；validate_start 接受 v2 策略；MODE_REGISTRY_VERSION=p56_a_modes_v2 |
| A1-2 | `src/agents/collab_modes.py` | **终审→局部修复→复审闭环** `_final_review_and_repair()`：独立终审→硬错镜确定性重生成（JobQueue 直提交，非 LLM 决策；actor/授权来源落账；额度检查，不足如实中止）→同政策复审该镜→still_hard 如实保留（达上限/额度不足不冒充通过）；producer 目标模板增 v2 声明指令 |
| A1-3 | `routers/agents.py` | CollabRunStartReq.mode_id 可选（缺省=实验默认，响应带 used_default_mode）；新增 `POST /collab-runs/{id}/resume` |

前端：CollabRunPanel 已有快照哈希折叠显示（P55 E 批），A1「正常入口可查看」满足；缺省模式入口面板侧后补（B/C 批以 REST 启动为主）。

## 3. 授权与边界

- 机器按本轮用户授权处理例行审核/有界修复：run.authorization 落 actor 与授权来源；独立审核独立性标注沿用 P55（fresh 无状态 vision 调用≠完全独立盲审）。
- 「用户接受」恒 `pending_user_review`——机器不填写；最终看片由用户完成。
- scoped grant / repairRequireNew / 审核卡指纹 / refresh 语义全部保留；未移除任何守卫。
- 就绪推进：`shot.generate_videos` 批量先入队后统一等待（现状已满足「不等逐镜确认」）；**依赖驱动自动派发（收货后自动提交下游）不在 A 批造第二套依赖队列**——P3（D 批）演练真实接力时验证，避免复制状态。

## 4. 定向测试与回归

### 4.1 新增定向测试：`tests/test_p56_a_mechanism.py` 20 项全过

| 域 | 项 | 覆盖 |
| --- | --- | --- |
| A2 | 8 | v2 策略解析/policy_requires_binding；context_only→exempted_context_only（full→via_first_frame）；接续三分；validate 拒绝未声明+未消费→声明/豁免放行；v1 旧策略行为不变（回归保护）；manifest continuity 落档；同场景前驱作用域 |
| A3 | 5 | 损坏租约 fail-closed 全路径（verify/acquire/transfer 拒写+diagnose+recover 重建+健康租约防绕过）；健康租约 P55 语义保持；relay 上限→awaiting_relay（落盘态非 completed）；resume 拒绝非待接力；resume 续跑同 run 完成落账；**watchdog 用尽→retry 续轮询原任务零新提交**（真实 handler 链路） |
| A4 | 2 | 单一解析优先序（env>config>默认+非法跳层）；结算后重配（未启动拒绝/幂等/扩容生效/在途拒绝/结算后应用）；run 启动 concurrency_effect 落档（无队列如实 applied=False） |
| A1 | 4 | combo v2 注册表；缺省启动+authorization；REST 缺省+resume 端点；UNKNOWN 提交暂停代码在位+契约键登记 |

### 4.2 既有测试适配（语义变更显式化，1 处）

- `tests/test_p55_handoff_review.py::test_lease_corrupt_file_fail_open` → **`test_lease_corrupt_file_fail_closed`**：P55 断言 fail-open 放行；Phase56 A3 定版 fail-closed（详测在 p56 文件）。
- `tests/test_ai_6f_real_pipeline.py::test_C42_..._previous_submit_uncertain` → 重写为新语义两段：①自动路径（无确认）拒绝新提交（待核验）；②显式确认放行+标注落库。

### 4.3 P55 定向回归

`test_p55_collab_modes.py` + `test_p55_recovery.py` + `test_p55_handoff_review.py` + `test_p55_video_contract.py`：42 项全过（41 原样 + 1 语义更新）。

### 4.4 全量回归（补上轮未回填结果）

命令 `python -m pytest tests/ -q`（完整日志 `_p56_a_full_regression.log`，1176s）。结果：**83 failed + 2507 passed + 207 errors**。按失败集合与 P55 基线日志对比（非只比数量）：

- **新增候选 4 项**（2 FAILED + 2 ERROR，全部 autopilot E2E）：`test_case1_e2e_mixed_project`、`test_case2_reuse_fresh_director_draft`、`test_e2e_case1_three_independent`、`test_start_locked_without_final_400`——**逐个单独重跑全部 PASS**（全量并发执行时的资源竞争时序 flake，AI-5A 时代已归档的 flake 类），非本轮引入。
- **翻通过 34 项**（P55 失败→本次通过）：native_av b1/c1/6f/shot_request 等预存环境 flake 族（P55 已归档为预存，两轮间环境翻转）。
- 失败/错误总数与 P55（82f+205e 摘要口径）同量级；集合级零新回归。

回归执行代码态=ec64827；其后 6dcd34a（approved_package 变体+测试，增量改动）由定向 63 项覆盖（P55 定向 42+P56 定向 21 全过）。

## 5. 遗留与边界（如实）

- 「同一逻辑请求又生成了不同 Provider ID」的去重：Agnes 无幂等键/查询端点（历史实证），A3 的 UNKNOWN 暂停+待核验已把「逻辑重复」入口收紧到显式确认通道；跨 ID 逻辑去重留待 P3 恢复演练实证后再定（如有必要新版本批次）。
- `ProjectStore.update_shot` 无 CAS（P55 A 报告 §1.3 已记录）：并发纪律仍靠 per-project asyncio.Lock + 收货幂等 + basis 复核；B 批并发主试验若现写冲突再评估加锁面（任务书允许）。
- 前端面板缺省模式入口（mode_id 省略的按钮）后补；本轮 REST 启动与面板显式选择均可用。

## 6. 吞吐与额度利用（本阶段）

- A 批全部为无媒体工程验证：视频 0s / 图片 0 / 文本调用仅本地 pytest 桩，未消耗额度。
- 今日（10-18）额度快照：video 0/500s、images 0/4000、text 0/7200（本地账本滚动后归零；服务端真值以 B 批首次真实提交被接受为准）。
- 全量回归墙钟 1176s（本地 CPU，非额度）。

## 7. 提交索引与冻结

- 子仓 `feat/phase55-collab-parallel`：**ec64827**（A 批机制收口，16 文件 +1427/-111）→ **6dcd34a**（approved_package 变体，B 批使能）。
- A 批冻结范围：本报告 §2 全部代码+测试、combo v2 注册表（p56_a_modes_v2）、reference_policy v2 语义、租约/接力/UNKNOWN 语义、并发解析与重配、修复闭环、模型（不换）、审核/修复政策（REPAIR_LIMIT=3、硬维一票否决、固定三帧位）、账户限流设置（config 现状）。
- A 后只读取证不改规则；新修复需新版本批次。运行面：后端重启载入冻结代码后进入 B 批。
