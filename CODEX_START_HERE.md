# Codex接手入口（最新复核）

**最新复核：原长片40002008268已于洛杉矶2026-10-23 11:33（18:33 UTC）失败，未达到180秒。两段各10.125秒的视频已完整解码并备份到B；PR #6修复下载与原任务接续。定时schedule已观察到3次成功，狭义单段云端基线现为4/4；三分钟完整制作仍未验收。**

先读[下载与接续报告](CODEX_MEDIA_RECOVERY_REVIEW_20261024.md)。历史文档的RUNNING、schedule=0或“待合入PR #5”均是早期快照，不能覆盖最新状态。

- A默认分支chore/migration-readiness，PR #1–#5已合入；PR #6分支collab/media-download-resume-20261024待最终回归与合入。
- 三分钟测试原nonce=film3m-20261023-rescue5，原失败run=40002008268。接续必须复用其快照、累计提交预算和已完成视频，禁止盲目换nonce重做。
- B/B1归档与图床凭据：AGNES_API_KEY、B1_ARCHIVE_TOKEN、FRAME_HOST_TOKEN；新图床Secret已实证可写。
- B仓部分成果备份draft Release 422455125 / asset 670987705，状态PARTIAL_NOT_ACCEPTED。
- A=生产代码，B=Release资产，B1=Registry/检查点，C=文档，D=公网参考图。C交接分支feat/codex-handoff-20261023。
- 用户已批准整顿、修复、合入与真实测试；真实成片至少180秒。Producer新能力、预览页、素材扩展后置。旧5秒demo2仍enabled=false。
