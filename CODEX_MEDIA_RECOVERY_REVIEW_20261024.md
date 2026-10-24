# 原项目下载、尾帧托管与接续复核

**最新复核（2026-10-24T02:49:44.394459+00:00）：PR #6–#8已合入；原项目接续运行40055563112，当前RUNNING，累计3次视频提交（含原两个已完成视频），三分钟成片尚未验收。真实schedule已观察到3次成功，狭义单段云端基线4/4。**

## 实测边界

| 运行 | 实际结果 |
| --- | --- |
| [40002008268](https://github.com/Q-1844/agent-system-v2/actions/runs/40002008268) | 失败：第三镜尾帧已生成，CDN GET/TLS超时；15文本、4图片、2视频提交 |
| [40053946925](https://github.com/Q-1844/agent-system-v2/actions/runs/40053946925) | 失败：原任务成功恢复、新尾帧已完成，但视频等待尾帧公网URL超时；累计16文本、5图片、仍2视频，无新视频POST |
| [40055563112](https://github.com/Q-1844/agent-system-v2/actions/runs/40055563112) | in_progress / None；B1=RUNNING；累计3次视频提交 |


继续使用nonce `film3m-20261023-rescue5`，原project `cloud3min_film3m-20261023-rescue5`、FullRun `frun_80b1bd5120`、ProjectRun `prun_4ddff9a28f`、首段SceneRun `run_4029a80181`。原规划5个故事段、20镜头、200秒；最终成片必须ffprobe实测>=180秒、完整解码、所选版本与生成回执对应、B/B1保存和重新下载SHA核验后才算验收。当前没有达到该终态，不以Mock回归或部分片段代替。

第一次接续已实际证明：原生Full/Project/Scene IDs保留、前两镜不重发、第三镜继续；5次累计图片调用中新增一次尾帧，文件已完成。失败发生于视频付费提交之前。第二次接续从40053946925的完整快照恢复，复用该尾帧，不重新生成；第三镜获ACCEPTED任务ID时累计图片调用仍为5次、文本16次，与接续前一致，证明这段尾帧未重画；原两个视频回执完整未变。已用20秒视频计入跨UTC日累计240秒提交预算。

## 已部署修复

- [PR #6](https://github.com/Q-1844/agent-system-v2/pull/6)，merge `029431812fa6f6141dd8099cc1dd04e5876b77fa`：匿名资产GET有界重试、原子写；图片优先内联，URL回退有独立恢复日志；失败FullRun接回原ProjectRun、SceneRun及已完成阶段；源Actions快照身份/SHA/路径/控制器/视频回执与文件核验后恢复，未知视频提交结果停止新提交。
- [PR #7](https://github.com/Q-1844/agent-system-v2/pull/7)，merge `a92d5ee86b31c8c1ef16a53bc5589750418f9c87`：RESTORED时清除旧terminal_status/error并保留失败历史；每个项目测试使用独立名称，避免旧控制器回调写到下一夹具。未修改原核心断言。
- [PR #8](https://github.com/Q-1844/agent-system-v2/pull/8)，merge `c3afe255bec6bccdb52aa8ad3e2bf98ab14db9c2`：已完成本地尾帧通过既有图床补公网URL，同步canonical候选与legacy槽；上传期间选择变化则CAS拒绝写回。仅可证明位于尾帧输入准备、且无提交意图/dispatch prompt/provider ID的失败视频工作可重试；取消、已受理及提交结果不明仍保持保护。

## 回归

| 最终源码 | 两轮GitHub完整回归 | 恢复专项 | Agent冒烟 |
| --- | --- | --- | --- |
| PR #6 `21fb513214caf5fb49df0d49c64076ab2df2bdef` | 3221通过/10跳过；3221通过/10跳过 | 372通过/10跳过 | 28通过 |
| PR #7 `2664fa0dd37e54950f625e21a0938ba423fc6114` | 3221通过/10跳过；3221通过/10跳过 | 372通过/10跳过 | 28通过 |
| PR #8 `d1dbc09faccedb51c8cd7fc708cfe752d3514948` | 3231通过/10跳过；3231通过/10跳过 | 382通过/10跳过 | 28通过 |


本机最终源码 `d1dbc09faccedb51c8cd7fc708cfe752d3514948`：3231通过、10跳过、0失败、0错误；针对尾帧发布/原子下载/绑定保护65项通过。回归使用Fake Provider；云端两轮均核对实际pytest日志；Linux FFmpeg校验、H264编码/probe/完整解码通过。较早本机并行运行共享测试目录造成的失败已作废，最终本机完整回归只运行一个进程，保留原断言。

## 已有成果与快照

两段原视频的实际视频流各10.125秒、H264、1260×720，含AAC；ffmpeg -xerror完整解码通过。

- `task_pkraULzuWocnwoTcMBlawZw0YxYohxo2` / vv_bf8c36681a10：3,841,027字节，SHA256 `2271cfc9a107f24a89c64aa785bf4b84c2275cf98ecf7ecd328747ebb221a7a4`。
- `task_zdzn0NXGfj2w4tWoxefFWauIpCqvSmwC` / vv_9db44576590e：3,059,330字节，SHA256 `8a202054ed5134f653ec182c953c67c05a3e03332ed7aeb797c7e116effc00d3`。
- 第三镜尾帧 lf_983a8fd6_1：1,218,394字节，SHA256 `d3e885eb2551c4593aaa6f76e0fd16d6b5f5901eb8d6518255db8db0cb8c8b19`。
- 来源40002008268：B draft Release 422455125 / asset 670987705，10,365,423字节，SHA256 `f88ea85661ad2433b267a04328ad9f2660bbac6f06dc0caebfcb023be6d72dac`；已重新下载核对。
- 来源40053946925：B draft Release 422470668 / asset 671058979，11,585,394字节，SHA256 `456617913ea97de27ab848834c8b367b9199d3d11335468d5157b269ab984a61`；已重新下载核对。

这些备份明确标识PARTIAL_NOT_ACCEPTED；不是最终VERIFIED_RESTORABLE。二次快照已离线恢复核对，两视频字节与原始完全一致，尾帧文件保留。

## GitHub定时运行

- [40015702924](https://github.com/Q-1844/agent-system-v2/actions/runs/40015702924)：2026-10-23T19:59:23Z，event=schedule，success。
- [40037377899](https://github.com/Q-1844/agent-system-v2/actions/runs/40037377899)：2026-10-23T23:02:58Z，event=schedule，success。
- [40050012987](https://github.com/Q-1844/agent-system-v2/actions/runs/40050012987)：2026-10-24T01:29:22Z，event=schedule，success。

三次均为默认分支、源码488ffa7fbc76499bee8037ae1078aa0d12de3b95的真实event=schedule，非手动dispatch。狭义单段视频云端基线补齐为4/4。实际触发间隔不规则，不承诺cron每20分钟准确执行；该结论不扩展为完整三分钟FullProject验收。

机器证据：[CODEX_MEDIA_RECOVERY_EVIDENCE_20261024.json](CODEX_MEDIA_RECOVERY_EVIDENCE_20261024.json)。用户授权已覆盖整顿、修复、合入及真实测试；Producer新能力、预览页与新任务来源继续后置。
