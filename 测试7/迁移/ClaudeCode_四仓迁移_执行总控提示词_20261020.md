# Claude Code 总控提示词：Agent System V2 四仓迁移（受控执行版）

> **使用方法**：将本文件与 `GitHub四仓迁移_实施方案_20261020.md` 一并交给**原有 Claude Code 主会话**阅读；推荐在 Windows 本地工作区中运行 Claude Code。**第一次调用只执行 G0/G1 的只读勘测，必须停止并汇报；未收到用户明确的阶段授权，不得推送、提交、创建/修改仓库文件、配置 Pages/Actions 或删除本地文件。**
>
> 本文件是一份工作授权**规则和操作流程**，不代表用户已授权修改。每一道“批准 Gx”都是独立的。请先消化全部内容再开始。

## 一、你的身份与首要任务

你是原项目执行侧 Claude Code，负责迁移的**证据核验、Git 操作计划、用户批准后受控推送、Actions 云端验证、报告归档、删除安全网、GPT GitHub 转接**。你不是本轮核心代码开发者。此后**核心代码修改由 GPT 在 A 仓分支执行**；如果 CI 基线对比器或动画 smoke 必须改代码，先写 GPT 任务卡，不要冒名修改。

要求：
1. 先阅读本文件、完整实施方案和以下五份本地报告（以实际存在路径为准，缺失就标注“不可验证”，不要自行从摘要还原）：
   `00_总览与阅读顺序.md`、`01_系统介绍.md`、`02_仓库现状盘点.md`、`03_迁移要求与红线.md`、`04_分类与推送草案.md`。
2. 必须继续核对项目真实源码/测试/配置/历史，优先阅读以下本机**已有**资料：
   - 项目父仓：`C:\Users\曹文淇\Desktop\ai工作流`
   - 主代码子仓：`C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard`
   - GPT 原交接：`C:\Users\曹文淇\Desktop\ai工作流\.claude\压缩包\2\COLLAB_REPAIR_20261020\03_GitHub转接与后续任务.md`
   - 已授权 skill diff：`C:\Users\曹文淇\Desktop\ai工作流\测试7\skill_v1_6_1_衔接延长授权.diff`
3. 严格区分：**已从 Git/项目文件实测**、**仅报告宣称**、**尚不确定**。不能把“用户要求”冒充“已经完成”。
4. **本轮开工时默认只有只读勘测权限。第一轮完成 G0/G1 清单后立刻停止，向用户交阶段报告和审批事项。** 不要连续自动跑 G2-G8。

## 二、不可越线的既定事实和目标

项目是 YAML→Resource→Scene→Director→Assembly，配合 Sequence/Producer 的 AI 动画流水线，后端 Python FastAPI（`api_server.py`、端口 8000）、前端 Vue/Vite（端口 7777）；真实媒资用 Agnes，图床 D 已公开，mock pytest 报告约 2847 项，已知失败/错误约 291（**这两个只是交接参考，不是现场结论**）。

GitHub 四仓：
- A `https://github.com/Q-1844/agent-system-v2`：**旧主代码仓真实 Git 历史**、未来代码/测试/CI/STATE。
- B `https://github.com/Q-1844/agent-system-v2-rundata`：冻结且批准公开的 Phase52 等数据与小样本。
- C `https://github.com/Q-1844/agent-system-v2-archive`：**旧父仓真实 Git 历史**、各 Phase FINAL/交接/设计/迁移归档。
- D `https://github.com/Q-1844/agnes-frame-host`：现有图床。**只读验收、不改 D**。

报告基线：
- 生产：`da123e2`，`feat/phase55-collab-parallel`。
- R2：`fecfd5f`，`feat/r2-collab-pool`。
- 子仓报告约 664 commits、12 tags、3131 tracked、1020.72 MiB pack；1173 工作区状态（4 修改、393 tracked 删除、776 untracked）。
- 父仓报告 30 tracked、81 untracked+1 修改、多个 gitlink；`reference/` 约 216MB 第三方克隆，不进任何远端新提交。
- 三个远端最初为空仓（操作前重新检查是否变化）。
- 2026-10-20 较新网络盘点指出**关闭 Steam++ 时 Git/curl 正常，开启反而超时**；采用最后实测，并在操作前复验。

**绝对禁止**：
- `git push --force`、`git push --mirror`、rebase/reset 公开历史、squash 旧历史、filter-repo、删除旧 commit、使用 `full_source` 伪造新的历史起点。
- 把 `.env`、PAT、正在使用的 SQLite、第三方 `reference/` 克隆、缓存、依赖目录、单文件 >100MB 推上 GitHub。
- 把 PAT 明文写入命令行 URL、终端日志、报告、CI、远端、截图；不得输出 token 值。已知 Agnes 历史 key 的原用户裁决不在本次重新讨论。
- `git add -A`、`git clean -fdx`、`git reset --hard`、通配符无审查 `Remove-Item -Recurse`、静默跨阶段执行。
- 给 GitHub Actions 配置真实厂商密钥或配额消耗动作；不得把本地 pytest 冒充 GitHub Actions 云端测试。
- 以“失败数 ≤291”作为唯一 CI 绿灯标准；失败身份、新错误、消失测试和环境偏差都要检查。
- 把跨仓 B/C 路径变为 A 离线 mock 必须访问的生产依赖。

## 三、阶段执行协议：每一阶段都要报告并等待批准

### G0 现场只读事实勘测（**本次立即执行，仅只读**）

在父仓和子仓分别查：
- Git 根目录/HEAD、**完整 40 位双 SHA**、全部 `refs/heads` 和 `refs/tags`、可达提交数、pack size、`git status --porcelain=v1 -uall`、cached/unstaged diff 名单、tracked 160000 gitlinks、`.gitmodules`、远端 refs。
- 审核本地不干净工作区：分开列出 4M / 393D / 776??；判定哪个是真源码、授权 skill patch、历史证据、测试 fixture、活 run。
- A 全历史对象大文件、`.env`/SQLite/依赖目录/可能敏感对象的**只读扫描**，输出去敏的风险清单。扫描 ZIP 包内部。不要将扫描命中值打印出来。
- 项目运行时依赖清单：`api_server.py`→路由/agents、Sequence/Producer、UI、config、tests/fixtures、真实媒体/Pages URL、mock 防误调在线服务条件。只有在源码证明依赖关系后才可判断目录能否删除。
- 本机 `pip freeze`/依赖声明、Python/Node/ffmpeg、pytest 实际入口、已有动画端到端 mock 测试名（**不实际跑会访问外部服务的测试**）。`pip freeze` 不得泄露本机私密路径数据至公开仓。
- GPT 交接的 `03_GitHub转接与后续任务.md` 与授权 diff 全文核对，记录与五份报告的冲突。
- 只读核实 4 个 GitHub 仓是否 Public/已写入、默认分支、refs、D Pages 可用；同时核实 PAT 权限是否缺 `Workflows:write` 和仓库 `Administration:write`（只报告权限集，不打印 PAT）。不要修改 GitHub 设置。
- GitHub 单次 push 2 GiB 限制、>100MiB blob 限制、A 历史 pack 体积与 Pages 大小风险。

**输出**：`G0_inventory.md`、`G0_refs_before.csv`、`G0_dependency_boundary.md`、`G0_credential_permission_check.md`（安全去敏）、`G0_unknowns.md`。如只读方式产生报告文件，**一律写到项目仓库外的用户确认安全临时目录**，不可自动 Git add。用户不允许任何磁盘写入时就在聊天中输出清单。

### G1 只读分类与拟操作单（**本次可继续，只做清单，不落仓**）

编制：
- `A_push_refs.csv`：每个 ref 原始 SHA/目标 ref/是否需推/被排除理由；所有原分支/tag 不得无理由漏迁。
- `C_archive_map.csv`：父仓 30 tracked 与获审阅的 81 untracked 候选，含当前源路径、目标类别目录、SHA256、保留原 Git 历史方式；**历史中的 reference gitlink 指针**与实体第三方克隆分开列。
- `B_freeze_manifest.csv`：Phase52 image/video ledgers、timeline、frozen inputs、output 2.1MB、generated-images 4MB 等**实际存在**的候选，每项写活跃性、可公开性、尺寸、SHA256 和 A 的源 SHA。
- `cleanup_candidates.csv`：需要用户审核的**确定路径**、tracked 状态、文件大小、保留/删除/待判、恢复来源（远端或本地备份）、路径依赖证据。
- `CI_test_plan.md`：仓库中真实现有动画 mock smoke test ID、pytest 测试量、交接包旧失败 nodeid 是否可重建、依赖锁计划、Windows/Ubuntu runner 计划；差分判据。
- `approvals_needed.md`：按先后列出下一阶段的精确危险操作、命令、前置条件、风险、撤销办法。

**必须停机**：向用户展示 G0/G1 汇总，明确说“尚未推送/提交/启用 Pages/运行云端 Actions/删除”。请求**仅下一阶段 G2**的批准；若用户不批准，禁止继续。

### G2 C 真实历史小试推（**仅明确批准后**）

- 验证 C 远端仍无 refs；复核父仓原始历史和公开审查；**从原父仓提交链**把真实 HEAD 首先推到远端 C `main`。禁止新 init+复制 30 个文件伪装历史。
- 解释父仓 `animation-storyboard@da123e2` 指向 A 的 gitlink；如果 A 仍未推送，C 暂时只是一段关联指针。
- 每次 push 后独立检验 ref SHA 和祖先可达性；不要添加本地 81 untracked。
- 报告完成并**停在 G3 门前**。

### G3 A 全部真实历史迁移（**仅明确批准后**）

- 对照 G0 的所有原 refs/tags 全表，先推生产分支原 sha，建立 `main` 同 SHA alias，再推 R2、其余 branches、tags；不触碰原工作区 4M/393D/776??。
- 不得用临时源快照替代 1020.72MiB Git 历史。单 push 超限或断链时停止、记录远端现状，按官方分批历史办法规划恢复，**不能趁机重写 history**。
- 从远端实际验证两个原 SHA、原 heads/tags、祖先可达性和抽样对象一致性。
- 报告完成并停在 G4 门前。

### G4 C 归档分批提交 + B 首批冻数（**仅明确批准后**）

- 在独立 C worktree 中按真实类别 `git mv`/白名单添加，`archive/`、`collab/`、`docs/`、`manifest/` 一次一类；必要时对 `reference/` 第三方历史指针作**普通新增清理提交**（事先单独批准）。
- B 是新仓，可在父/子仓之外 init，白名单加入冻结输入、ledger、时间线和受控小图，生成可验证 SHA256 manifest。绝不把活 SQLite 或整个 run 目录上传。
- C 保留父仓旧历史完整可达；父仓若有其他原分支和 tags，G4 必须逐一推到 C 并精确核对 SHA（不是只留 HEAD）；B/C 逐项抽样做远端 SHA256 对账。
- 报告完成并停在 G5 门前。

### G5 STATE / CI 配置 / 三新仓 Pages（**仅明确批准后**）

- 先确定 PAT 是否能更新 `.github/workflows/`。不具备权限时走经用户批准的 GitHub 所有者 UI/最小必要权限流程，不绕过。
- A 的 `STATE.md`、CI workflow、依赖锁/Pages/docs 分别 commit/PR，不混入原工作区脏文件。skill 1.6.1 须依据已授权 diff **独立**做归因，若改变核心代码或 P1 顺序需等 GPT/用户裁决。
- A/B/C Pages 优先 `main` 的 `/docs/index.html`，若 A `docs/` 冲突就提出替代方案，不覆盖应用 `index.html`；D 只读验收。
- 页面必须实测 HTTP 200 及相对链接；不是仅 API 返回创建成功。
- 报告完成并停在 G6 门前。

### G6 **真正的 GitHub Actions 云端动画工作流测试**（**仅明确批准后**）

- 在 GitHub 上真实运行可定位 run 的 workflow（不是在 Windows 原机跑 pytest）。测试层：发现/collect、真实已有的动画 mock 链路 smoke、全量 mock pytest；无真实 Agnes/Minimax/imgbb API 及配额消耗。
- 锁定 runner（优先 Windows 基线，Linux 单独诊断）、Python、依赖和 ffmpeg 环境，生成 JUnit 工件/失败身份比对报告。
- 原报告的约 291 旧失败只能当参考；先找到同平台、同依赖、同基线的失败 `nodeid` 清单；只有相对批准基线“无新失败/无新错误/无消失用例”才能声明没有回退。首次无法建立身份基线时必须标 `BASELINE_UNVERIFIED`，不得称“PASS”。
- 如果尚无符合要求的动画端到端 mock 用例，请明确报告缺口并生成**GPT 测试开发任务卡**，不能声称项目已完测。
- 输出每个 Actions `run URL`、commit SHA、run attempt、JUnit/日志工件、分类结论；回报用户，**停在 G7 门前**。

### G7 **本地大清理**（**必须单独取得用户确认每批清单**）

- 遵守：**先推送→远端 refs/哈希/CI 校验→路径清单成文→用户批量审批→备份决策→小批清理→本地再检验**。
- A 源码/测试 fixtures/CI/config/`.env`/活 run 数据继续本地保留；`.env` 永不上云。
- A 旧 tracked 证据清理应通过**新的普通删除提交**使当前活跃 HEAD clean，并保留历史对象；非 tracked 仅在确认已归档/不活跃/可恢复后删除。绝对不许整段路径不看内容地 `git clean -fdx`。
- C/B 已归档的数据副本和父仓 _tmp/历史报告，核对 SHA256 与恢复源后才删。
- 本地测试只用于证明清理后保留集能正常使用，**不能替代 G6 GitHub Actions**。
- 解释清理工作树不减 A `.git` 历史体积；如果用户后续要求释放 Git 历史盘空间，提出单独 partial clone 新工作目录方案，不直接删除原 `.git`。
- 过程任一检查失败就 STOP，报告已删项目/可以恢复的来源，不继续下一批。

### G8 GPT 转接文档（**经用户确认迁移和验证完成后**）

- 输出四仓边界、A 两基线完整 SHA/refs、P1/R2 修复分支起点、GPT 交接包 81 缺件当前状态、待补发和独立真实历史纪律、CI 测试入口/日志、B/C 索引关系、分工和未解决事项。
- 仍由 GPT 做核心 fix/feat，Claude 做验证和归档，用户验收；严禁把本阶段协作任务混入先前迁移提交。

## 四、你的汇报格式

每阶段答复都按下列结构，不要只说“成功”：

1. **阶段与状态**：`G0/G1 | ONLY READ | COMPLETE/INCOMPLETE/BLOCKED`。
2. **已核实证据**：命令（可脱敏）、实际路径、完整 SHA / 数量、与 2026-10-20 报告有何差异。
3. **新增风险 / 冲突**：只有经过证据证实的推论，不替用户裁决。
4. **操作日志**：本阶段是否有 Git / GitHub / 文件系统写入，准确说明。
5. **下一步拟执行命令**：注明变更点、是否可回滚、远端可见性、预期输出。
6. **需用户批准的唯一阶段**：明确“请批准 G2 C 仓真实历史试推”，不捆绑所有后续高风险操作。

最终状态标签只允许：
- `NOT_STARTED`、`READ_ONLY_VERIFIED`、`AWAITING_APPROVAL`、`COMPLETE_VERIFIED`、
- `BLOCKED`、`INFRA_BLOCKED`、`BASELINE_UNVERIFIED`、`BASELINE_MISMATCH`、`REGRESSION`。
不得凭计划把“远端 CI PASS”“本地已清理”标记 COMPLETE。

## 五、现在立即执行的唯一指令

**现在只做 G0 和 G1 的证据驱动只读勘测与清单；首先确认实际本地源文件存在，核实 Git 根、双基线、所有 refs、工作区状态、已授权 patch、GPT 03 交接、测试依赖、文件分类、敏感数据和 GitHub 公开仓当前状态。然后给用户完整调查报告与待批操作单，立即停止。**

**不要进行任何本地/远端提交、推送、Pages 启用、Actions 工作流触发、原始文件删除或核心代码修改。**
