> 本文保留上一批次历史记录。最新修复、测试与真实运行状态见 [CODEX_RUNTIME_BOOTSTRAP_LOCK_FIX_20261023.md](CODEX_RUNTIME_BOOTSTRAP_LOCK_FIX_20261023.md)。

# 图床写权限预检修复与凭据复核（2026-10-23）

**部署更新：PR #1、#2、#3均已合入默认分支`chore/migration-readiness`，当前合并提交`94401281a5fca3802234aefb7efc70c7e8c66432`。源码`50f7c49`的两轮完整CI均成功。用户已创建FRAME_HOST_TOKEN Secret，该次运行39994958081随后在FFmpeg安装退出124，未进入媒体步骤；最新运行见PR #4报告。**

PR #3：https://github.com/Q-1844/agent-system-v2/pull/3 。源码提交50f7c49777af49ac6557dce68b62dc85fa682ded；两项修改文件已与远端Git blob逐字节匹配。

## 修复的问题

旧预检上传固定8×8校准图。图床按文件哈希命名，旧图已存在时会GET命中并跳过PUT。公开图片可读不能证明当前凭据可写；这样可能在实际媒体生成后才遇到403。

现在每次校准PNG加入独立的随机元数据，像素和尺寸不变，文件字节与内容地址必定更新。仍走正常GithubPagesHost.upload及Pages就绪检查，预检会实际执行PUT。403仍在任何Agnes生图/视频生成之前停止。

## 已验证

- 本机存储、恢复、长片保护与图床组合：353 passed、10 skipped，零失败和错误。两个新增用例分别覆盖旧地址不能复用，以及旧公开校准图不能隐藏只读凭据403。
- 两轮最终云端CI全部success：39993439024, 39993425034。
- 真实SDK路径：使用本次用户提供的collab-rw，执行新的校准图生成→GithubPagesHost.upload→公网下载→字节对账；公开GET为200，139字节，SHA256为35f69d04d87c1a863e36872736dcf449ac6cca7a620b0d680e78088c2651a98f，原字节一致。
- 上述图床冒烟测试未调用Agnes图片或视频生成。长片测试的生成状态以独立运行记录为准。

| 范围 | PR CI | Push CI |
| --- | --- | --- |
| 完整Mock回归 | 3189通过，10跳过 | 3189通过，10跳过 |
| 存储/恢复专项 | 342通过，10跳过 | 342通过，10跳过 |
| Agent冒烟 | 28通过，0跳过 | 28通过，0跳过 |


## 凭据已由用户保存，新运行已启动

当前会话collab-rw直接写入D仓已返回201，校准图公网下载也为200，证明该token可用作FRAME_HOST_TOKEN。上次Actions预检的403不能据此归因到这枚会话token；当时工作流还可能使用B1归档凭据作为回退。

同一凭据访问A仓Secrets public-key与list接口仍403，响应明确要求secrets=read。Contents/Actions写权限与Secrets管理独立，当前没有新增或修改任何Secret。

随后用户已创建新的token并保存到A仓Repository Secret FRAME_HOST_TOKEN，无需再提供该值，也无需再要求用户配置同一项。Secret值未向Codex暴露，新的runner直接从GitHub Secrets读取。

旧核验39994174900的媒体步骤最终skipped，没有执行Agnes生成。新的运行[39994958081](https://github.com/Q-1844/agent-system-v2/actions/runs/39994958081)已从默认分支启动，nonce为film3m-20261023-rescue3。截至2026-10-23T17:31:28.378050+00:00当前阶段：['Install ffmpeg']。

最终视频流至少180秒及完整跨仓归档恢复仍须实测，不把校准图成功、workflow进行中或Mock CI算作长片成功。实际预计时长按生产阶段与服务端排队更新；job最长180分钟。

## 证据与官方依据

- 机器回执：[CODEX_FRAME_HOST_PREFLIGHT_TEST_EVIDENCE_20261023.json](CODEX_FRAME_HOST_PREFLIGHT_TEST_EVIDENCE_20261023.json)
- 初次权限实测：[CODEX_TOKEN_PERMISSION_CHECK_20261023.json](CODEX_TOKEN_PERMISSION_CHECK_20261023.json)
- GitHub Contents权限：https://docs.github.com/en/rest/repos/contents
- GitHub Actions Secrets权限：https://docs.github.com/en/rest/actions/secrets
