# CLAIM_EVIDENCE_MATRIX — 主张—证据表（复算不预判）

复算脚本：`06_analysis/p56_pack_analysis.py`；复算输出：`06_analysis/CLAIM_RECOMPUTATION.json`。
所有时间为 Unix epoch（本地时区 UTC+8），派生间隔在 JSONL/复算输出中标注 `derived_*` 或独立列，不与原始字段混写。单调时钟未使用（全部 wall clock epoch），跨重启不可相减的时刻未相减。

| # | 主张 | 原文来源 | 原始证据定位 | 复算方法 | 复算结果 | 是否支持 | 限制/替代解释 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 容量 1/2/3 真实生效与热重配 | PHASE56_B 报告 §2 | run 记录 concurrency_effect（04_runtime_evidence/run_record_*_INF*.json）；worker 池重建代码 02_source/src/core/job_queue.py `reconfigure_video_workers` | 读 run 记录 applied/workers/source 字段 | 三 run applied=True；INF1 source=config、INF2/INF3 source=run_reconfigure:2/3 | ✅ 支持 | "生效"指队列容量层面；峰值在途重叠为另证（timeline JSONL 区间并集，B 报告 §2 peak=1/2/3） |
| 2 | 单片墙钟无改善 | PHASE56_B 报告 §2 | 同上 run 记录 + jobs.json | 五镜齐=max(每镜首个 done.finished)-首提交（复算脚本） | 1184.2 / 1207.7 / 1159.1s（±4%） | ✅ 支持（负结果成立） | 样本 n=1/档位；方差大（净生成 ±50%），不能排除真差异被噪声淹没——B 报告已声明不宣称显著 |
| 3 | INF3 1159s 计时边界 | PHASE56_B 报告 §2 | timeline_P56_P1_B_INF3_run_13c423ece6.jsonl | 首提交=最早 video job created；第5镜齐=每镜首个 done 的 finished 最大值 | 1159.06s；边界=轮询精度（JobQueue 状态落盘粒度），非服务端完成时刻 | ✅ 支持（口径如实） | 完成时刻=轮询首次观察到，非精确服务端时间 |
| 4 | 三场 13 次拒绝及类别 | PHASE56_B 报告 §4 | jobs_p56_all.json（error 字段） | 按 error 关键词分类（speaker/dialogue→台词闸；boundary_frame_stale→basis；reference_media→哨兵） | INF1: 台词闸3+basis2+哨兵1+其它1；INF2: 台词闸6+basis1；INF3: 台词闸4+basis1（合计 19 次失败，其中台词/说话者闸 13 次） | ✅ 支持（13 次专指台词/说话者闸，口径=该子类） | "拒绝"=提交前 fail-closed（0 额度）；分类靠错误串关键词，非结构化错误码枚举 |
| 5 | c02 ~650s 延误与上游 ~224s 就绪语义 | PHASE56_B 报告 §1/框架提案 §1.1 | timeline INF3 + 复算 JSON claim5 | 延误=c02 首次提交 − c01 首个 done；就绪=c01 done（下载完成+指针更新，非"审核通过"） | INF3 延误=651.4s（报告写 ~650，复算 651.4）；c01 收货 epoch 见复算输出；INF1=381.4s、INF2=610.5s | ✅ 支持（数字精化 650→651.4） | "就绪"=下载完成+final_video 指针更新；「审核通过/可用于下游」是另一事件（终审在其后）——两者未混同；延误归因"LLM 忙于重试"为时间线推断（提交波次与失败回执时序吻合），非直接因果证明 |
| 6 | 净生成 176-243s 中位/357s 最长 | PHASE56_B 报告 §1.1 | jobs started/finished | done jobs 的 finished-started 中位/最大 | INF1 中位 175.8 / INF2 240.3 / INF3 179.3；最长 357（INF3） | ✅ 支持（数字精化 176→175.8 等） | 净生成含 provider 排队+下载；无法进一步拆分 provider 内部阶段 |
| 7 | 收尾 ~190s、终审 180-292s 是否重叠 | 框架提案 §1.1 | run steps（producer_turn/independent_final_review） | 复算 JSON claim7 | INF1 收尾 184s/终审 180s；INF3 收尾 193s/终审 292s；重叠=0s（终审在 producer_turn 结束后才开始——串行执行） | ✅ 支持 | 终审与装配在当前实现中串行——这本身是可优化点（与 v3 提案一致） |
| 8 | 六员慢 2.7 倍 | PHASE54 报告（01_reports/HISTORY_PHASE54_REPORT.md）；P55 A 报告 §1 | 历史报告数字（非本包原始账本） | **无法复算**——P54 原始计时账本不在本包（历史运行）；分子分母=B1 5.4h vs B2 1.74h（P54 报告 §1 口径） | 引用成立性=P54 报告自证；观察性数据（非对照实验） | ⚠️ 引用级支持 | 不同负荷/审核政策同时变化（P55 任务书 §1 已声明）；且 P56_C 实证 W09 模板无法消费冻结包——"慢 2.7 倍"的负荷可比性有限 |
| 9 | INF2 连续 3 次修复失败未变策略 | PHASE56_B 报告 §2 | run_record_INF2 repair.attempts + claim9 复算 | 对比三次 repair_attempt 的 job params 差异 | 三次均同参数确定性重掷（无 prompt/参考/策略字段差异）；复审三连 identity 硬错；still_hard 如实保留 | ✅ 支持 | "未变策略"指提交参数层；LLM 会话内是否有隐式策略思考无法从证据排除（但未落到任何工具调用） |
| 10 | 机制接线现状 | 框架提案 §3.4/P56 A 报告 §2 | 静态源码（02_source）+ run 记录 | 代码存在性+运行证据匹配（复算 JSON claim10） | 自动依赖派发=**未实现**（650s 延误即证据）；自动修复闭环=已接线（INF2 still_hard）；主控 fencing=已接线（verify fail-closed）；写入版本保护=部分（shot 级 OCC 有、Store 无 CAS）；未知提交=已接线（待核验暂停）；热重配=已接线 | ✅ 支持（逐项见复算输出） | 静态存在≠全路径真机验证——各机制的定向测试见 05_tests_existing，全量回归口径见 _REGRESSION_CONTEXT.md |

## 无法核验项（如实）

- P54 "慢 2.7 倍"：原始账本不在包内（#8）。
- 供应商内部阶段拆分（排队 vs 生成 vs 下载）：无服务端事件，只有本地观察区间（#6 限制）。
- 运行进程内实际 env（AGNES_VIDEO_INFLIGHT 等）：本 shell 未见该变量=取 config 默认（runtime_limits_snapshot.json 为进程真实额度/限流读数，env 白名单见 03_config_redacted/_env_whitelist.json，注明 shell 口径限制）。
