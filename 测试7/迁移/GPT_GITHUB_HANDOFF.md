# GPT GitHub 接入说明（G8 交接，2026-10-21）

> 致 GPT：四仓迁移已完成并核验。本文件是你恢复工作后的接入凭据与第一批任务。

## 一、仓库地图

| 仓 | 地址 | 用途 | Pages |
|---|---|---|---|
| A 主代码 | https://github.com/Q-1844/agent-system-v2 | 你的代码修改在此进行 | https://q-1844.github.io/agent-system-v2/ |
| B 运行数据 | https://github.com/Q-1844/agent-system-v2-rundata | 冻结批次归档 | https://q-1844.github.io/agent-system-v2-rundata/ |
| C 档案 | https://github.com/Q-1844/agent-system-v2-archive | 报告/交接/迁移记录 | https://q-1844.github.io/agent-system-v2-archive/ （开通构建中） |
| D 图床 | https://github.com/Q-1844/agnes-frame-host | 只读验收，勿改 | https://q-1844.github.io/agnes-frame-host/ |

## 二、A 仓锚点（推送后逐条 SHA 核验一致）

- 生产基线：`da123e22e0b413b5118c6d87632cda72204422d7` @ `feat/phase55-collab-parallel`
- R2 实验线：`fecfd5f5bb90b59abb432abec4f5e166674205f2` @ `feat/r2-collab-pool`
- `main` = `e462b06`（= 基线 + 迁移 5 提交：skill 1.6.1 / CI / STATE.md / docs / requirements 修复），见 A 仓根 `STATE.md`
- 全部 28 refs + 12 tags 原样迁移；对账单：测试7/迁移/G0G1_清点_20261020/refs_before_child.csv

## 三、CI（已实跑）

- 工作流：`.github/workflows/ci.yml`（`mock-regression`），windows-latest + Python 3.13 + `requirements-ci.txt`
- 首跑（commit e462b06，2026-10-21）：**2847 项全部收集并执行（638s），failures=157 / errors=228（合计 385 未通过）**
  - Run URL：https://github.com/Q-1844/agent-system-v2/actions/runs/39516733875
  - JUnit 与原始日志证据：C 仓 `测试7/迁移/CI证据_首跑/`
- 已知失败基线 ~291（交接包口径）vs 云端 385：**差值=云端环境差异，待身份校准**；请勿以总数判定，按 nodeid 身份差分
- 你的对比器/测试修改如需改核心代码 → 分支 + PR（Claude 侧验证归档）

## 四、凭据

- fine-grained PAT（90 天，All repositories）：Contents / Pull requests / Pages / Workflows = Read and write
- 本机位置：`C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard\.env` 的 `GITHUB_TOKEN=`（勿入仓、勿写日志）

## 五、恢复后第一批任务（依你 03 文档 §2/§4）

1. 补发 COLLAB_REPAIR 缺失的 81 文件（截断证据与清单我方已定档）
2. 从 `da123e2` 建 `collab/production-p1`、从 `fecfd5f` 建 `collab/r2-p2`（P1 含于 r2-p2 口径按你 03 文档核对）→ 应用补丁 → 本机回归 → PR 到对应分支
3. `skill 1.6.1` 已单独提交（`6e0bd2a`，归因=用户授权 diff），勿重复处理
4. CI 身份基线校准（可选，用首跑 JUnit nodeid 清单）

## 六、纪律（不变）

真实历史不重写；full_source 快照不伪装历史；活 SQLite/.env/大媒体永不入仓；实验改核心走候选分支保留原始失败；B/C 冻结数据以 source SHA 关联 A，不建运行时依赖。

—— 执行侧 Claude Code，2026-10-21
