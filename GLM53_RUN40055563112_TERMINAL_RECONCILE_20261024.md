# 运行 40055563112 终态对账与时间预算结论（GLM 5.3 值守，2026-10-24）

本地值守接管于 2026-10-24 15:38（UTC 07:38）。运行早已终态，未轮询、未派发、未改任何代码；仅只读取证并对账。

## 终态判定：INTERRUPTED_RECONCILE（无任何环节故障）

- Actions 40055563112：completed / conclusion=failure，02:46:23Z 启动、05:18:04Z 结束（151m41s）。
- B1 检查点（test/e2e-film3m-20261023-rescue5 分支）：phase=RUNNING、error=null、saved=null，最后心跳 05:17:33Z。
- 驱动日志原文：`full-project acceptance failed (TimeoutError): 150-minute test deadline; evidence retained, no blind restart`。
- 判定依据：旧 runner 撞 150 分钟驱动保险丝，属交接文档 §6 预言场景；监控器退出码 4，已停止自动动作。

## 身份与资产核验（全部通过）

- 身份链：run_id 40055563112、head_sha c3afe255bec6bccdb52aa8ad3e2bf98ab14db9c2、nonce film3m-20261023-rescue5、request_sha256 8b42d98b…、FullRun frun_80b1bd5120、复用凭证前缀 2/2 匹配。
- 预算：20/20 视频任务 ACCEPTED（含复用 2 个），累计 200s / 240s；图片 41、文本 57。无超支、无重复提交。
- e2e-evidence 归档（ID 12548693050）：135,862,027B / 121 文件，API 官方 sha256 e2d08aa8160901374974cec41ec11f15eea961564704b09a023333a63ed2fdb5，本地下载校验一致。
- 归档内 20 个镜头 mp4 全部在位（69.7MiB）：19 个 job 完整落账；s05_c04 job 状态 running/progress=100，其 mp4（s05_c04_vv_b0c76b8f4bc3.mp4）atom 链完整闭合（ftyp→moov→free→mdat，合计恰 3,002,801B），仅收尾登记被切断。素材无缺口。
- 成片：未开始。stage=production 全程，无合成、无 final.mp4、无 B1 归档、无 Release。

## 真实生产节奏（本次实测，rescue 模式、现成人物素材）

- 18 个新镜头提交跨度 02:48:53Z→05:11:16Z ≈ 143 分钟，平均约 8 分钟/镜（AGNES_VIDEO_INFLIGHT=1 串行节奏，用户确认该设计保持）。
- 第 20 镜 05:11:16Z 提交，距保险丝仅 6.5 分钟，不足以完成等待+下载+合成收尾。
- 归档上传实测：129.6MiB 用时约 4 秒（机房对机房）；仓库间传输不是瓶颈，生成速度才是。

## 用户口径时间预算（2026-10-24 16:15 确认）

- 3.2 分钟成片从零（含素材创建→首帧→视频）：一般约 4.5 小时，最多约 5 小时。
- 有现成素材、1 分钟片、更换视频模型：耗时口径不同，不能用单一常数。
- A 仓为公有仓库，Actions 分钟免费不限量；时长瓶颈纯为时限配置，与成本无关。

## 建议（供 Codex 决策，值守方不代改代码）

1. 本次收尾：显式 resume_run_id=40055563112 入口，复用 nonce、原生 IDs、累计 200s 预算与全部素材，仅剩合成+校验+B1 归档+Release，预计十几分钟。严禁新 nonce 清零重做。
2. 保险丝参数：固定 150 分钟已被实测证伪（本次带现成素材尚且 143 分钟才完成提交）。建议参数化（env 或 workflow input，按目标片长/模型/有无素材取值），3.2 分钟从零场景默认 >=330 分钟；并保持比 workflow timeout 早 30 分钟的优雅缓冲（workflow timeout 相应 180→360，不超过 GitHub 6h 硬顶）。
3. 两层保险丝+超时结构与 AGNES_VIDEO_INFLIGHT=1 维持现状（用户 2026-10-24 确认设计良好）。

## 证据索引（本地 evidence/film3m-40055563112/）

- watch-binding.json（身份绑定）、latest.json / snapshot-last-good.json（终态快照）、timeline.jsonl
- actions-logs.zip（17,182B，sha256 3d59f4122c2f5e6175d8dfa87f46195b79d85044a2b85393e6263e6a0612f96d）
- e2e-evidence.zip（135,862,027B，sha256 校验通过，见上）
- evidence.json（下载与校验记录）；包内 e2e_run/…/summary.json、progress.json、planned-duration.json、cache/jobs.json 已只读核验
