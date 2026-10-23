# GITHUB_AUTONOMY_E2E_REPORT — 真实端到端证据

- 日期：2026-10-23 ｜ C 仓 `agent-system-v2-archive` 分支 `feat/codex-handoff-20261023`
- 全部为 GitHub 真实运行 + API 交叉核验，非 mock、非本地冒充

## A. 视频生成（VERIFIED）

**run 39961036358** `video-autoproduction-e2e` (event=workflow_dispatch, conclusion=success, ubuntu-24.04, 13:26:01–13:28:44Z ~2m43s)
- 真实 Agnes t2v：video_id `task_tHn3kY9MzSFbMXMx2qyTGgNfRoZI10wB`
- 产物 URL：`https://cos-platform-outputs.agnes-ai.cn/videos/agnes-video-2.5/task_tHn3kY9MzSFbMXMx2qyTGgNfRoZI10wB.mp4`
- 5.0s / 720P
- ffprobe：duration 5.184s，video_stream `h264,1280,720`，**playable=true**
- MP4 SHA256 `102b5a8acfbef74ab6d8a701c65d100397f83b184b1cdaec4eb76500d5b56523`，1,954,214 字节
- artifact `e2e-evidence`（id 12504372799，1.95MB）已上传（含 MP4 + summary.json 备份）

## B. 仓库协调（VERIFIED）

| 项 | 值 | 交叉核验 |
|---|---|---|
| B 仓 Release | tag `e2e-video/e2e-1792761961`，release_id `421876392`，draft | GET /releases 确认 |
| B asset | `video-e2e-1792761961.mp4`，asset_id `669214514`，size 1954214 | == MP4 原始字节 ✓ |
| B 资产完整性 | 重下载 SHA256 == 原值 `102b5a8a…` | verified_bytes=true ✓ |
| B1 Registry | 分支 `test/e2e-e2e-1792761961`，路径 `e2e/e2e-1792761961/state.json` | GET contents 确认 sha `2e196464f3f560a095f3ec505fb6adfde19b06dd`（1953B）✓ |
| B1 终态 | registry_revision=5，activity_seq=2，archive_status=VERIFIED_RESTORABLE，archive_ref 含 release_tag/asset_name/sha256/tree_fingerprint | 解码 state.json 含 `activity_seq:2, archive_queue:[e2e_e2e-1792761961]` ✓ |
| 项目 | project_id `e2e_e2e-1792761961` | — |

## C. 自主整理 / 巡检循环（VERIFIED 逻辑；schedule 触发待观察）

**run 39962609983** `video-patrol` (event=workflow_dispatch, conclusion=success, 13:36–13:39Z)
- patrol 扫 `tasks/pending/demo1.json` → B1 dedup 检查（state.json 不存在）→ 调 e2e 生产 → 成功
- 日志：`[patrol] demo1: pending + not produced -> run production...` → `[patrol] demo1: PRODUCED -> B1 test/e2e-demo1 rev=5 sha=045cb2e4...` → `produced=1 skipped=0 failed=0`
- B1 demo1 state.json 实存：sha `7e1ca53efe79afd37e7f2a9d262c575b97683edb` ✓
- dedup 机制：B1 state.json 存在性 → 已完成任务不会被重新生产（patrol 跳过）

## D. 真正的定时巡检（NOT YET OBSERVED）

- `video-patrol.yml` schedule `*/10 * * * *` 已部署 A 仓默认分支 `chore/migration-readiness`，workflow 注册 active
- 测试窗口 13:41–13:58Z 未观察到 event=schedule 的 run（GitHub schedule 抖动/跳过；新工作流首 fire 常延迟）
- workflow_dispatch 已证明 patrol 逻辑正确（C 节）；schedule 一旦由 GitHub 自己 fire 即补齐本项

## 最终裁定

| 环节 | 状态 |
|---|---|
| 真实视频生成 | ✅ VERIFIED (run 39961036358) |
| 跨仓保存 | ✅ VERIFIED (B Release sha 对账) |
| 状态整理 | ✅ VERIFIED (B1 Registry CAS rev5 VERIFIED_RESTORABLE) |
| 一次实际 schedule 巡检 | ⏳ NOT YET OBSERVED (configured + 逻辑 proven via workflow_dispatch；等 GitHub cron 自己 fire) |

**GITHUB_BASELINE_OPERATIONAL = 3/4 YES（schedule real-fire 待 Codex 观察一次即闭环）**。按用户裁定门槛，未观察到 schedule 实触发前不报全 YES。
