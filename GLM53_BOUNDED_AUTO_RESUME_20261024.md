# 有界自动续跑落地与实弹验证（GLM 5.3，2026-10-24）

## 结论：A+B 双机制已合并默认分支，B 巡检实弹验证通过

- **PR #13**（cb7835cf）：A=排水后自派发（RESUME_DISPATCH_TOKEN PAT，GITHUB_TOKEN 被平台禁止触发新运行）；B=video-patrol 死链清扫；MAX_AUTO_HOPS=3 超限置 AWAITING_HUMAN；13 项单测；CI 三项全绿。
- **PR #14**（0b9f6cd4）：修复 sweep 检查点形态解析——read_checkpoint 返回文件本体而 sweep 误找 doc 包装层，相位恒 None（安全上歪打正着无事故，但真实死链会被漏掉）。修复+回归测试 14 项；CI 三项全绿。

## 实弹验证（零配额）

- 巡检 run 40090934291（修复前）：5 nonce 全跳过但 reason 均为 phase None → 暴露解析 bug。
- 巡检 run 40091648358（修复后，sha 0b9f6cd4）：rescue1=STARTING(pre-flight 留人工)、rescue4=FAILED not auto-resumable(凭据问题留人工)、rescue5=COMPLETE(不重做)、demo1/1792761961 无检查点——**逐 nonce 真实相位判定，零误派发**。
- 派发链路所需 secret RESUME_DISPATCH_TOKEN 已由用户配置（无期限 PAT，仅本仓 Actions 读写）。

## 待验证（需要消耗真配额）

- A 机制（排水后自派发下一跳）：下一部真实新片用短保险丝（driver_timeout_minutes=30）实弹验证自动接力；预计总时长约 2.5h（两跳）。用户批准后执行。

## 运维备注

- 视频生产 timeout-minutes: 360 / DRIVER_TIMEOUT_MINUTES 默认 330 / 强制 30 分钟缓冲已由 PR #10 参数化（本值守 10-24 验证通过 40081890414）。
- 用户口径：Agnes 按日 500s 刷新无累计预算；一次一片；A1 并行搁置；两层保险丝与 INFLIGHT=1 维持。
