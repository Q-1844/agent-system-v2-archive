# Phase 53 A0｜核验与冻结基线（2026-10-13）

执行者：Claude Code（测试执行与取证者）。本文件记录开工时真实核验结果；标 `未取得` 的项说明原因。

## 1. 代码与环境

| 项 | 值 | 证据 |
| --- | --- | --- |
| 生产仓库 HEAD | `d734144aaf8c8cad622cda9adcf935120bf83562`（animation-storyboard） | git rev-parse |
| 用户改动（保留，不动） | `_p51_va_multiview_video.py`（M）、`components.d.ts`（M） | git diff --stat |
| 主仓库指针 | `8c5c33d` chore: submodule pointer - PHASE51_E_REPORT §11 | git log |
| Python | `D:/Delta Force/python.exe`（项目运行时） | 实测 `-c print` |
| 后端 | FastAPI :8000，2026-10-13 11:23 启动成功；Workflow 恢复扫描 4 个历史活跃 run（未触碰） | backend.log |
| AGENTS.md | **未取得**——仓库不存在该文件；以 `CLAUDE.md`（阶段5 旧指引）+ 实际注册代码为准 | ls |
| 测试目录 | `测试4/PHASE53_TEST/`（evidence/scripts/logs）；测试脚本与生产仓库分离 | 本文件 |

## 2. Agent 注册（registry.py 实核）

`src/agents/registry.py` 注册 **1+9** 个 Agent（spec 顺序）：producer + script_writer / character_designer / scene_designer / director / production_planner / shot_producer / continuity_reviewer / editor / assembly。

**本轮「六员体系」= Producer（总协调）+ script_writer（编剧）+ character_designer（Resource Agent：角色/造型/道具/生产资源）+ scene_designer（场景）+ director（导演：分镜/首帧/视频/审核）+ assembly（成片装配）。** production_planner/shot_producer/continuity_reviewer 为 capability-dispatch 遗留通道（AI-6F 时代），现行生产链（Phase 45-51 实测）经原生 tool-loop 的 director 承担制作与审查，不在六员协作主链。

- Producer 硬边界（producer.py:123 物理保证）：工具面**只有只读工具 + 5 个 delegate**（script_writer/character_designer/director/scene_designer/assembly.delegate），无任何写/生成工具。owner/锁：story→script_writer、character+resources→character_designer、scene_production→scene_designer、storyboard(shot)→director、sequence→assembly（routers/agents.py:294-356 域锁实核）。
- 委派守卫 `wf_delegate_guard`：目标不在 allowedDelegates → 服务端直接回执失败。

## 3. 正式 Skill

| Skill | 版本 | 哈希（SHA256） | 绑定 |
| --- | --- | --- | --- |
| `full-story-relay-calibration` | 1.6.0 | SKILL.md 见 evidence/skill_hashes.json | director=primary_executor(100) / producer=coordinator(80) / script_writer=contributor(60) / character_designer+scene_designer=conditional(40) |
| `keyframes-bridge-repair` | 见 evidence/skill_hashes.json | — | — |

加载机制：L1 catalog 常驻 → `skill.load`（L2 正文+role resource）→ `skill.read_resource`（L3）；trace 落 `output/agents/skills/trace.jsonl`。**权限边界（runtime.py 硬约束）**：skill 只教方法不授新权限；`required_capabilities` 与 agent 真实工具面对账，缺失工具记 `capability_check.missing`，必须 fail 或 delegate。**Phase 53 B 批预判：Producer 加载 director role 的 skill 不会获得 shot 生成工具——是否「直接执行」取决于 B2 探针对现有授权机制的真实核验。**

## 4. 模型 / Thinking（config.yaml 实核）

- text：`agnes-3.0-flash`（全部 Agent 默认 profile）；Vision 审查：`agnes-2.5-flash`（director_vision_review.py:38 显式）
- image：`agnes-image-2.1-flash`（1K 档 16:9→1312x736）；video：`agnes-video-2.5-flash`（唯一，seconds 4-12s，720P，mode text/keyframe/reference）
- Thinking：turn 级参数（routers/agents.py:143 SendMessageReq.thinking）；agnes 适配=`chat_template_kwargs.enable_thinking`（agnes_client.py:239-248；Phase 48 出站抓包实证 reasoning_content 返回）。Phase 39 用户指令：Producer turn 测试默认开 thinking——本轮 A/B 一致 true。
- 限流 RPM：video=1（串行）、image_1k=20、image_2k=16、text=20。
- ImageHost：github_pages（Q-1844/agnes-frame-host，PAT in .env）。

## 5. 配额（Token Plan 口径）

| 项 | 每日上限 | 当前账本 |
| --- | --- | --- |
| 视频时长 | 500 s/天 | 2026-10-12 用 369s；10-13 按日重置，开工时 0 |
| 生图 | 4000 张/天 | 0 |
| 文本 | 7200 次/天（滚动窗口理论值） | 0 |

**注**：QuotaLedger 是本地保守估计非服务端真值（项目记忆实证）；独立进程须从 config.yaml 以 500 初始化单例。每天开工先读账本，不套用历史日额度。

## 6. 审核 / gate / 修复上限 / 选版（协作流程 v2，用户 2026-10-11 定版，commit 95c34d3）

1. **审核三查判据**：只查①人物身份出错②环境跨镜不一致③大的其它不合理；资产样式不归审核管；分镜文本=拍摄蓝图非逐帧验收。
2. **前置 4 卡 autoApprove**：human_review 节点 config.autoApprove=true → 创建即自动批准（事件留痕）。
3. **修复 3 次豁免闸**：同节点 reject≥3 → continue 追加「修复豁免」卡自动 approve，不再开修复 attempt；最终取舍留用户。
4. **尾帧接续链策略**（Skill v1.6.0 §9）：镜内 10s→20s 接力容错 + 镜间接续。
5. **选版/终审**：系统产出候选与提案；`select final_render` 永远由用户显式执行（producer.py:118 硬边界明文）。

## 7. 时长政策冻结（B3 共同输入前置项）

**现行正式策略 = Skill v1.6.0 正文「时长配方」**：静态/反应镜 5s；动态镜 8s；高运动/复杂交互 10s（实证两轮 20 attempts 零截断；Phase 42 定版、随 v1.6.0 冻结体生效）。**用户认可证据链**：Phase 42 封板验收（09-30 定版配方）→ Phase 51-E §11（10-11 用户复盘定版，协作流程 v2 五项含尾帧接续链，commit 95c34d3 落地）→ 本轮开工时 Skill 正文未变。→ **早期「至少八秒」政策已被该配方覆盖**（视频契约本身允许 4-12s）。A/B 逐镜时长向量按各自分镜的动作量估时，规则同源同文；禁止为提速私下改秒数。

## 8. 日志与取证能力

- JobQueue：`cache/jobs.json`（11820 条历史，kind/status/project/shot_id/task_id）——task ID 可恢复。
- Workflow run：`projects/<p>/output/workflows/`（definition/run/events.jsonl）；API `GET /api/project/{p}/workflow/runs/{run_id}/events`。
- Skill trace：`output/agents/skills/trace.jsonl`（append-only）。
- Agent trace/receipts：sessions + delegate 回执（Task Result）。
- 限制：客户端显示累计时间≠单镜请求耗时；Provider 完成时刻常为轮询观察区间（上界）——记录为 `observed_at` + `derived=true`。

## 9. 冻结清单（本轮全部测试共用，结束前不得变更）

- [x] 代码 HEAD `d734144` + 用户 diff 2 文件（不动、结束核对无新增）
- [x] 六员注册与 owner/锁边界
- [x] Skill v1.6.0 正文哈希
- [x] 模型 ID / Thinking / RPM / ImageHost
- [x] 审核三查判据 + autoApprove + 3 次豁免闸 + 用户终审
- [x] 时长配方（5/8/10s 按动作量）
- [x] 配额口径（video 500s/day Token Plan）
