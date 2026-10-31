# HANDOFF: 按天接续（跨日 429 恢复）遗留问题清单 — 2026-10-31

> 交付对象：codex。本文档由 GLM 线（qingyan）整理，基于 r46（nonce `film6m-r46-20261030`，任务描述 6 分钟 / ~360s，35 镜 307s 已 ACCEPTED）七跳实测接力链的证据。
> 仓库坐标：A `Q-1844/agent-system-v2`（主代码）· B `Q-1844/agent-system-v2-rundata`（运行数据）· C `Q-1844/agent-system-v2-archive`（本仓，档案）· D `Q-1844/agnes-frame-host`（图床）· B1 `Q-1844/agent-system-v2-rundata-1`（检查点/索引层）。

## 一、背景：七跳接力链战况

r46 是「按天接续」能力的首次系统性实测（白天耗尽额度 → 次日额度刷新后接力收片）。当前状态：**35 镜 307s 素材零损失躺在恢复链上，差 ~53s 补拍 + 合成**。

| 跳 | 时间(北京) | 死因 | 定性 | 修复 |
|---|---|---|---|---|
| hop1-2 | 10-30 深夜 | 半重绑检查点身份闸拒绝 | 设计内牺牲跳 | PR #32（已合并） |
| hop3 | 06:01 | 读到 hop2 修复前旧检查点 | 牺牲跳（PR #32 修的就是它） | — |
| hop4 | 06:02 | `STAGE0_BOUND` 不在可恢复 phase 白名单 | Bug B | PR #33（已合并） |
| hop5 | 06:18 | artifact staging 嵌套埋深（每跳失败埋一层，顶层空壳无 project.json） | Bug C | PR #34（已合并） |
| hop6 | 10:08 | 身份/phase/素材三层全过、35镜307s 零损失恢复 → 4 秒死于昨日 429 错误原样重放（零新请求） | Bug D | PR #35（已合并） |
| hop7 | 10:30 | 同样死于 429 原样重放——PR #35 修复未生效 | Bug E | PR #36（已提交，CI 中） |

## 二、Bug E（PR #36 修的表层 + 遗留深层问题）

### 表层（已修）

PR #35 的重排判定要求 job 的 `provider_task_id` / `submission_intent_id` / `dispatch_prompt` 三字段全空。但 hop7 artifact（run 41160317704，163MB e2e-evidence）实证：429 拒收的 video job 里 **`submission_intent_id` / `dispatch_prompt` 是 handler 在 POST 之前登记的意图收据**，429 时并未兑现：

```
job 70dc5e158d36 (s04_c03, video, failed)
  error: 重试 5 次仍失败: 429: {...request id: 20261030054158...（前一日）}
  params.provider_task_id:     None      ← 供应商未受理、零扣费
  params.submission_intent_id: f2cb61f8… ← POST 前登记，未兑现
  params.dispatch_prompt:      "The 10 luminous circles…"  ← 同上
```

→ 意图字段被 paid 判定误当已付费证据 → `quota_rejected` 永远 False → 旧错误原样重放、4 秒判死。PR #36 已改为：**真付费证据 = `provider_task_id`**（受理后才有）；429 + 无任务号 → 允许重排。

### 深层遗留（交 codex 系统性解决）

1. **意图收据生命周期无人管理**。`submission_intent_id` 在 POST 前登记、429 拒收后成为「孤儿意图」——PR #36 重排时不静默清除（避免动账本状态），但这些未兑现条目会累积。需要审计：
   - 意图登记的写入点（`routers/shots.py` `_handler_video` 的 `_claim_submit` 链）与 B1 账本（`tools/relstore/` 对账逻辑）的对应关系；
   - 429 拒收路径上意图条目应回滚还是标记 `unredeemed`（参考修复③的 4xx 「回滚意图条目」先例，`routers/shots.py` `_is_material_fetch_rejection` 附近）；
   - resume 重排后同一 shot 的新提交会登记新 intent，旧 intent 与新 intent 的账务关系。

2. **「按天接续」链路上同类「陈旧状态未清理」问题可能不止这一处**。已知前科：PR #30 修过项目层场景状态的陈旧 429、PR #31/#35 修过 job 层。建议系统性排查 resume 路径上所有「恢复自持久化状态但携带过时事实」的点（错误串、attempts 计数、配额快照、检查点 phase）。

3. **attempts 熔断与 429 重放的关系未完全排除**。hop6/hop7 均显示错误串为持久化旧值（request id 是前一天的），但「重试 5 次仍失败」文本格式来自 `src/api/agnes_client.py` `_request`（365 行附近）。真实链路是「重排后 handler 立即撞 attempts=5 上限直接抛缓存错误」还是「根本没进 handler」，建议在修完 Bug E 后用一跳实测确认；若还有残余，查 `shot.video.attempts` 的 resume 清零逻辑。

## 三、实测验证状态（PR #36 合并后需做）

1. 合并 PR #36 → 派 hop8：`target_duration_seconds=auto` + `task_nonce=film6m-r46-20261030` + `resume_run_id=<hop7 run id 41160317704>` + `media_inflight=2`。
   - ⚠️ 派发参数三个都不能少：缺 nonce 会报 "no authoritative checkpoint"（run #53 实测）；缺 auto 会报 "nonce 已绑定 auto 模式任务"（run #54 实测）。
2. hop8 预期：过身份/phase/素材/429 四层闸，`s04_c03` 等镜头重排补拍（今天额度 500s 全新，只需 ~53s），然后合成收片。
3. 若 hop8 过了 429 层但死在更深位置（如 attempts 残余、B1 对账冲突），按 §二.3 继续。

## 四、按天接续终极验收（收片后）

r46 收片只是「手动接力」走通。完整按天接续闭环还需：
- 派一个 ≥10min 新任务，让它白天自然耗尽额度 → 验证额度闸门（`tools/quota_gate.py`）拒绝落账；
- 次日 09:00 video-patrol 巡检自动拉起（`tools/resume_dispatch.py` 的 hop 链）→ 不需人工派发地接力收片。
当前该闭环从未跑通过；今晨六跳修的就是这条链上的连环雷。

## 五、关键证据索引

- hop7 run：A 仓 Actions run 41160317704（run #55），artifact id 13026678246（163MB，含 `cache/jobs.json`：429 job 实测形态）。
- hop6 run：41158643535（run #52）。
- 错误串实样：`重试 5 次仍失败: 429: {"error":{"code":"","message":"已达到 API 用量上限，请在 **2026-10-31 00:00** 之后重试。 (request id: 20261030054158288898746xBCF0xVu)","type":"AgnesAI"}}`
- 修复链 PR：#32 成对重绑 / #33 phase 白名单 / #34 嵌套剥离 / #35 429 重排 / #36 意图≠已付费（全部在 A 仓 `chore/migration-readiness` 默认分支或待合并）。
