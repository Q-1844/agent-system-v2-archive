# 回归证据口径（如实）
- `_p56_a_full_regression.log(.gz)`：Phase56 A 批收口时的全量回归（pytest tests/ -q，1176s），代码态=子仓 ec64827；结果 83 failed + 2507 passed + 207 errors。失败集合与 P55 基线对比=等价（4 个 autopilot 时序 flake 单独重跑全过；34 项预存环境 flake 族翻通过）。
- `_p55_full_regression_final.log(.gz)`：Phase55 收口全量回归（基线参照）。
- `.failures.txt`：FAILED/ERROR 行 + 摘要行提取（直接可读）。
- 本取证未重跑测试（任务书 §8 默认不重跑）；上表即既有真实输出。
- Phase55 报告测试计数与全量回归口径差异：P55 定向 41-42 项=定向子集；全量=含预存环境失败的完整套件——两口径并存，对比时以失败集合为准（非数量）。
