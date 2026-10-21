# SOURCE_MAP — 包内文件 ↔ 原仓库映射

原仓库：`animation-storyboard/`（git 子仓），取证时分支 `feat/phase55-collab-parallel`，HEAD `82e305019f37a089f6499504954b5abfc4a4cb9b`（2026-10-18 08:51 +0800）。
工作区状态：3 个已跟踪文件有未提交改动——`_p51_va_multiview_video.py`（P50/51 时代遗留脚本，与本轮无关）、`components.d.ts`（自动生成）、`routers/shots.py`（**本轮合法改动未提交**：FirstFrameRequest 增 scene_reference_mode/human_reference_mode/population_constraint——diff 副本在 00_snapshot/uncommitted_patch_routers_shots.py.diff；当前运行后端已载入该改动）。02_source 中 `routers/shots.py` 为**工作区版本**（含该补丁），非 HEAD 版本。

| 主题 | 包内路径（02_source/ 下） | 符号/关注点 | 全文/节选 |
| --- | --- | --- | --- |
| 角色注册/运行时 | src/agents/registry.py; src/agents/runtime.py | `SPECIALISTS`、`AgentRuntime.unified_turn`、`AgentError`(:42) | 全文 |
| Producer 主执行 | src/agents/producer.py | `producer_turn`(:1335 起；lease acquire/AgentError 修复点 :1340-1362)、tool-loop、`_audit_wrap` | 全文 |
| 协作模式注册表 | src/agents/collab_modes.py | `COLLAB_MODES`(combo v2 定义)、`DEFAULT_EXPERIMENTAL_MODE_ID`、`start_collab_run`、`_apply_run_concurrency`、`_producer_turn_with_relays`、`resume_collab_run`、`_final_review_and_repair`(终审→修复→复审闭环)、`_APPROVED_PACKAGE_STEPS`(v2.1 批量提交指令) | 全文 |
| 主控租约/交接 | src/agents/master_lease.py; src/agents/handoff.py | `acquire/verify/transfer/diagnose/recover`（P56 损坏 fail-closed+恢复路径）；`relay_producer_session` | 全文 |
| 授权 | src/agents/grant.py | 五族工具面、TTL、审计 | 全文 |
| Skill 系统 | src/agents/skill_system/*（registry/loader）；_skill_catalog.txt | 目录常驻+按需 load；版本目录清单（正文未打包） | 代码全文+目录清单 |
| 工作流（六员链） | src/workflow/{plan,executor,models,store,outputs,templates}.py | `workflow_snapshot_v1`、W09 模板（重建型节点目标——C 批消费缺口证据）、repairRequireNew | 全文 |
| 提交入口 | routers/agents.py; routers/shots.py; routers/workflow.py; routers/jobs.py | collab-runs 端点、`_handler_video`（恢复分支/UNKNOWN 待核验/收货幂等 :1690-1930）、契约闸接线(:2010 附近)、`FirstFrameRequest`（含未提交补丁） | 全文 |
| 统一契约 | src/generation/video_contract.py | `REFERENCE_POLICIES`(v2=baseline_equiv_chain)、`scene_reference_consumed` 五态、`continuity_semantics`、`validate_video_submission`、`VIDEO_JOB_PARAM_KEYS` | 全文 |
| 适配/客户端 | src/generation/video_adapter.py; src/generation/agnes_adapter.py; src/generation/image_adapter.py; src/generation/native_av_pack.py; src/api/agnes_client.py | 槽位编译/哨兵 prev_tail_look_scene/`resolve_scene_reference_mode`/`DEFAULT_SCENE_REFERENCE_MODE="auto"`、429 Retry-After(`_parse_retry_after`) | 全文 |
| 队列/配额/限流 | src/core/job_queue.py; src/core/quota.py; src/core/rate_limiter.py; services/lifecycle.py | `resolve_video_inflight`、`reconfigure_video_workers`（结算后热重配）、watchdog 延长窗、`recover_pending_videos` | 全文 |
| 项目写入 | src/core/store.py; src/core/write_lock.py; src/core/models.py | `update_shot`（整文件原子写、无 CAS）、Shot/VideoVersion/OCC 字段、`opening_cut_reason` | 全文 |
| 会话/恢复 | src/agents/session_governance.py; src/agents/turn_registry.py; src/agents/context_budget.py | reground、turn 互斥、usage 账本 | 全文 |
| 审核/修复 | src/agents/review_pipeline.py; src/agents/shot_review.py; src/storyboard/continuity_service.py | `VIDEO_HARD_DIMS/VIDEO_MINOR_DIMS/STATE_FRAME_POSITIONS`（video_review_v2）、`SHOT_REVIEW_HARD_DIMS`(v1 静帧硬维——对照)、`_classify_shot_frames`、固定三帧位抽帧 | 全文 |
| 绑定 | src/shot_binding/service.py; src/shot_binding/store.py | readiness/binding 文档 | 全文 |
| 前端面板 | src/components/agent/CollabRunPanel.vue; src/api/index.ts | 模式选择/启动/快照哈希显示 | 全文 |
| 结构服务 | src/storyboard/structure_service.py | `update_shot_fields`（opening_source/opening_cut_reason 白名单+值校验） | 全文 |
| 入口/装配 | api_server.py; deps.py; src/agents/assembly.py; src/agents/director.py; src/agents/script_writer.py; src/agents/character_designer.py | 启动单例、装配/选版、shot 工具面（SHOT_UPDATABLE_FIELDS 含 opening_source/opening_cut_reason）、SW 建段 | 全文 |
| 配置 | 03_config_redacted/config.redacted.yaml + runtime_limits_snapshot.json | 并发/额度/限流生效段、运行时真实读数 | 脱敏全文 |

## 未包含与理由

- `.git/`、node_modules、虚拟环境、cache 全集（jobs.json 以规范化导出代替）、`projects/` 正册全集（按链索引引用）、媒体/帧图（核心包不含；按 chain JSON 内索引定位）。
- 会话转录（sessions/*.json）：含完整对话内容，非架构研究所需，剔除；其摘要性事实已由 run 记录与报告覆盖。
- Skill 正文：仅目录清单+版本（方法论内容如需，按 catalog 定位）。
- 其余测试文件（非 p55/p56 直系）：代表性子集已含；全量测试清单可用 `tests/` 目录在原仓库查。
- 行号：全部为全文复制（无节选截断），行号=原仓库行号（唯一例外 routers/shots.py 为工作区版本，比 HEAD 多 21 行补丁——见 00_snapshot diff 对齐）。
