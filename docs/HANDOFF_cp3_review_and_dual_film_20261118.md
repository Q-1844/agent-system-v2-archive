# HANDOFF CP-3 复核记录（Codex PR#58/#59 验收 + 双片调度）2026-11-18

## 复核结论（复核人：GLM-Agent，2026-11-18 01:30）

### PR#58（7fa237c）通过——两处真缺口被堵上
1. 接续时恢复的批三 job 复用会丢 content_policy_feedback 参数（幂等 q.retry 路径）——已修：重试前把本次真实反馈写回 job.params
2. BoundedRealClient.__getattr__ 会让修订调用 chat_completion 绕过文本预算账/finalize-only 闸——已修：显式 chat_completion 方法走 _reserve_text_call 持久扣账

### PR#59（883840f）通过——批三失败的死终点升级为 Producer 审核修复循环
- 批三改写仍被拒 → 升级 finding 进 Producer（source=provider_rejection，携带 job_id/full_run_id/供应商原文/实际送出提示词/回执）
- 遵守用户拍板原则：无固定禁词表、无预过滤；UNKNOWN/在途不算拒收（fail-loud 保持）；同 Job ID 重发原文冒充修复会被拒
- CI 三闸：7fa237c ✓ 883840f ✓（da13197 为中间稿，已修复于终稿）
- 顺手修了 ci.yml relstore 拉取（hash 校验直取，替代 contents API——正是 ea14fa0 curl 22 抖动根因）

## run 339 取证（anime750s-20261116a 为何停 81/97）
02:16:33 批1拒 → 02:16:47 批2拒 → 02:17:27 批3（带反馈+agent 改写后）仍拒 → 阶段死 → patrol 红警隔离 AWAITING_HUMAN（机制按设计工作）。改写后的提示词仍被拒属预期边界——正是 PR#59 升级路径的存在理由。

## 双片调度（01:25 北京）
- real720s-20261117T094444Z（Codex 派发）：run 342 在产 67 镜，健康
- anime750s-20261116a：我派 run 343 接续（resume 44001657223，已排队在 342 后）——s03_c09 将走 PR#59 新路径首验：批三败 → Producer 修复循环
- 额度账：今日 500s = real720s 剩余 ~184s + anime750s 剩余 ~128s，双片今日均可收
