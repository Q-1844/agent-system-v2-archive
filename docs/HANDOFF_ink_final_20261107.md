# ink-diffusion 完成审核与最终恢复（进行中）

## 当前权威状态

任务 `ink-diffusion-20m-20261105` 尚未完成。原 run `42276180756` 停在 FAILED，137/145镜完成，1128请求秒数，原FullRun `frun_9b6951965f`及计划指纹不变。已付费137个视频全部可复用，零UNKNOWN/SUBMITTING；本轮尚未提交新的付费生产运行。

根因仍是D仓Pages部署600秒超时：视频和末帧字节已生成，但部署失败不会因反复GET自行重建，旧driver又把它当成普通FAILED，巡检无法接棒。

## 已完成的修复与验证

- A [PR #52](https://github.com/Q-1844/agent-system-v2/pull/52) 已合并 `ffda176ab547775f153b6e638d0345aad7998e50`：主动重建、独立基础设施等待账本、排水后INTERRUPTED/technical_wait自动接续。保留3次重试及20分钟终试，不改变冻结Asset结构及创作输入签名。
- 最终全量3929 passed、0 failed/skipped，492.885秒，含真实P55样本。
- 原始996155547字节artifact SHA256 `e5da8d5831d915a290af0d3debd02b797a38960f57add0d8ac5a0f3803fb8cef`已核验。完整离线故障循环跨两工作目录通过；137视频ID、版本、SHA256全保留，零生成请求。
- 本地管理PAT执行新恢复代码，84.84秒后原JPEG恢复200且字节一致；该验证不是生产FRAME_HOST_TOKEN权限证明。

## 生产密钥验证发现的新配置差异

[探针42328905145](https://github.com/Q-1844/agent-system-v2/actions/runs/42328905145)证实 FRAME_HOST_TOKEN 可读Pages设置和构建状态，但请求重建API返回403。因此不能只依赖本地PAT成功便声称生产自动恢复已验证。

后续 [PR #53](https://github.com/Q-1844/agent-system-v2/pull/53) 正在验证：只有确认legacy根目录发布分支、且重建API明确403时，使用同一密钥已有的Contents写权限提交一条可去重恢复标记，触发正常推送构建；不扩大权限、不借B1令牌、不覆盖图像。54项专项通过，最终全量进行中。带403的完整离线跨hop循环已通过，137视频哈希不变。

目前由Codex继续处理。通过使用生产密钥的零生成runner探针后，才从最新失败run `42276180756`恢复同一nonce，避免重复派发。新的run链接、最终成片、归档及注册表验收将补入本文。只有全部145镜完成、MP4全量解码、归档回读/restore full通过且B1/注册表COMPLETE，才能宣告本片完成。

## 生产密钥补充验证已通过

PR #53 已合并 `c4535b14d4d487ed6842d7b5197d1fa0dbb4bbba`。补充后全量 **3934 passed，0 failed/errors/skipped，473.418秒**。

更新探针 [42330221975](https://github.com/Q-1844/agent-system-v2/actions/runs/42330221975) SUCCESS，使用真实 FRAME_HOST_TOKEN 走Contents恢复提交路径。D仓commit `10b9432f400ac0af4d042f02eb36317a6ad88556` 只有一个新增恢复标记文件，零图片覆盖、零Agnes调用；已触发Pages构建。当前等待这次构建built，再提交原片最后8镜的接续。

## 续跑前最后的入口修复

生产令牌探针对应的D仓Pages运行42330239152已SUCCESS。另发现每次恢复和finalize_only仍发布随机canary，超时会改成巡检不接手的BLOCKED_PREFLIGHT。PR #54保留新任务新写入预检；恢复改用已存在的逐实际输入公开校验，finalize_only不写图床。119项关联通过，最终全量进行中。尚未派发付费续跑。
