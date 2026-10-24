# 长片 film3m-20261023-rescue5 本地独立验收通过（GLM 5.3，2026-10-24）

## 结论：CLOUD_PASS + 本地独立验收全部通过，>=180 秒真实成片达成

- 收尾运行 [40081890414](https://github.com/Q-1844/agent-system-v2/actions/runs/40081890414)（workflow_dispatch、源码 52519848、耗时 3.0 分钟、SUCCESS）：PR #10「无再生成收尾」按设计复用全部素材，未消耗新生成配额。
- B1 检查点：phase=COMPLETE，duration_s=202.861003，video_attempts 20/20 ACCEPTED，累计 200s/240s。

## 本地独立验收记录（GLM 5.3 于证据目录逐项核验）

1. final.mp4（Release asset 671782040，38.8MiB）下载 SHA256 = e6c3a743f2d6453b1930ad3dbbf21fc0b546a97b42271c7cd166e392970ea49f，与 B1 archive_ref.final_mp4_sha256 一致 ✅
2. ffprobe：h264 视频流 1280x720、4860 帧、202.861s；aac 音轨 202.901s；容器 202.901s；视频流与容器均 >=180s ✅
3. ffmpeg -v error -xerror 全解码：returncode 0、零错误输出 ✅（真实视频流+音轨，非封面/静帧/NaN）
4. project-40081890414.tar（asset 671834416，258,488,320B）下载 SHA256 = 24cbce1725001f51c60495082945f077ab3889b31bcf8c957d517d7ce1990574，与 B1 archive_ref.sha256 一致 ✅
5. tools.relstore.restore_campaign 空目录恢复：restorable_level=full、files_checked=140、hash_bad=[]、missing_required=[]、snapshot_fingerprint=6c1403dd… 与 B1 tree_fingerprint 一致、source_code_commit=52519848 ✅
6. composition manifest（prun_4ddff9a28f）：20 clips、20 唯一 video_version_id、20 唯一 shot_id、5 scene_run、合计 200.0s ✅
7. 恢复目录 20 个 mp4：20 个互异 SHA256、20/20 与清单版本 ID 一一对应、逐镜文件名↔shot_id 全部一致 ✅
8. B1 Registry：archive_status=VERIFIED_RESTORABLE、residency=RESIDENT、open_jobs=0 ✅

## 断点续跑链证据（同 nonce 五次接力，零素材损失）

- 原运行 40002008268 → 40053946925（快照恢复+复用 2 视频）→ 40055563112（150 分钟保险丝优雅切断，e2e-evidence 归档 12548693050 SHA256 校验通过）→ 40081890414（finalize-only 收尾）。
- 全程累计 200 秒视频预算无超支、无重复 POST；跨仓协调 A↔B1↔B 全链验证。

## 新能力确认（PR #10-#12，源码 52519848）

- 保险丝参数化：DRIVER_TIMEOUT_MINUTES（默认 330）+ WORKFLOW_TIMEOUT_MINUTES（默认 360），强制驱动比 workflow 早 >=30 分钟；workflow_dispatch 新增 driver_timeout_minutes / finalize_only 输入。
- 到点「有界排水」：deadline 触发后进入 PAUSING 相位排水收尾，不再硬切。
- 用户 2026-10-24 拍板：330/360 结构、AGNES_VIDEO_INFLIGHT=1、两层保险丝设计维持；Agnes 按日 500s 刷新，无累计预算限制。

## 状态

- 三分钟（>=180s）FullProject 真实验收：**已通过**。Producer 新能力与预览页按既定路线解锁排队。
- 自动续跑（保险丝触发后自动派发下一跳）尚未实现，仍需显式 resume；建议加入自动跳数上限（如 3 跳）后落地——待 Codex 复活后决策。
- GLM 5.3 值守本轮任务完成，证据留存于本地 evidence/film3m-40055563112/ 与 evidence/final_acceptance/。
