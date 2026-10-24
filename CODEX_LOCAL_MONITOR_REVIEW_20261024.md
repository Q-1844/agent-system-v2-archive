# 本地GLM 5.3监控交接与超时修复（2026-10-24T03:58:28.758382+00:00）

截至 2026-10-24T03:58:28.699481+00:00：运行40055563112为in_progress，B1=RUNNING，累计11个视频任务ACCEPTED（不代表均已完成），图片21次、文本35次。最终>=180秒成片仍待本地独立验收。

## 代码修复

[PR #9](https://github.com/Q-1844/agent-system-v2/pull/9)已合入默认分支chore/migration-readiness，merge `12b1ca4355cc743aa3e12eaeb22f67a015d1038b`，最终测试源码 `1e5193258501d9df0951ecef845ea15c6c649251`。

原驱动达到150分钟时只发pause请求便退出event loop，原生FullRun可以先于SceneRun和队列暂停；已受理视频可能仍未下载。修复为先封锁新图片/视频提交，再最多15分钟等待所有原生控制器停止、项目队列无在途工作、每个ACCEPTED ID有唯一非空完成视频。确认安全后保存drain_complete；超时记录INTERRUPTED，禁止把父任务paused当作可恢复快照。若生产恰已完成，仍需继续媒体验证与归档才能PASS。

**当前40055563112固定运行旧源码c3afe255bec6bccdb52aa8ad3e2bf98ab14db9c2；不会热更新，也没有因新修复重启影片。** 新驱动修复只用于后续运行。本地GLM需要按旧runner上限和实际检查点处理终态。

## 回归和实查

- 针对监控、暂停收尾与既有验收保护：57通过。
- 本机完整：3265通过，10跳过，0失败，0错误。
- 云端[40059904480](https://github.com/Q-1844/agent-system-v2/actions/runs/40059904480)：完整3265通过/10跳过；恢复416通过/10跳过；Agent冒烟28通过；Linux媒体校验/编码/probe/解码通过。
- 云端[40059897928](https://github.com/Q-1844/agent-system-v2/actions/runs/40059897928)：完整3265通过/10跳过；恢复416通过/10跳过；Agent冒烟28通过；Linux媒体校验/编码/probe/解码通过。

回归使用Fake Provider，不替代真实三分钟验收。新监控脚本已用真实GitHub/B1接口执行--once，读取原任务并验证固定身份与既有付费回执，没有产生新的workflow或媒体请求。

## GLM接手文件

- [完整操作说明](CODEX_GLM53_HANDOFF_20261024.md)
- A仓tools/watch_full_project.py：Python标准库，只允许GitHub GET，支持单次或有界值守、三次读取失败停止、心跳/未知回执停止、终态日志和快照收集、SHA256/summary/Registry核对。
- A仓tools/watch_film3m_20261024.json：固定当前run、source、nonce、FullRun和前两个视频ID。
- A仓docs/GLM53_LONG_FILM_HANDOFF.md：Windows/Bash启动、退出码、终态本地媒体/归档恢复验收和失败对账规则。

监控不触发生产、不读Repository Secret的值、不要求Agnes Key、不自动重发。远端成功返回20=CLOUD_PASS_REQUIRES_LOCAL_AUDIT，不能写成最终本地验收通过。当前任务总预算仍240秒，已有成果与原生IDs保留。Producer新能力、预览页等继续后置。
