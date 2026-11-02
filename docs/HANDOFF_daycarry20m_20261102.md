> 最新接续结果：过闸后原 cron 未触发的唤醒缺口已修复。新 alarm 自动派发续跑 41498341720，已增至 38 条 ACCEPTED / 311 秒请求量，原 34 条回执保留。详见 [最新唤醒实测交接](HANDOFF_quota_wakeup_20261102.md)。以下保留上一轮启动及成片验收记录。

# 旧片完成验收 + 新片按天接续测试交接

## 当前结论

旧片 `daycarry12m-20261101` **已正常成片并完整归档**。本轮独立下载并核验真实文件，不仅依据 Actions success 判断。新片已提交并启动；Codex 在下述启动检查后停止监控，不等待长片生产。

## 旧片验收及状态修复

- 制作 run：[41337749271](https://github.com/Q-1844/agent-system-v2/actions/runs/41337749271)，B1 COMPLETE，source SHA `6696fda5ba736e34c906bbf6361a86ada4f04b30`。
- 成片：视频实测 **719.711995 秒**，容器 719.733333 秒，H.264/1280×720，含音频。独立 ffmpeg 全量解码通过，抽样画面正常；不宣称抽样等于完整艺术质量评审。
- 90 镜全部有 done 版本且选中，6 个场景及 FullRun/ProjectRun 完成。原 63 镜的任务号、版本、本地 SHA 逐项与基线相同，仍在成片选版中。
- 90 条真实 ACCEPTED 对应请求 714 秒；历史 UNKNOWN 仍记 8 秒可能成本，不计作有效回执或成片时长。
- Release 430826907，final.mp4 138961755 bytes，SHA256 `909f9a9fcc7c17b29dad8da996537aa028e804fdaa394967310ff46c0b53178f`；project.tar 967536640 bytes，SHA256 `4c7f37ff7f0ef84eb3ef0e549fd9a8096fcd49b6b15c4e2267b07b999d6e8057`。
- project.tar 独立安全恢复 **600 个文件，full**，hash_bad / missing / missing_required 均空；包内成片与独立下载的成片 SHA 一致。
- 发现 registry.production_status 漏记、仍 IN_PROGRESS。本轮新增 guarded 完成事件后，通过纯元数据维护 [run 41379184135](https://github.com/Q-1844/agent-system-v2/actions/runs/41379184135) 成功回填。已读回 B1 确认 **检查点和注册表都 COMPLETE**，原 video_attempts、owner、archive_ref 均未变，没有重拍或再上传素材。

## 修复代码与测试

[A PR #46](https://github.com/Q-1844/agent-system-v2/pull/46) 已合并：`0aaca50b10b6da4fae4adb5802c2a4997cb24cf9`。

1. driver 完成 QA 和 full 归档恢复验证后，显式写 registry COMPLETE；仅同一已验证归档、原 revision/activity、无在途或同步意图的项目可完成。回填 CLI 两次 CAS 中间中断可幂等重跑，拒绝覆盖新活动，不改变旧片资源。
2. 旧完成 run 的 Actions artifact 实际 **3856636565 bytes**，重复包含打包、重下载和恢复验证副本。新上传排除这些大文件/验证树，保留 projects/cache 和 JSON 留证。生产恢复改为流式下载/解包，并核对长度和 SHA；磁盘界限为 ZIP 8 GiB、展开 16 GiB，保留路径安全和对账纪律。避免 20 分钟片后续 hop 因旧 1 GiB/2 GiB 限制或整包内存读取而失败。
3. 新任务 `confirm_uncertain_submissions=true` 原先未被创建路径消费。本轮在媒体 workers 启动前保存 nonce/request 绑定的未来风险授权。默认仍禁止，真正的 UNKNOWN 重提仍须停止源 run 后逐笔核对 native Job/意图/镜头输入。

本地全量 **3837 passed / 0 skipped / 0 failed**，439.75 秒，23 项既有弃用 warning；P55 fixture SHA 已核验。新增 39 项用例覆盖真实打包/恢复/完成事件、CAS 竞争/回执丢失/两写中断、旧回执不变、新活动保护、fresh policy、流式网络和解包、大小/长度/SHA/展开边界。另 262 项关联回归通过。GitHub CI 如尚在运行，不冒充已通过。

[代码内完整报告与验收方法](https://github.com/Q-1844/agent-system-v2/blob/0aaca50b10b6da4fae4adb5802c2a4997cb24cf9/docs/HANDOFF_completed_film_and_next_day_test_20261102.md)

## 新片：从这里继续

- 片名：《星港修复店》，新故事、新 nonce，Producer 自主安排情节、镜头及专家协作。
- nonce：**`daycarry20m-20261102`**。
- 当前 run：**[41379443191](https://github.com/Q-1844/agent-system-v2/actions/runs/41379443191)**，source SHA `0aaca50b10b6da4fae4adb5802c2a4997cb24cf9`。
- FullRun：`frun_6dec578ae4`。
- 启动检查截至 `2026-11-02T02:49:17Z`：B1 **RUNNING，error=null**，原生 FullRun preparing / director_plan / s03。此处仅确认启动与规划推进，不宣称新视频、额度暂停或新一轮跨日恢复已经通过。
- Stage0 **FROZEN**：5 个场景，预算 target_s 合计 **1200 秒**，显著超过 500 秒；approximate 时长目标，保留创作自由。
- request SHA256：`d80a5d2b2af43d64244ecaa797dde31448e417e51af9c6c9052146fd7db282d7`。
- plan fingerprint：`694ac1f43cc9b81f9abea36c4bdd208fb33807a34127517093993baf83b18096`。
- 风险 policy 已真实落账：policy_id `2b86cc62bb6dbdfb2c186d8877eccfedc84cfef8949d030d577704d0eced5d0f`，authorized_run_id=41379443191，actor=Q-1844，accept_duplicate_charge=true。之后同 nonce 的 hop 继承；不需每天人工放行。
- dispatch：auto，media_inflight=2，driver_timeout_minutes=330，confirm_uncertain_submissions=true，finalize_only=false。新建任务时 resume_run_id 留空；往后续跑务必以 B1 最新 owner 为准。

## GLM 今晚及后续检查顺序

1. 活跃 run 不要重复派发。约每 30 分钟看一次即可，任何单次连续人工真实验证仍不超过 50 分钟。
2. 额度耗尽应落 WAITING_QUOTA / quota_exhausted、有效 quota_resume_after、drain_complete=true；拒收意图终结，已受理任务及视频保存。不能当天反复 POST，不能把额度等待记为剧情/质量失败。
3. **以供应商回执和 B1 quota_resume_after 判断何时过闸，不按客户端“零点”猜测。** GitHub cron 为 best-effort。过闸后观察巡检自动派发同 nonce 的最新 artifact 接续；新 owner/source 对应新 run，已完成视频 ID、选版和 SHA 保留，并发起新有效请求。
4. 若无人触发，先查 patrol 派发理由；按之前 C 的顺序手动 dispatch video-patrol，再考虑最新 resume_run_id + 本 nonce + auto 兜底。手动救援只能证明恢复能力，不能算全自动唤醒通过。
5. 后续 UNKNOWN 有本任务的持久授权，可交巡检在源 run 停止后恢复对账；原生任务号存在时优先轮询原任务。不得在活进程直接重发，也不得把旧未知成本当成镜头素材。
6. 用 watcher 收集较大 artifact 时显式设置 `--max-download-mib 8192`，其默认审计下载上限仍为 1 GiB；不要把 watcher 自己的限额误判为生产恢复失败。
7. 最后核验：全镜头 done/选版、全量视频解码与真实时长、旧片 SHA、B/B1 full-restorable 归档、registry COMPLETE 与 checkpoint COMPLETE。RESTORED、ACCEPTED 或 Actions success 单独都不等于全链完成。

本轮没有新建等待整夜的 Codex 监控，也没有亲自运行超过 50 分钟的真实长片测试。新片正在云端执行，后续额度刷新与无人值守接续由 GLM 持续实测。
