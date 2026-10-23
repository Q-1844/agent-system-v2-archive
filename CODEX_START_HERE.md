# Codex 接手入口（2026-10-23）

**部署状态：A 修复分支提交 `a929e75` 已发布；默认分支仍为 `061735c`，尚未合入。默认分支更新被自动审批拦截，待用户批准具体 PR。以下修复说明指待合入代码；线上 cron 当前仍是原有 `*/10`。**
先读 [本轮运行链复核与修复报告](CODEX_RUNTIME_REVIEW_20261023.md)，再读本分支 `GITHUB_RUNTIME_STATUS.md` 和历史 `GITHUB_AUTONOMY_E2E_REPORT.md`。

两轮最终 GitHub CI 已全部成功，每轮完整回归为 3162 passed、10 skipped、0 failed、0 errors。

审阅入口：[A 仓 PR #1](https://github.com/Q-1844/agent-system-v2/pull/1)。最终源码的机器证据见 `CODEX_RUNTIME_TEST_EVIDENCE_20261023.json`。

## 本轮范围与能力边界

用户最新决定：先整理并修复既有系统；Producer 自主工具、预览页、跨仓素材扩展和新任务来源留在后续设计。

原真实 Agnes 单段 t2v → MP4 → B Release → B1 Registry 已通过运行记录与原始字节 SHA 重新核实。该成功来自 `tools/e2e_autonomous_run.py`，不等于完整 Director/Planner/SceneRun/composition 系统已在 GitHub 自主运行；E2E 分支内的单项目 Registry 也不证明全局多项目容量调度。

本轮补上终态去重、失败退出码、逐任务回执、付费提交前持久化检查点、已知视频接续、跨仓中断恢复与 Registry CAS 校验。提交结果不明且没有 video_id 的任务会保留检查点等待对账，不自动重发。旧版缺少检查点的中断任务需要单独对账。

## 仓库职责

| 仓库 | 默认分支 | 职责 |
| --- | --- | --- |
| `Q-1844/agent-system-v2`（A） | `chore/migration-readiness` | 代码、测试、工作流与驱动 |
| `Q-1844/agent-system-v2-rundata`（B） | `main` | Release 成品与归档 |
| `Q-1844/agent-system-v2-rundata-1`（B1） | `main` | Registry；当前 E2E 使用隔离的 `test/e2e-*` 分支 |
| `Q-1844/agent-system-v2-archive`（C） | `main` | 报告和交接；本交接在 `feat/codex-handoff-20261023` |
| `Q-1844/agnes-frame-host`（D） | 以仓库实际设置为准 | 图片托管，本轮未扩展 |

## 工作流与凭据

- `video-autoproduction-e2e.yml`：手动单次单段生产或已有任务的幂等核对。
- `video-patrol.yml`：文件任务队列巡检，定时和手动触发；定时成功须有 `event=schedule` 的真实运行证据。
- `ci.yml`：运行恢复专项、完整 mock 回归、既有 Agent 管线冒烟。各项结果分别查验，完整回归不因专项通过而自动算绿。
- A 仓 Secrets：`AGNES_API_KEY`、`B1_ARCHIVE_TOKEN`。这里只记录名称；不要把值、Authorization 或凭据文件提交入仓。

具体部署提交、测试数字和实际定时触发状态以 A 仓本轮报告和 `GITHUB_RUNTIME_STATUS.md` 为准。历史报告中的 `3/4` 只指单段云端基线的四个环节，不是完整系统完成率。

## 本地接手

先 `git fetch` 核对远端。已有分叉和未提交修改要保留，尤其已有 skill 修改。推荐从远端建立独立 worktree；不能沿用旧交接中无条件 `reset --hard` 的建议。

任务 nonce 代表不可变单段请求。新增任务仍使用既有 `tasks/pending/*.json`；任务接入与 Producer 新能力尚未扩展。
