> 最新状态：该片已完成，独立验收 719.711995 秒 / 90 镜 / 600 文件 full 恢复，注册表已回填 COMPLETE。下一轮已启动 20 分钟新片，见 [最新交接](HANDOFF_daycarry20m_20261102.md)。以下保留当时的历史接续记录。

# Codex 接续交接：第五道闸已放行并产生新回执

记录时间：UTC 2026-11-01 / 北京 2026-11-02。按 C issues #1/#2 的顺序修复：普通暂停排水 → 显式 UNKNOWN 授权 → 原任务真实接续。用户已明确接受可能重复扣费，优先验证按天接续。

## 当前生产（GLM 从这里接棒）

- 原 nonce：`daycarry12m-20261101`，原项目 `cloud3min_daycarry12m-20261101`，FullRun `frun_372385c158`。
- 冻结计划：90 镜、714 秒。继续原片，没有创建替代 nonce。
- 本次从 `41331753136` 派发的真实 run：**[41337749271](https://github.com/Q-1844/agent-system-v2/actions/runs/41337749271)**，source SHA `6696fda5ba736e34c906bbf6361a86ada4f04b30`。
- B1 截至 `2026-11-01T18:43:56Z`：phase `RUNNING`、status producing，**65 条 ACCEPTED、514 秒确认请求**。这是真实接口回执；不等于全部视频已下载或成片时长。
- 原 63 条确认回执 ID 及顺序逐项比对一致，原 498 秒保留。原 `s05_c03` 8 秒 SUBMITTING 改为带审计授权的 `RESUBMIT_AUTHORIZED`，provider_outcome 仍 UNKNOWN，8 秒可能成本仍占累计授权预算。
- 当前任务已保存 nonce/request 绑定的持久授权，后续 hop 不需每天再手工 true。默认 false 表示不新增授权，不会撤销该任务已有策略；其它任务仍默认 fail-loud。
- Codex 在记录此状态后停止监控，不等待整片生成，也没有执行超过 50 分钟的真实长片测试。

## 提交代码

- [A PR #44](https://github.com/Q-1844/agent-system-v2/pull/44)，合并 `6696fda5ba736e34c906bbf6361a86ada4f04b30`：普通 paused 也排水；停止仍运行的子级但不复活 paused FullRun；提供 workflow `confirm_uncertain_submissions`；原生 Job 意图归档/一次性重提；正向任务号优先回收；保留未知成本及版本风险标志；RESTORED 与对账结果一次 CAS 保存；恢复失败不污染原 owner/phase；修复 legacy STAGE0_BOUND 的巡检入口。
- [A PR #45](https://github.com/Q-1844/agent-system-v2/pull/45)，合并 `5e481e526e22b32c4439356c4908c560f72664c9`：有有效持久风险策略、完整未知意图身份的 FAILED/failed 任务允许巡检进入 stopped-snapshot 对账。缺授权/身份、有回执、取消、超 hop 上限仍拒绝。只影响后续巡检，不重启本次活跃 run。
- [详细设计、参数和验收顺序](https://github.com/Q-1844/agent-system-v2/blob/5e481e526e22b32c4439356c4908c560f72664c9/docs/HANDOFF_unknown_submission_continuation_20261101.md)。
- [原 63 镜 SHA256/版本/任务号基线](https://github.com/Q-1844/agent-system-v2/blob/6696fda5ba736e34c906bbf6361a86ada4f04b30/docs/evidence/daycarry12m-20261101-preserved-clips.json)。

## 测试证据

- PR #44 本地全量：**3790 passed，0 skipped，0 failed**，440.94 秒，Python 3.12，P55 fixture SHA256 已核验。首次全量在既有取消竞态测试处停滞后中断，该文件单跑 12 项通过，完整重跑全部通过；没有把中断的那轮当作通过。
- 新增 UNKNOWN 授权恢复测试 34 项；关联大回归 263 项通过。
- PR #45 的 8 项新增巡检矩阵及相关回归：**159 passed**。其 GitHub CI 可从 PR checks 查看，不把尚未完成的 CI 宣称通过。
- 原 399751950-byte hop5 artifact，SHA256 `4c12f13f1b334120423d864d101c03daba1d459b04f4bbff06c39ce3152bf4d7` 已核验。默认恢复在复制项目前拒绝；显式授权只作用于原 Job `6427f45421e3`。63 个视频 ID、版本和文件 SHA 全保留，源检查点未修改。
- 用原 artifact 的真实 SceneRun、JobQueue、handler 加 fake provider 做离线端到端重放：恰好一次 replacement POST，64 确认/506 秒 + 8 秒可能成本，63 原视频 SHA 保留，零付费调用。此结果与上面真实 run 的 65/514 秒分开记录。

## GLM 后续顺序

1. 先查看上面的活跃 run 和 B1 owner；活跃期间不要再派同任务。后续始终使用 B1 最新 github_run_id，不再固定从 41331753136 恢复。保持 nonce、auto 档位、冻结任务要求和 2 路视频策略。
2. 约每 30 分钟检查一次即可；无需连续盯守。每次需要人工连续真实验收时仍遵守 50 分钟上限。
3. 检查新增镜头真正 done/被选中、旧 63 镜文件 SHA 与版本不变。ACCEPTED 是供应商受理证据，不单独等于镜头完工。
4. 若再次用尽额度：应有 WAITING_QUOTA / quota_exhausted、有效 quota_resume_after、拒收意图终态、drain_complete=true；不能当天反复 POST，也不能把额度等待算内容失败。过闸后巡检从最新 artifact 续跑，同 nonce/FullRun，发起新有效请求。
5. GitHub cron 为 best-effort。过闸后没有新 owner 时，先手动 dispatch A 默认分支的 video-patrol.yml 并看派发理由；仍需手动 driver 兜底时传最新 resume_run_id + 原 nonce + auto。已有持久授权，无需每天再 true。
6. 新的 UNKNOWN 默认仍不能在活进程重发；本任务策略允许停机后巡检交给恢复对账，先核对 native intent/Job/镜头输入。已拿到任务号始终优先轮询原任务，不能为了继续就丢掉它。
7. 最终验收：全部镜头与选版、真实成片 ffprobe 时长及全解码、B/B1 registry/full-restorable 归档、旧片 SHA。历史 8 秒 UNKNOWN 可能成本不得计入真实成片时长。

已证实本次恢复会实际向前生产；尚未宣称连续多天、下一次 quota 自动唤醒和最终成片归档已通过，以上由 GLM 持续实测完成。
