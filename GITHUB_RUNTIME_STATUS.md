# GitHub 运行态（2026-10-23，Codex 接手复核）

**部署状态：A 修复分支提交 `a929e75` 已发布；默认分支仍为 `061735c`，尚未合入。默认分支更新被自动审批拦截，待用户批准具体 PR。以下修复说明指待合入代码；线上 cron 当前仍是原有 `*/10`。**
A 默认分支为 `chore/migration-readiness`。本轮具体提交、逐项证据和验收结果见 [运行链修复报告](CODEX_RUNTIME_REVIEW_20261023.md)。

## 已核实的历史证据

- 真实单段生产：run [39961036358](https://github.com/Q-1844/agent-system-v2/actions/runs/39961036358)，`workflow_dispatch/success`。
- 巡检：run [39962609983](https://github.com/Q-1844/agent-system-v2/actions/runs/39962609983)，`workflow_dispatch/success`。
- 原 B 资产 `669214514` 已重新下载，1,954,214 字节，SHA256 `102b5a8acfbef74ab6d8a701c65d100397f83b184b1cdaec4eb76500d5b56523`。
- B1 demo1 权威状态已读回，为 `VERIFIED_RESTORABLE`。

这些证据证明单段 E2E 路径，不证明完整项目自动制作和素材生命周期已在云端完成。

审阅入口：[A 仓 PR #1](https://github.com/Q-1844/agent-system-v2/pull/1)。

## 本轮修复与测试

- 巡检按任务终态和归档引用去重；远端读错、失败、超时及坏回执使运行失败。
- E2E 在付费请求前保存 B1 CAS 检查点；已知 ID 接续；不明确提交停止自动重发。
- B 已保存、B1 未完成时支持基于同一资产和 operation_id 继续登记。
- 两条生产工作流共用并发组；巡检上传逐任务证据；使用稀疏检出。
- Vision 测试 Fake 增加 `max_tokens` 参数；API 测试用临时项目代替未入仓的本机项目。
- 新运行恢复 CI 与 Agent 冒烟在 [39973107428](https://github.com/Q-1844/agent-system-v2/actions/runs/39973107428) 已通过；完整回归单列，不用旧的 aggregate 数字替代本轮测量。

旧报告的 `157 failed, 2730 passed, 10 skipped, 228 errors` 是历史记录。Codex 已找到部分明确原因并修复测试夹具；当前回归与逐节点对比见本分支本轮报告，不能统一归因于 relstore，也不能把“历史已有”理解成“无需处理”。

## 定时触发

最近一次只读 API 查询：`event=schedule` 的 total_count=0。狭义单段基线仍为 3/4，真实定时触发尚未验证；触发缺失原因尚未确诊。

GitHub schedule 是 best-effort，只在默认分支运行。计划的错峰 cron 是 `7,27,47 * * * *`（UTC，每 20 分钟），实际部署内容以 A 默认分支工作流为准。修改 cron 不等于已观察到触发；手动 dispatch 不算 schedule 证据。

## 保留事项

完整 Director/Planner/多 SceneRun/合成的 GitHub 真实验收、真实任务源、进入/退出生命周期、预览页、跨仓素材管理及 Producer 新能力留待后续。现有任务队列仍是 `tasks/pending/*.json`。

本地分叉先 fetch 对账并保留修改，建议使用独立 worktree。不要无条件 reset --hard。凭据只从 Secrets 或当前授权会话提供，不依赖旧报告提及的本地 Windows 凭据文件路径。
