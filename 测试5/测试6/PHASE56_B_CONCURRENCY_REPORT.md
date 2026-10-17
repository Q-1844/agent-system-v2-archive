# PHASE56 B 单项目内并发主试验——报告

日期：2026-10-18。任务书：`测试5/测试6/PHASE56_02_CONCURRENCY_BENCHMARK.md`。
被测项目：P1《断电前的证词》批准工作包（冻结清单 `projects/P56_P1_TESTIMONY/output/agents/P56_freeze_manifest.json` sha1=eb6c58ea0bcf+config 修订 2 条；一景五镜，每镜 8s，硬依赖 1→2[multi+prev_tail_look_scene 三参考]，其余独立）。

## 0. 结论摘要（分节判定）

- **机制**：档位→队列容量真实生效。三档 run 的 `concurrency_effect` 全部 `applied=True`（INF1=1/config、INF2=2/run_reconfigure、INF3=3/run_reconfigure——**结算后热重配实证工作**）；峰值在途=1/2/3 各自达成（时间线并集实测）。
- **效率**：**单片墙钟未观察到稳定改善**。5 镜齐耗时 INF1=1184s / INF2=1208s / INF3=1159s（±4%，在单视频生成时长方差与重试噪声内）。并发无收益=有效结果（02 文件口径），不宣称提速。
- **自主性**：三 run 全程经正常产品入口（REST collab-runs，combo v2 实验默认）由 Producer 自主完成；无执行侧补交/代写 canonical；INF2 的 c02 三修后仍硬错→如实保留 `still_hard`（不冒充通过）。

## 1. 试验版本演进（02 文件：版本批次纪律）

| 版本 | 内容 | 处置 |
| --- | --- | --- |
| v1.0（审查政策 v1） | P55 静帧硬维套视频三帧位 | **发现样本**：run_fba9de2066 完整保留（104s 消耗）。结构性误报实证：中帧动作位移→missing_character；景别边界→shot_size 硬错→c02/c03 各 3 修全败（重掷引入新错误）。 |
| v2.0（审查政策 v2） | video_review_v2（硬维仅状态帧+景别构图降次维） | 发现样本：INF1/INF2 各完成（peak 仍=1——**逐镜串行提交**使容量闲置）。 |
| **v2.1（正式对照）** | 目标模板批量提交指令（就绪镜一次 shot.generate_videos 多目标+依赖镜单独提交） | **正式 B 轮**：INF1/2/3 三 run，同冻结包同政策仅改在途上限。 |

每次版本变更=独立提交（f4f15b0 审查 v2 / 5efd5ed 目标 v2.1 / f7cd706 租约修复）；旧轮保留不与新版混算。

## 2. 正式对照（v2.1）逐档结果

| 项 | INF1（inflight=1） | INF2（inflight=2） | INF3（inflight=3） |
| --- | --- | --- | --- |
| run_id | run_3946440d29 | run_bbf65ad1af | run_13c423ece6 |
| 终态 | completed | completed | completed |
| concurrency_effect | applied=1（config 来源） | applied=2（run_reconfigure） | applied=3（run_reconfigure） |
| **峰值在途（并集实测）** | **1** | **2** | **3** |
| producer_turn 历时 | 1402s | 2242s | 1380s |
| 5 镜齐（首提交→第5镜收货） | 1184s | 1208s | **1159s** |
| video jobs（done/failed） | 5/7 | 12/7 | 5/5 |
| 修复 | 无 | c02×3 全硬错→still_hard 如实 | 无 |
| 独立终审（v2 政策） | 零硬错 | c02/c04 硬错→修复轮 | 零硬错 |
| 成片 | sequence 已渲染 | sequence 已渲染（40.0s，Δ21ms） | sequence 已渲染 |

原始证据：`_tmp/p56_b_evidence_P56_P1_B_{INF1_run_3946440d29,INF2_run_bbf65ad1af,INF3_run_13c423ece6}.json`（run 快照/步骤账本/并发效果/媒体 job 全时间线/审核/修复）。观察区间说明：无服务端完成事件，完成时刻=轮询首次收货时刻（秒级轮询，区间精度 ±1 轮询周期）。

## 3. 三件必须证实的事（02 文件逐条）

1. **档位真实作用于执行队列** ✅：三档 concurrency_effect applied=True+覆盖来源落 run；INF1 的 queued 任务在容量 1 下排队（running=1+queued=2 观测）；热重配在结算后应用（INF2/INF3 的 source=run_reconfigure）。
2. **独立任务真实重叠+依赖未破坏** ✅/◐：峰值在途 1/2/3 实证（1→2 依赖镜在其上游收货后才提交——v2.1 目标明确指令+契约闸兜底）；但 INF2 内重叠收益被 c02 重试与修复抵消。
3. **同等负荷下等待/人工推动改善** ✗（本轮）：5 镜齐三档差异 ±4%（1184/1208/1159s），不构成稳定改善。归因：①负荷结构=4 独立+1 依赖，容量 1 已可流水；②单视频生成时长方差大（同包同配置 90-250s 波动）；③对白标记闸 fail-closed 重试（派发前失败零额度但耗时）在三臂随机分布；④INF2 的 c02（multi+三参考接力镜）真身份硬错触发修复轮。**人工推动=0**（全部机器路径；无救援）。

## 4. 过程发现（全部已落档/修复）

| 发现 | 处置 |
| --- | --- |
| producer_turn 租约拒绝路径 UnboundLocalError（死分支 import models 不存在的 AgentError） | 修复+回归测试（f7cd706）；B1 首跑实证 |
| 克隆脚本 video 字典多余键炸 canonical（producer 诚实 blocker 零伪造=纪律正确） | 修复（abe3725） |
| P55 静帧硬维套视频三帧位=结构性误报→never-win 修复烧额度 | **审查政策 v2**（f4f15b0）+v1 样本完整保留 |
| producer 逐镜串行提交使 in-flight 上限形同虚设（v2.0 peak=1@容量2） | **目标模板 v2.1 批量提交**（5efd5ed） |
| 台词字段含"本镜无对白…"说明文字+括号说话者修饰→闸门 fail-closed 重试 | 未修（三臂共享常量不偏倚对照）；P2/P3 包将以干净格式构建 |
| multi+prev_tail_look_scene 三参考镜（c02）身份硬错率高（INF2 三修全败） | 如实保留 still_hard；C 批跨剧情观察是否复现 |

## 5. 额度与消耗

- 今日视频：368/500s（B 全部轮次累计；v1 发现样本 104 + v2.0 发现 80 + v2.1 正式 184）。图片 55/4000、文本正常。
- 计费口径=提交源时长；派发前 fail-closed（语言/台词/绑定闸）零额度。
- 冻结源修订 2 条（config_amendments 在清单）：native_av.spoken_language 补全；冻结清单本身 sha1 记录。

## 6. 候选档位建议（探索性，交 C 批跨剧情观察）

- **候选：inflight=3**（5 镜齐最快 1159s+零修复+峰值满载），但差异在噪声内——**不宣称长期最优**。
- INF2 的 c02 修复消耗提示：含 multi 接力镜的负荷对高并发档的收益更敏感（修复串行段拖长总历时）。
- 依赖链的收益边界：1→2 链使链尾镜必然串行；纯独立镜负荷（P3 类）才可能展现接近容量比的改善——待 C/D 跨剧情验证。

## 7. 与任务书的偏差（如实）

- 第二轮（3→2→1 复验）未做：当日额度 368/500 已不足以完成 P2/P3 核心样本+复验（132s 剩余 vs 复验 120s+P2 96s+P3 40s）。**B 首轮部分完成，不把一轮写成复验通过**；复验排下一额度日。
- 台词格式噪声未修（保持三臂同条件）；P2/P3 包构建时以干净格式。
- c04 复审一次 not_reviewed（复审调用异常→按非硬错停止）：fail-open 语义，已在证据中如实标注。
