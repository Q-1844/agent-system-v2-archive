# ink-diffusion 完成审核：尚未完成，Pages 发布误判已修复

## 审核结论

`ink-diffusion-20m-20261105` 已跨日续产，但不能宣告整片完成。原 run [42252251047](https://github.com/Q-1844/agent-system-v2/actions/runs/42252251047) 从 106 镜 / 889 秒推进至 **114 镜 / 953 秒**后，因 `s04_c26`、`s05_c05` 的尾帧图生图输入 URL 不可下载而 FAILED。冻结计划 **145 镜 / 1192 秒**，FullRun 仍是 `frun_9b6951965f`。

114 条 ACCEPTED 均对应已完成、已选中视频；115 条意图为 114 COMPLETED + 1 REJECTED，零 SUBMITTING/UNKNOWN。上一跳 106 个视频的 ID、版本、SHA256 与当前 artifact 逐项一致。

## 真实根因

- 两个失败镜头均 inherit_previous，首帧来自 `s04_c25` / `s05_c04` 的真实视频末帧。本地 JPEG 与 D 仓 Contents 字节都存在。
- D 仓 Pages [42260516611](https://github.com/Q-1844/agnes-frame-host/actions/runs/42260516611) 的 build 完成，但 deploy 等待 600000ms 后超时；两张图片 URL 仍为 404。
- `GithubPagesHost.upload()` 在 GET-first 内容匹配时直接返回，跳过 `_wait_ready()`，使重试把「已入库但未发布」误当成可用 URL。图片供应商随后报 `400 media URL could not be downloaded`。
- 原 artifact `13524649308` 完整下载：832684988 字节；SHA256 `1a99fc2831cce24ad1a04e0c18c6a53b277364cf7648e39359582a1ab7ed693f`。

## 修复与测试

[A PR #51](https://github.com/Q-1844/agent-system-v2/pull/51) 已合并，merge SHA `fbba2a6f435e7bd0b74afe143cc250e0770b11ea`。

1. 内容匹配只免 PUT，仍检查 Pages 200；不重复上传同一字节。
2. 图片生成优先使用已保存资产的原字节 data URI，保留逻辑 URL / receipt key / 参考顺序，不将 base64 持久化。
3. 对旧快照中的 Pages URL，新视频提交前复查发布；检查发生在意图登记、POST 之前。已有任务的续轮询不受影响，原输入守卫仍在等待后复验。
4. 保留三次末帧重试、120s 退避和1200s终试等待及其结构测试。

新增 9 项回归通过。本地全量 **3894 项：3884 passed、10 缺 P55 样本 skipped、0 failed/errors，476.987s**。随后取回 SHA 核验一致的真实 P55 样本，相关两文件补跑 **15 passed、0 skipped**，覆盖全部 10 项先前跳过。

原始快照经 `restore_snapshot` 真实恢复，用原生尾帧 handler 和本地供应商替身回放两处失败镜头成功；全部 114 个完成视频的 ID、版本、SHA256 不变；离线回放真实付费请求为零。

## 图床恢复和原片续跳

- D 仓 failed-job retry 获受理但仍排队且无新 job；随后显式请求 Pages build，最终 built。
- 原两个 URL `objects/06b6023117e7199c.jpg`、`objects/392ce53d36aefe50.jpg` 已独立 GET=200、image/jpeg，并与 artifact JPEG 逐字节一致。
- 原片续跳已派发并运行：[42276180756](https://github.com/Q-1844/agent-system-v2/actions/runs/42276180756)，使用上述 merge SHA。
- 参数：原 nonce，`resume_run_id=42252251047`、`target_duration_seconds=auto`、`media_inflight=2`、`confirm_uncertain_submissions=true`。继续用户已允许可能重复计费换取接续的授权；原快照本次没有 UNKNOWN，不需要重提任何已受理视频。
- 本文只确认修复测试、图床发布恢复和派发成功；不将新 run 的 in_progress 冒充生产推进或整片完成。

## 后续验收

检查同一 FullRun / nonce / 计划指纹；114 镜基线全部保留；两个失败尾帧成功；新有效视频超过 114。随后等待145镜完成、最终 MP4 全量解码通过、归档回读与 restore full 通过，且 B1 / 注册表均 COMPLETE，才能宣告本次长片整链完全成功。

A 仓审查与机读证据：`docs/REVIEW_ink_publication_recovery_20261107.md`、`docs/evidence/ink-publication-audit-20261107.json`。本轮不新开影片，不等待长片生产完成。
