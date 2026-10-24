# 下载失败复核与原项目接续（洛杉矶2026-10-23）

**最新复核：原长片40002008268已于洛杉矶2026-10-23 11:33（18:33 UTC）失败，未达到180秒。两段各10.125秒的视频已完整解码并备份到B；PR #6修复下载与原任务接续。定时schedule已观察到3次成功，狭义单段云端基线现为4/4；三分钟完整制作仍未验收。**

## 实际终态

[40002008268](https://github.com/Q-1844/agent-system-v2/actions/runs/40002008268)从18:16:56 UTC至18:33:55 UTC执行约17分钟，以failure结束。B1检查点FAILED；FullRun frun_80b1bd5120、ProjectRun prun_4ddff9a28f、SceneRun run_4029a80181。s01_c01、s01_c02已完成，s01_c03尾帧阶段失败。

两次尾帧请求都已收到图片结果，但在routers/shots.py调用AgnesClient.download的GET/TLS连接阶段超时。不是生成接口拒绝，也不是新FRAME_HOST_TOKEN权限问题。旧实现未保存返回的图片URL，又发起了一次图片生成。原动作合计15文本、4图片、2次10秒视频提交；无第三次视频POST。

## 素材核验与备份

- 两个视频实际视频流均10.125秒、H.264、1260×720，含AAC；ffmpeg -xerror完整解码成功。它们是部分源素材，不是三分钟成片。
- s01_c01：3,841,027字节；SHA256 2271cfc9a107f24a89c64aa785bf4b84c2275cf98ecf7ecd328747ebb221a7a4。
- s01_c02：3,059,330字节；SHA256 8a202054ed5134f653ec182c953c67c05a3e03332ed7aeb797c7e116effc00d3。
- Actions artifact 12523292315，共10,365,423字节；下载SHA256 f88ea85661ad2433b267a04328ad9f2660bbac6f06dc0caebfcb023be6d72dac，与GitHub回执一致。
- 已备份到B仓draft Release 422455125，tag `partial-film/film3m-20261023-rescue5/run-40002008268`，asset 670987705 original-actions-snapshot.zip；重新下载SHA对账通过。明确PARTIAL_NOT_ACCEPTED，不写成最终VERIFIED_RESTORABLE。
- 实际快照离线恢复后仍为原20镜头/200秒规划，已完成视频字节不变，创作source signature与原FullRun一致。

## PR #6修复

[PR #6](https://github.com/Q-1844/agent-system-v2/pull/6)，当前源码`50966f807e260503ba91de93c565193784c8e96d`。

- 资产GET在连接/读取/临时HTTP错误时有界重试；无API授权头，临时文件完整收货后原子替换，失败保留旧文件。
- 尾帧优先请求内联图片，URL回退先保存独立恢复日志；匹配模型、绑定basis、首帧及实际输入后复用同一URL。原依赖变更guard保持，未通过guard的结果不写入canonical批次。
- 原FullRun resume接回原ProjectRun；仅失败图片阶段重试，已完成视频不重发，已取消与视频结果不明的工作不自动重试。
- 显式resume_run_id下载原失败Actions快照，校验身份与SHA、限制提取目录、确认原生任务均已停止、校验所有已受理视频均有唯一完成文件，再恢复路径与累计计费记录。
- nonce仍为film3m-20261023-rescue5，复用原Full/Project/Scene IDs及两个视频；已用20秒仍计入240秒总预算。不会换nonce清零。

新保护22项通过，结合既有绑定/提交保护60项通过。第一轮完整回归揭示未提交回执不应进入canonical批次，已按原断言修正为独立恢复日志；最终本机与云端回归仍待回执。新接续尚未启动，不把修复、备份或Mock绿色当作长片完成。

## 定时实触发已取得证据

| 自动运行 | 创建时间UTC | 事件 | 结果 |
| --- | --- | --- | --- |
| [40015702924](https://github.com/Q-1844/agent-system-v2/actions/runs/40015702924) | 2026-10-23T19:59:23Z | schedule | success |
| [40037377899](https://github.com/Q-1844/agent-system-v2/actions/runs/40037377899) | 2026-10-23T23:02:58Z | schedule | success |
| [40050012987](https://github.com/Q-1844/agent-system-v2/actions/runs/40050012987) | 2026-10-24T01:29:22Z | schedule | success |


三次均是event=schedule、默认分支源码488ffa7fbc76499bee8037ae1078aa0d12de3b95，非workflow_dispatch。最早19:59:23 UTC的运行已补上原单段云端基线最后一项；cron仍为GitHub best-effort，不声称每20分钟准确运行。此结论不等于完整FullProject三分钟验收。

机器证据：[CODEX_MEDIA_RECOVERY_EVIDENCE_20261024.json](CODEX_MEDIA_RECOVERY_EVIDENCE_20261024.json)。Producer新能力、预览页与新任务来源继续后置。
