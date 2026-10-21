# COLLAB_NEXT_STAGE A 批：R1.1 回装与无配额对接报告

日期：2026-10-18（本机 Asia/Shanghai；交接包 LA 时区同为 10-18，符合"明日=10-19"约定）。
执行：Claude Code（本机）。依据：交接包 `COLLAB_NEXT_STAGE` 00/02 文档 + R1.1 补丁内 00/02/03 文档。

---

## 一、批次与代码

### 基线与补丁
- 源码根：`C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard`，分支 `feat/phase55-collab-parallel`，提交 `82e3050` + 工作区未提交修改（FirstFrame REST 等 3 个 tracked 修改）。
- 补丁：`COLLAB_FIX_R1_1_20261018.zip`，SHA256 `d1edd956…6f65d`，交接包清单 11/11 文件哈希全部核对通过。
- 应用前核对：22 个目标文件中 19 个既有文件 before 哈希**全对齐**、3 个新增文件（file_lock.py / video_commit.py / test_collab_safety_revision.py）、0 冲突。
- 回滚口径：正式目录备份 `.collab_patch_backups\20261018T124333Z_c2c35c9b`（22 文件原始字节）。

### 隔离工作区（D:\isolated\）
| 目录 | 用途 | 状态 |
|---|---|---|
| `animation-storyboard` | A1/A2/A3 主副本（含 node_modules 2.06G） | R1.1 已应用 + **本机修复候选**（见 §四.1） |
| `animation-storyboard_a4` | A4 全量/恢复三例（无运行残留） | 纯 R1.1，无本地改动 |
| `animation-storyboard_base` | 归因用基线副本 | 已回滚至 pre-patch 字节（22/22 验证） |
| `COLLAB_FIX_R1_1_20261018` | 补丁解包（项目外） | GBK 文件名修正解压 |

排除项：`.env`、`projects/`、`projects_archive_20261007/`(5.1G)、`.git`(2.7G)、`logs/`、`output/`、`cache/`、`agents_data/`、`shared_library/`、各历史媒体/审查目录。副本内无真实凭据、无真实项目数据。

### 环境
- Python 3.13.0（`D:\Delta Force\python.exe`，项目 start.bat 指定解释器）；pytest 9.1.1。
- **本机环境变更**：安装 `pytest-timeout==2.4.0`（TEST_ENVIRONMENT.json 记载的交付验证版本，仅测试插件）。此前本机无该插件。
- Node v24.5.0 / npm 11.8.0。交付环境为 Linux/Py3.12.14——所有差异按下文逐项归类，不算代码回归。

---

## 二、行为与验证

### A01 安装器行为（全部实证）
1. dry_run → `dry_run_ok`（22 pending）✓
2. `--apply` → applied 22 文件，备份落盘 ✓
3. 重复 dry_run → `already_applied` 22 项，无重复写 ✓
4. `--rollback` → rolled_back 22 项；逐文件 SHA256 比对 **22/22 字节精确恢复**（含新增文件删除）✓
5. 再 `--apply` → 再次 applied ✓
6. 跨项目根回滚被拒绝（backup belongs to another project root）——安全设计顺带实证 ✓

### A02 关键回归切片（122 项）
- 首轮（无 timeout 插件）：**122 passed in 33.69s**（安全测试参数展开后 43 项含在内）。
- 环境差异：交付命令带 `--timeout=45`，本机当时无 pytest-timeout；补装 2.4.0 后以 `--timeout=45` 复跑：121 passed + 1 failed（`test_lease_cross_process_unique_holder`，见 §四.2 定性）。
- 切片文件：test_collab_safety_revision / test_p55_recovery / test_p56_a_mechanism / test_p39e_trace_hints / test_ai_6f_real_pipeline / test_ai_6f_shutdown。
- 证据：`D:\isolated\evidence\local\a2_slice*.events.jsonl` + `.xml`。

### A03 接口对接
**只读冒烟（包内工具）**：Windows 派生版（唯一差异=守卫放行 loopback——原版一刀切 connect 会拦掉 Windows asyncio ProactorEventLoop 自建 self-pipe，交付 Linux 原生 socketpair 不触发）。
- 结果：**7/7 checks passed，network_attempts=0，provider_calls=0**（与交付证据一致，含 combo_recommended v2.1.0 契约断言）。
- 证据：`D:\isolated\evidence\readonly_smoke_local.json`。

**集成驱动（`D:\isolated\evidence\a3_integration_driver.py`）**：真实路由（无生产 lifespan）+ 脚本化假 Producer（含 relay 交接、阻塞 turn）+ 假媒体生成器（不触网，独立版本文件落盘）。**最终 34/34 flows passed，network_attempts=0**：
- F1 模式列表/健康/jobs/grant：combo v2.1.0 可用性如实（假 rt 下 available=True）✓
- F2 默认模式启动→completed_with_issues（镜头无已接纳视频→独立终审如实记问题=机器验收 needs_attention，正是 A3 文档要求验证的状态显示）✓；步骤账本 preflight/grant/producer_turn/independent_final_review ✓；grants.json + reference_policy.json 落盘 ✓
- F3 relay 上限→awaiting_relay（relay_count=3）→REST resume{"thinking":false}→completed（resumed=1，producer_turn_resume_N 步骤）→终态再 resume 400 ✓
- F4 REST cancel{"reason":"offline test"}→cancelled 且原因落 run（期间发现并修复取消复活缺口，见 §四.1）✓
- F5 假媒体 job：提交→done→独立版本挂接+文件存在；jobs REST/SSE 快照+实时 job 事件+跨项目过滤 ✓
- F6 项目事件 SSE：snapshot/实时推送/跨项目过滤/重连 snapshot ✓
- F7 刷新持久化：3 个 run 从盘重查状态一致；missing run 404 ✓

### 前端
- `npx vite build`：**✓ built in 35.62s**（全量 bundle，含 R1.1 修改的 CollabRunPanel.vue）。
- `npm run typecheck`：**被既有 TS2688 阻塞**（tsconfig 引用 node 类型，`@types/node` 不在 node_modules 也不在锁文件依赖中——原仓同状态，非本批引入；按文档不改脚本绕过）。诊断模式（临时 config 放行 node 类型入口，用后即删/仅存副本）：错误 17 项原仓 vs 18 项副本，**17 项共有错误逐条一致**（store/index.ts 4 项=CLAUDE.md 记载既有；其余 ShotCard/Workbench/resources/scene-system 等历史项），**R1.1 触及文件 0 类型错误**。副本多出的 1 项 vite.config.ts TS2307 同属缺 node 类型既有类问题（该文件哈希两边一致）。

### A4 恢复差异与全量对照
**恢复三例（干净副本，--timeout=60）**：**3 passed in 36.14s**。真实耗时：case4 13.34s / **case6 10.12s** / case7 7.59s。case6 贴近交付全量 10s 上限——本机实测解释了交付受限全量中它的超时：环境速度敏感，非代码回归。

**全量（--timeout=60，Windows 只能用 thread 方法——任何用例超时即杀全进程，故无法复刻交付 10s 口径）**：
- 本机 R1.1：**2561 passed / 81 failed / 205 setup errors**（2847 节点，13:31）。
- 交付 R1.1 记录：2559 / 83 / 205（2847 节点）。
- **nodeid 级对照（2026-10-18 修正：以 `review_r11_final.events.jsonl` = R1.1 最终记录为准，2847 节点）**：
  - **节点集合完全一致：2847 = 2847，0 仅本机、0 仅交付**。
  - 状态差异共 4 项：
    1. `test_ai_7ch_cancel_race.py::test_case1_stale_object_resurrection`：本机 failed / R1.1 记录 passed。定性：**Windows 时序敏感**（后台 postcommit 任务 0.66s 未完成即断言；单独复跑 3/3 过，耗时 1.19s/**28.2s**/2.08s）。
    2. `test_full_project_autopilot::case1_e2e_mixed_project`：本机 passed / 记录 failed。
    3. `test_full_project_autopilot::case5_planner_failed_resume_continues`：本机 passed / 记录 failed。
    4. `test_project_autopilot::case6_run_consistency`：本机 passed（60s 口径，实测 10.12s）/ 记录 failed（10s 超时口径）——与恢复三例干净复查结论互相印证。
  - 205 setup errors 节点集合与记录一致。
- ⚠️ 更正记录：本报告初版曾对照 `full_final.events.jsonl`（实为 R1 时代记录，2835 节点），得出"缺 12 项"的错误表述——系**对照文件选错**，非证据包缺口。以本节 review_r11_final 对照为准。

### 网络与额度
- 全程未调用真实视频/图片/文本/视觉/TTS/图床服务。证据：run_offline 断外网守卫（events 文件 `network: external DNS and TCP blocked`）+ 冒烟/驱动 `network_attempts=0` 计数。**真实 Provider 调用数 = 0（有实际计数来源，非 unknown）**。

---

## 三、正式目录回装与重启
- 回装前复核 22 文件 before 哈希无漂移、后端无在途任务（jobs 0）、health ok。
- 停后端（PID 42444，端口 8000 释放）→ dry_run_ok → apply（备份 `20261018T124333Z_c2c35c9b`）→ 重启。
- 重启验证：health ok / controller_ready / Workflow 恢复扫描 6 个活跃 run 对账 0 在途 attempt / Uvicorn 8000 监听（新 PID 3716）。
- git 状态：19 M + 3 新增 + `.collab_patch_backups/`，与补丁清单完全一致。
- **提交存档**（用户批准自修复后）：子仓 `da123e2`（R1.1 全 22 文件 + 本机取消修复 R1.1.1，+1423/−246）；父仓指针 `7bf00da`。
- **取消修复复核材料**：`测试7/COLLAB_CANCEL_FIX_R1_1_1/`（统一 diff + 修复后完整文件 + 前后 SHA256 + 双层回滚说明）。
- **回滚命令**（需先停后端）：
  `python apply_patch.py --project-root "C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard" --rollback "C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard\.collab_patch_backups\20261018T124333Z_c2c35c9b"`

---

## 四、发现与未关闭问题

### 1. 🔴→✅ 取消复活缺口（**已修复并回装正式目录**，用户批准 2026-10-18）
**现象**（A3 集成驱动 F4/F7 实证复现）：取消落在 producer turn 执行中时，`cancel_run` 落盘 `cancelled` 后，执行侧持有的内存 run 快照（仍 running）在后续 `save_run` 中把盘上终态覆盖回 running，run 最终被标记 completed——用户取消被静默复活。
**根因**：`src/agents/collab_modes.py` 的 `save_run` 无条件整本覆盖，执行长流程与盘上状态无 CAS。
**修复**（执行侧自修，约 10 行）：`save_run` 写入前读盘上现态，若为终态（cancelled/completed/completed_with_issues/failed）且与内存态不同→保留盘上终态，仅合并步骤/结果增量。修复后驱动 34/34，切片复跑除既有 flake 外无新失败。
**回装记录**：用户批准后（10-18 晚）同一修复已写入正式目录 `src/agents/collab_modes.py`，与已验证副本逐行 code-only 等同（注释措辞差异仅注明批准来源）；后端二次重启，health ok / Workflow 恢复正常。该修复在 `.collab_patch_backups\20261018T124333Z_c2c35c9b` 之外（补丁备份不含它；如需完全回滚 R1.1 须连带撤销本修复）。建议把 diff 同步给补丁作者复核（无需阻塞）。

### 2. 🟡 R1.1 新用例 `test_lease_cross_process_unique_holder` Windows 时序敏感
**统一命令完整切片（生产同构代码 R1.1+修复，`--timeout=45`，2026-10-18 晚补跑）：122 passed × 2 连跑（23.66s / 22.67s），本轮零失败**——真实测试前的"按统一命令完整跑过"要求已满足。历史 flake 率约 1/4 次全切片运行（失败语义=脚手架 15s 等待超时，非排他性破坏，见下）。
失败=测试脚手架超时（spawn 子进程 15s 未回报，`queue.Empty`），**非租约排他性被破坏**（通过运行中 `[False,True]` 断言正确）。复跑记录：切片内 1 败 / 单独 3 过（1.19s/28.2s/2.08s 波动一个数量级）。属 Windows spawn 冷启动+磁盘噪声；建议作者放宽 deadline 或预热。不阻断假服务开发；涉及写权威域的测试在真实媒体测试前应保持关注。

### 3. 🟡 case6 时长贴近 10s 上限（本机实测 10.12s）
交付全量 10s 口径下必然临界。建议该用例在交付环境也按 60s 干净复查口径管理。

### 4. ✅（已更正）全量对照文件选错
初版报告误以 `full_final.events.jsonl`（R1 时代记录，2835 节点）为 R1.1 对照基准，得出"缺 12 项"表述——系对照文件选错，非证据包缺口。**已改用 `review_r11_final.events.jsonl`（R1.1 最终记录，2847 节点）重核：节点集 2847=2847 完全一致，状态差异 4 项全定性**（见 §二 A4）。

### 5. ⚪ 交付环境 3 项失败在本机通过
case1_e2e_mixed_project / case5_planner_failed_resume_continues / case4_recover_rebinds_child——本机通过不能反证相应生产问题已解决（交付方同样提示），保留观察。

### 6. B/C/D 批未开始
候选过渡池、接纳协调器、确定性派发、宽权限子 Producer、多项目调度均为**未实现**状态（R1.1 的 unattached_* 仍只是保护性留存记录）。E 批真实视频测试按计划 2026-10-19 之后、且 B/C 门槛达成后执行。

---

## 五、结论
- **A 批门槛：passed**。安装/回滚/安全用例/关键切片/前端构建/实际路由与 SSE 对接/恢复差异归类全部完成，0 真实服务调用。
- "已完成本批" ≠ "全系统已验收"：R2 能力（B/C/D）全部待实现；正式目录当前 = R1.1 + 上述已知失败集合（与交付等价且净少 2 项失败）。
- 明日真实视频测试前置条件：A 批已就绪；E 批还要求 R2 模式实现并通过 B/C/D 门槛（若仅 R1.1 则只能做 R1.1 真实冒烟并如实报告 R2=not_implemented）。
- 隔离区与证据索引：`D:\isolated\evidence\`（readonly_smoke_local.json / a3_integration.json + driver / a2_slice* / a4_recovery_trio / a4_full60 / nodeid_diff / recheck_*）；本报告副本数据不涉真实凭据。
