# ink-diffusion 原片最终续跑交接

## 结论与范围

本轮检查时，影片**没有完成**：原运行42276180756在最后一场s05_c17的末帧托管阶段FAILED，已有137/145个视频完成、1128请求秒数。不能把已有约19分钟可播放素材或RESTORED当作成片完成；当时尚无本片最终MP4和完整归档验收。

已修复实际断点，保留同一nonce、FullRun和冻结计划，启动[真实续跑42332397687](https://github.com/Q-1844/agent-system-v2/actions/runs/42332397687)。本轮不是“全程无人干预已经证明成功”，而是失败后的修复及恢复；最终成片验收仍待COMPLETE。

## 为什么连续多天仍发生故障

正常的每日额度等待与技术故障必须分开看。原续跑历史包含两次额度终态，也包含s03_c18末帧、s04_c26尾帧和s05_c17末帧发布故障。这些故障不能一律归因为额度。

本次原始日志证明D仓Pages deploy停在syncing_files直至600秒超时。图像字节已写入Contents并不代表Pages已经发布；反复GET也不能重启失败的部署。前一轮修复了假就绪，却没有闭合重建权限和失败后重新进入生产的路径。此前模拟测试还遗漏了管理PAT与真实FRAME_HOST_TOKEN的权限差异。

另发现每次恢复和finalize_only都发布随机校验图，它超时会把已有付费素材的任务改成巡检不接手的BLOCKED_PREFLIGHT。该无关依赖也已移除，实际视频输入的发布检查仍保留在付费提交前。

## 已合并源码

- [PR #52](https://github.com/Q-1844/agent-system-v2/pull/52)，`ffda176ab547775f153b6e638d0345aad7998e50`：识别失败部署并请求重建；独立按镜头/版本/本地文件SHA绑定的发布等待账本；安全排水后INTERRUPTED/technical_wait，允许原生续跳。保留GLM的3次重试和20分钟终试，不改冻结Asset结构或创作输入签名。
- [PR #53](https://github.com/Q-1844/agent-system-v2/pull/53)，`c4535b14d4d487ed6842d7b5197d1fa0dbb4bbba`：Pages重建API明确403时，用同一FRAME_HOST_TOKEN已有Contents写权限增加可去重恢复标记，触发正常推送部署。验证legacy、根目录及发布分支；不扩大权限，不借B1令牌，不覆盖图片。
- [PR #54](https://github.com/Q-1844/agent-system-v2/pull/54)，`5931c62c57e945ab3d51d8e8c0575aba6e993804`：新任务仍须全新写入并发布校验图；恢复改用已有逐实际输入发布保护；finalize_only不发布新图。

## 测试和原始证据

最终全量**3939 passed，0 failed/errors/skipped，475.17秒**，包含真实P55归档样本。Linux runtime-regression和pipeline-smoke通过；Windows mock-regression最后一次检查仍在运行，未据此宣称远端全绿。

原始artifact：996155547字节，SHA256 `e5da8d5831d915a290af0d3debd02b797a38960f57add0d8ac5a0f3803fb8cef`。137个旧视频全部独立ffprobe及完整解码通过，实际视频时长合计1147.708343秒；这是源素材总时长，不是最终影片时长。

跨两个工作目录的完整离线故障循环已通过：原生末帧4轮失败→独立等待账本→实际排水→自动接棒资格→快照恢复→原生末帧完成。包括Pages重建API403的模拟，137个任务号、版本、SHA256全部保持不变，零生成调用。[137镜基线](evidence/ink-137-preserved-clips-20261107.json)已保存。

真实生产令牌探针[42330221975](https://github.com/Q-1844/agent-system-v2/actions/runs/42330221975) SUCCESS，使用FRAME_HOST_TOKEN走Contents恢复路径，零Agnes调用；D仓commit `10b9432f400ac0af4d042f02eb36317a6ad88556`只有一个新增标记，无图片改动。对应[Pages部署42330239152](https://github.com/Q-1844/agnes-frame-host/actions/runs/42330239152)也已SUCCESS。这弥补了仅用管理PAT验证的不足。

## 原片当前接续与参数

- nonce：`ink-diffusion-20m-20261105`
- 项目：`cloud3min_ink-diffusion-20m-20261105`
- FullRun：`frun_9b6951965f`
- ProjectRun：`prun_1ec9b9ecb4`
- 计划指纹：`88ccdffb831b7437a37add75e7c05b95b5757a7e97d5c8303c705a57f199da20`
- 本跳owner：`42332397687`；源artifact run：`42276180756`
- target：`auto`；media_inflight：`2`；driver_timeout_minutes：`40`；本nonce既有UNKNOWN风险授权延续。

本跳已RESTORED→RUNNING，error=null，旧pause_reason与额度闸门清除。原137条完整回执逐字段一致；新增s05_c18已获得供应商任务号。最新可复核状态见[真实恢复证据](evidence/ink-final-resume-20261107.json)和B1权威检查点。ACCEPTED只是受理，不得算为下载完成的视频。

B1：仓`agent-system-v2-rundata-1`，分支`test/e2e-ink-diffusion-20m-20261105`，文件`e2e/ink-diffusion-20m-20261105/full-project-production.json`。

## 最终验收顺序

1. 先读B1当前owner；若该owner仍active，不要重复派发或从旧run恢复。每次接续必须使用最新owner artifact和同一nonce，保留auto档。
2. 完成标志须同时满足B1 COMPLETE、145个选定视频、无SUBMITTING/UNKNOWN，以及原137任务号/版本/SHA不变。检查全部供应商任务号及源文件哈希无重复。
3. 按B1 `saved.archive_ref`独立回读最终MP4及项目tar，校验SHA256，ffprobe实际时长并全量解码MP4；不能以1192秒计划或请求秒数代替最终时长。
4. tar完整恢复必须full、missing_required为空；检查合成manifest逐镜顺序及版本；注册表production_status必须COMPLETE且archive_ref与B1一致。
5. 如果再次遇到发布等待，应干净保存INTERRUPTED/technical_wait并自动接棒；只有正常额度耗尽才WAITING_QUOTA。不要删除意图或重拍已有视频，不要把技术等待改为剧情修订。

本轮未另开影片。达到上述最终验收前，不宣告“整部影片接续完全成功”。
