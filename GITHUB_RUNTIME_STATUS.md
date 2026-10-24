# GitHub运行态（2026-10-24T02:49:44.394459+00:00）

**最新复核（2026-10-24T02:49:44.394459+00:00）：PR #6–#8已合入；原项目接续运行40055563112，当前RUNNING，累计3次视频提交（含原两个已完成视频），三分钟成片尚未验收。真实schedule已观察到3次成功，狭义单段云端基线4/4。**

先读[下载、尾帧与接续复核报告](CODEX_MEDIA_RECOVERY_REVIEW_20261024.md)。历史文档的RUNNING、schedule=0、待合入PR #5/#6/#7均是早期快照。

- A默认分支chore/migration-readiness；PR #1–#8已合入；最新merge `c3afe255bec6bccdb52aa8ad3e2bf98ab14db9c2`。
- 当前真实测试[40055563112](https://github.com/Q-1844/agent-system-v2/actions/runs/40055563112)；source `c3afe255bec6bccdb52aa8ad3e2bf98ab14db9c2`；scope=full-project-3min；原nonce=film3m-20261023-rescue5，必须复用其快照、累计预算和已受理视频，禁止换nonce清零。
- 失败历史：40002008268为CDN GET超时，40053946925为内联尾帧缺公网URL。两个原视频与新尾帧已备份B、SHA重下载核对；新运行的素材验收仍待最终回执。
- 凭据名称AGNES_API_KEY、B1_ARCHIVE_TOKEN、FRAME_HOST_TOKEN；不保存或展示token值。
- A=生产代码；B=Release资产；B1=Registry/检查点；C=文档；D=公网参考图。C分支feat/codex-handoff-20261023。
- 用户已批准整顿、修复、合入与真实测试；真实成片至少180秒。Producer新能力、预览页、素材扩展后置。旧5秒demo2仍enabled=false。
