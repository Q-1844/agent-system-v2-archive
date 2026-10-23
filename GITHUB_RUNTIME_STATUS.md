# GitHub运行态（2026-10-23）

**当前部署：PR #1–#5均已合入默认分支`chore/migration-readiness`，合并提交`488ffa7fbc76499bee8037ae1078aa0d12de3b95`。最新三分钟真实验收运行[40002008268](https://github.com/Q-1844/agent-system-v2/actions/runs/40002008268)；截至2026-10-23T18:24:41.931326+00:00，workflow=in_progress、检查点=RUNNING。最终成片尚未验收。**

最新报告：[CODEX_COLD_START_CONTROLLER_FIX_20261023.md](CODEX_COLD_START_CONTROLLER_FIX_20261023.md)。

PR #1巡检/恢复、#2三分钟验收/旧任务暂停、#3真实图床PUT预检、#4媒体环境/Windows锁、#5冷启动控制器去重均已合入。

当前真实nonce=film3m-20261023-rescue5，阶段={'action': None, 'scene': None, 'stage': 'production', 'status': 'producing'}；视频提交=1；已确认Provider ID=1；成片未验收。

前次39998736879：新Secret/媒体环境通过，重复控制器导致文本阶段blocked，4文本、0图片、0视频。更早39994958081仅FFmpeg安装失败，媒体未执行。

| 云端运行 | 完整Mock | 存储/恢复 | Agent冒烟 | Linux媒体工具 |
| --- | --- | --- | --- | --- |
| [40001872646](https://github.com/Q-1844/agent-system-v2/actions/runs/40001872646) | 3198通过、10跳过 | 349通过、10跳过 | 28通过、0跳过 | 下载/SHA/编码/探测/解码通过 |
| [40001864912](https://github.com/Q-1844/agent-system-v2/actions/runs/40001864912) | 3198通过、10跳过 | 349通过、10跳过 | 28通过、0跳过 | 下载/SHA/编码/探测/解码通过 |


本机专项399通过、10跳过。最终全量3198通过、0失败、10跳过；此前后台任务清理及随机指纹误报均已修复，证据见最新报告。

原5.184秒单段39961036358及手动巡检39962609983成功；它们不能充当本次三分钟完整制作验收。schedule最新总数仍0；Producer扩展、预览页与新任务来源后置。
