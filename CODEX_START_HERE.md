# CODEX_START_HERE — GitHub 自主视频生产系统交接（给 Codex 中转站）

- 日期：2026-10-23 ｜ 由 Claude Code 完成 + 提交本文件到 C 仓 `agent-system-v2-archive` 分支 `feat/codex-handoff-20261023`
- 交接前提：A/B/B1/C 仓真实远端已部署可运行工作流；relstore 代码已在 A 仓默认分支
- 本文件 = Codex 入口；详细证据见同分支 `GITHUB_AUTONOMY_E2E_REPORT.md`，运行态见 `GITHUB_RUNTIME_STATUS.md`

## 一句话现状

GitHub 上**真实 Agnes 视频生产 + 跨仓保存 + 状态整理 + 巡检循环逻辑已跑通并交叉核验**（非 mock）。唯一未"亲眼看到"的是 GitHub 调度器自己按 cron 触发的那一次 schedule 巡检（已配置 active，GitHub schedule 有抖动/跳过，未在测试窗口内观察到 fire）。

## 仓库职责（真实远端默认分支）

| 仓 | 远端 | 默认分支 | 职责 |
|---|---|---|---|
| A | `Q-1844/agent-system-v2` | `chore/migration-readiness` | 代码 + 工作流 + 驱动（relstore 在 `tools/relstore/`、`tools/e2e_autonomous_run.py`、`tools/patrol_run.py`） |
| B | `Q-1844/agent-system-v2-rundata` | `main` | 成品持久存储（Release + asset，含历史 15 战役 tar） |
| B1 | `Q-1844/agent-system-v2-rundata-1` | `main` | 活跃项目 Registry 状态（CAS state.json，测试命名空间 `test/e2e-*`） |
| C | `Q-1844/agent-system-v2-archive` | `main` | 报告 + 交接文档（本文件所在） |
| D | `Q-1844/agnes-frame-host` | — | 图床（非本轮） |

## 已部署工作流（均在 A 仓默认分支 `chore/migration-readiness`，active）

1. `ci.yml`（mock-regression）— 预存；**当前 failure**（加 relstore 进 `tests/` 后，见 runtime-status 已知问题）
2. `video-autoproduction-e2e.yml` — `workflow_dispatch` 单次真实生产（Agnes t2v→MP4→ffprobe→存 B Release→B1 Registry）
3. `video-patrol.yml` — `schedule: '*/10 * * * *'` + `workflow_dispatch`；巡检 `tasks/pending/*.json`，B1 state.json 存在性做 dedup，无任务 idle

## 必需 GitHub Secrets（仅名称，不含值；已在 A 仓配置）

- `AGNES_API_KEY` — 真实 Agnes 生成（廉价 key，用户政策可入 secret）
- `B1_ARCHIVE_TOKEN` — B/B1 仓 fine-grained PAT（永久 Contents:write），用于 A 工作流跨仓写 B Release + B1 state.json

## Codex 接手优先级

1. **观察一次真实 schedule 触发的 video-patrol run**（GitHub 按 cron 自己 fire；本轮未在窗口内观察到）→ 拿到后即满足 `GITHUB_BASELINE_OPERATIONAL=YES` 的最后一环
2. 修复 `ci.yml` mock-regression failure（relstore 测试进 `pytest tests/` 后的 collection/交互问题）
3. cron `*/10` 是演示用，改为合理间隔或事件驱动（避免每 10 分钟跑一次）
4. 任务源目前是 `tasks/pending/*.json` 手动提交；Codex 可接真实任务源（issue/API/Registry 驱动）
5. 真生成可选 i2v（需公开图 URL）替代 t2v（身份一致性更好）
6. A 仓 git 历史 reconciliation：远端有 Contents-API 提交，本地 `feat/relstore-integration-handoff` 分叉；如需 git 推送先 `fetch + reset --hard` 到远端 HEAD

## 调用方式（Codex 自取）

- 触发单次生产：`POST /repos/Q-1844/agent-system-v2/actions/workflows/video-autoproduction-e2e.yml/dispatches` `{ref,inputs:{task_nonce}}`
- 触发巡检：同上 `video-patrol.yml`
- 读 run：`GET /repos/.../actions/runs/{id}` + `/logs`（zip）
- collab-rw PAT（All-repos Contents/PR/Pages/Actions:write）由用户直接交付 Codex（不入仓）

详细证据 + 运行态 + 已知问题见同分支另两份文档。
