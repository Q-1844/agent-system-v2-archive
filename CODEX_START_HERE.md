# Codex接手入口（2026-10-23）

**当前部署：PR #1–#5均已合入默认分支`chore/migration-readiness`，合并提交`488ffa7fbc76499bee8037ae1078aa0d12de3b95`。最新三分钟真实验收运行[40002008268](https://github.com/Q-1844/agent-system-v2/actions/runs/40002008268)；截至2026-10-23T18:24:41.931326+00:00，workflow=in_progress、检查点=RUNNING。最终成片尚未验收。**

最新报告：[CODEX_COLD_START_CONTROLLER_FIX_20261023.md](CODEX_COLD_START_CONTROLLER_FIX_20261023.md)。

用户已批准整顿、修复、合入；任何真实视频验收成片至少180秒。Producer新能力、预览页与素材扩展后置。先读最新报告，再读[GITHUB_RUNTIME_STATUS.md](GITHUB_RUNTIME_STATUS.md)；历史批次中的“缺Secret/待合入/5秒成功”不能覆盖当前状态。

| 仓库 | 角色 |
| --- | --- |
| A Q-1844/agent-system-v2 | 生产代码/调度；默认chore/migration-readiness |
| B Q-1844/agent-system-v2-rundata | Release成片与项目归档 |
| B1 Q-1844/agent-system-v2-rundata-1 | Registry/CAS持久检查点 |
| C Q-1844/agent-system-v2-archive | 文档；交接分支feat/codex-handoff-20261023 |
| D Q-1844/agnes-frame-host | 公网参考图 |

A仓Secrets：AGNES_API_KEY、B1_ARCHIVE_TOKEN、FRAME_HOST_TOKEN；D凭据不再隐式复用B1。新FRAME_HOST_TOKEN已真实验证，无需再次索取。

下一步核查[40002008268](https://github.com/Q-1844/agent-system-v2/actions/runs/40002008268)终态、视频流至少180秒、独立源视频及B/B1归档恢复；有付费提交或不明结果时先对账，不盲目重做。旧5秒demo2已enabled=false。schedule实触发单独保留未验证。

接手先fetch保留已有分叉与skill/未提交改动，不无条件reset --hard。
