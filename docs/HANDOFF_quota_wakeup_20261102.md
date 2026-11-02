# 跨日接续实测更新：唤醒修复后已继续生产

## 当前结果（原始时间为 UTC）

- 片子仍是《星港修复店》：nonce `daycarry20m-20261102`，目标约 1200 秒，FullRun `frun_6dec578ae4`。没有新开替代影片。
- 原 run `41379443191` 正确停在 WAITING_QUOTA / quota_exhausted，保存 34 条 ACCEPTED、278 秒，drain_complete=true，无未决收据。闸门 `2026-11-02T16:10:00Z` 已开；检查时仍无新 owner，原因是最后一次 cron patrol 在 10:00Z、过闸后没有运行。
- 这属于此前唤醒链过度依赖 cron 的设计缺口。PAT 已配置，日志证实配额闸门和暂停判断正常；不是额度继续拒收或素材丢失。
- [PR #47](https://github.com/Q-1844/agent-system-v2/pull/47) 已合并 `edeae72352fc4b9ca0115efa5702206b78a62e46`，加入完成事件 + 非 billable 环境等待定时器；[PR #48](https://github.com/Q-1844/agent-system-v2/pull/48) 已合并 `957312a57b0f115ea8f044deb599ad486c50d85e`，修复跨 hop 继承的旧派发回执误触发去重。

## 实际验证链

1. 本次遗留生产 run 在新 observer 部署前已经结束，GitHub 不会重放旧 completed 事件。因此做了一次迁移 smoke 登记，**不把这次人工登记冒充原先已经全自动唤醒**。
2. 唤醒 run **[41498095882](https://github.com/Q-1844/agent-system-v2/actions/runs/41498095882)**：created=2026-11-02T18:10:51Z，resolve started=2026-11-02T18:10:55Z，wake started=2026-11-02T18:12:18Z，最终 success。1 分钟环境等待已实际观察并通过最小年龄检查。
3. wake job 只注入原生 `GITHUB_TOKEN` 和 B1_ARCHIVE_TOKEN，没有 Agnes/图床凭据；由 **github-actions[bot]** 自动派发原片续跑 **[41498341720](https://github.com/Q-1844/agent-system-v2/actions/runs/41498341720)**，source SHA `edeae72352fc4b9ca0115efa5702206b78a62e46`。不是 Codex 再手工直派 producer。
4. B1 经 RESTORED 后已 RUNNING，error=null。**截至 2026-11-02T18:23:33Z：38 条 ACCEPTED，确认请求秒数 311 秒；新增 4 条有效回执，其中 2 条新任务已轮询完成。** 受理/请求量不是最终成片时长。
5. 原 34 条财务回执逐项完全一致；原 artifact SHA 核验及离线恢复也复用了全部 34 个已完成视频，版本/文件 hash 基线已保存。云端完整新文件/最终成片验收仍需结束后取 artifact/归档检查，不能把当前 RUNNING 当作整片完成。

## 测试证据

- PR #47 本地全量 **3869 passed，0 skipped / failed，449.85 秒**，P55 fixture SHA 已核验；23 项既有弃用 warning。
- 初版相关回归 171 项通过；补齐假原生令牌环境下的测试隔离后 55 项通过。
- PR #48 新增 7 项来源/nonce 去重矩阵，含真实 timer + patrol 路径，相关回归 **178 passed**。该小补丁未冒充另一次全量 3876 通过。
- 控制器的失败/等待/去重/CAS 测试不调用媒体供应商，不重置镜头 attempts、付费记录、nonce 或预算。
- 原 artifact ID 13116077738，194540377 bytes，SHA256 `646f7168f3a0a32769a53d2ffd61e111932ab2100e7a69bd59c51a94407b5014`。本地恢复全部 34 段、278 秒，零付费测试调用。

## GLM 从这里接棒

- 当前 producer owner 是 **41498341720**。活跃期间不要重复派发；始终以 B1 最新 owner 为准。
- 已配置标准环境 `producer-quota-wakeup` wait_timer=20，以及 smoke 环境 wait_timer=1；都无人工 reviewer。后续标准流程的等待不占 runner 的 billable time，短控制任务本身仍正常执行。
- 观察下一次额度耗尽：应干净落 WAITING_QUOTA、有效 quota_resume_after、drain_complete=true。生产 workflow completed 事件应**自动登记**新 alarm，B1 quota_wakeup.state=ARMED，来源 run 为当时最新 owner。此项标准 20 分钟自动登记/整夜链路尚未等到下一次真实额度墙，由 GLM 继续验证。
- 关闭期间 alarm 每次经过环境等待后重新检查，重登记均回到标准 20 分钟环境；smoke 不能绕过供应商闸门。
- 过闸后 alarm 复用 patrol 的来源/liveness/宽限/去重检查，按同 nonce/auto/冻结并行策略派新 hop；原有镜头和回执保持，再看新增有效任务。新 owner 不得被上一跳继承的 auto_resume 回执误阻挡。
- 默认分支当前已含 PR #48。当前生产 run 仍运行 PR #47 的 source SHA；后续控制/恢复读取最新默认分支，同时仍严格核对源 artifact 的原 SHA，不能混写版本。
- GitHub 平台仍可能排队或失败；cron 保留为兜底，不承诺精确某一分钟。排查先看 alarm run、environment waiting/保护规则、quota_wakeup 票据及派发理由；不要只看以前的 cron。
- 正常约 30 分钟查看一次；每次人工连续真实验证仍不超过 50 分钟。Codex 已在新增请求和完成轮询得到确认后停止监控，不等待整部片。
- 最终仍验收所有镜头/选版、本地 SHA、成片真实时长/全解码、B/B1 full-restorable 归档和 registry/检查点 COMPLETE。

[实现及环境配置说明](https://github.com/Q-1844/agent-system-v2/blob/957312a57b0f115ea8f044deb599ad486c50d85e/docs/HANDOFF_quota_wakeup_20261102.md)
[原 34 段基线](https://github.com/Q-1844/agent-system-v2/blob/957312a57b0f115ea8f044deb599ad486c50d85e/docs/evidence/daycarry20m-20261102-hop1-baseline.json)
