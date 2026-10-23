# GITHUB_RUNTIME_STATUS — 运行态与已知问题

- 日期：2026-10-23 ｜ C 仓 `agent-system-v2-archive` 分支 `feat/codex-handoff-20261023`

## 已部署工作流（A 仓 `Q-1844/agent-system-v2`，默认分支 `chore/migration-readiness`）

| 工作流 | 文件 | 触发 | 状态 |
|---|---|---|---|
| mock-regression | `.github/workflows/ci.yml` | push/PR/workflow_dispatch | active；conclusion=failure（**预存诚实红基线，见下**，非本轮回归） |
| video-autoproduction-e2e | `.github/workflows/video-autoproduction-e2e.yml` | workflow_dispatch | active；已验证 PASS (run 39961036358) |
| video-patrol | `.github/workflows/video-patrol.yml` | schedule `*/10 * * * *` + workflow_dispatch | active；逻辑 PASS (run 39962609983)；schedule 实触发未观察到 |

## 运行环境

- runner: `ubuntu-latest`（windows-latest 镜像无 ffmpeg 在 PATH；ubuntu 24.04 需 `apt install ffmpeg`，工作流已含该步）
- python 3.13 + `requirements-ci.txt`（fastapi/httpx/pydantic/pytest 等）
- 默认分支：A=`chore/migration-readiness`，B/B1/C=`main`

## 必需 Secrets（仅名称，已在 A 仓配置）

- `AGNES_API_KEY` — 真实 Agnes 生成
- `B1_ARCHIVE_TOKEN` — B/B1 fine-grained PAT（永久 Contents:write），A 工作流跨仓写 B Release + B1 state.json
- 不在仓库存任何密钥值；config.yaml 全 `${...}` 占位符

## 已知问题（Codex 接手处理）

1. **ci.yml mock-regression failure = 预存基线，非回归**
   - `157 failed, 2730 passed, 10 skipped, 228 errors`（run 39963298829 等）
   - 失败全在 `tests/test_video_multi_mode_34.py` 等（`review_candidates` 返回 'uncertain' 非 'pass'）
   - 这是 10-21 记录的"诚实红"基线（`2847/157F+228E` 待校准），与 relstore/E2E 工作无关
   - relstore 278 测试在 CI 全 PASS（归入 2730 passed）
   - Codex 校准该基线（非本轮职责）
2. **schedule 实触发未观察到** — video-patrol 的 cron 已配，GitHub 未在测试窗口 fire；Codex 观察一次即闭环 `GITHUB_BASELINE_OPERATIONAL=YES`
3. **cron `*/10` 演示用** — 改合理间隔或事件驱动（每 10 分钟跑一次浪费）
4. **任务源** — 当前 `tasks/pending/*.json` 手动提交；Codex 接真实源（issue/API/Registry 驱动）
5. **真生成模式** — 当前 t2v（无需图，最简）；可换 i2v（需公开图 URL，身份一致性更好）
6. **A 仓 git 历史** — 远端含 Contents-API 提交（ubuntu/ffmpeg/patrol 等），本地 `feat/relstore-integration-handoff` 分叉；Codex 如需 git 推送先 `fetch + reset --hard` 到远端 HEAD

## Codex 可直接继续优化的模块与优先级

1. 观察 video-patrol schedule 实触发（最后一环）
2. 校准 ci.yml 基线（预存诚实红）
3. cron 频率/事件驱动化
4. 真实任务源接线（替代手动 tasks/pending）
5. i2v 模式 + 公开图托管
6. git 历史对账
7. 视频质量/一致性优化（项目既有 backlog）

## 凭据交接

- `collab-rw` PAT（fine-grained, All-repos Contents/PR/Pages/Actions:write）由用户直接交付 Codex（不入仓、不入本文档）
- B/B1 PAT = `B1_ARCHIVE_TOKEN` secret（值在 `C:\Users\Public\Documents\g3b_token.txt`，已入 A 仓 secret，不入仓）
