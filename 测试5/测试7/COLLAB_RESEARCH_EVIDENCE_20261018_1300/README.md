# COLLAB_RESEARCH_EVIDENCE_20261018_1300 — 协作架构深度研究取证包

取证时刻：2026-10-18 13:0x +0800。只读取证——未修改任何业务源码/canonical/配置，未调用模型接口，未重启服务，未重跑测试。
仓库版本：父仓 master@59f8e8d / 子仓 feat/phase55-collab-parallel@82e3050（+1 个未提交补丁，见 MISSING.md 版本一致性节）。

## 阅读顺序（研究 Agent 建议）

1. **本 README** + `00_snapshot/snapshot.json`（仓库/运行状态基线）
2. **`01_reports/PHASE56_COLLAB_FRAMEWORK_PROPOSAL.md`**——被研究的主张（v3 提案：决策并行层+确定性流水线+专家降级）
3. **`CLAIM_EVIDENCE_MATRIX.md`**——10 项主张×证据×复算结果（先看"是否支持"列与"无法核验"节）
4. 深入按主题：`04_runtime_evidence/`（run 记录/时间线/请求链）→ `02_source/`（机制实现，SOURCE_MAP.md 索引）
5. 缺口与限制：`MISSING.md`

## 目录说明

| 目录 | 内容 |
| --- | --- |
| 00_snapshot | git 双仓状态/取证时刻/未提交补丁 diff/运行实例映射说明/未结清在途（=无） |
| 01_reports | v3 提案全文、P56 A/B/C 正式报告、00-06 任务书+启动提示词、P55 报告与任务书、P54 报告（HISTORY_ 前缀）、研究指令（_HANDOFF_ 前缀=交接件非证据） |
| 02_source | 关键源码 55 文件全文（2.2MB）——SOURCE_MAP.md 给符号级索引 |
| 03_config_redacted | 脱敏 config、冻结清单×2、参考策略、额度账本+运行时真实读数、env 白名单 |
| 04_runtime_evidence | 6 个 run 协调账本、4 份正式终审报告、4 份规范化时间线 JSONL、jobs 规范化导出（142 条）、RUN_INDEX、4 条最小请求链（chains/） |
| 05_tests_existing | P56/P55 定向测试源码 + 全量回归日志（gzip）+ 失败清单提取 + 口径说明 |
| 06_analysis | 复算脚本与输出（CLAIM_RECOMPUTATION.json）——复现方法全开放 |

## 最重要的三个证据点（研究入门）

1. **`chains/chain_B_依赖镜延误_INF3_s01_c02.json` + timeline**：依赖镜晚提交 651s 的完整时序——v3 提案"依赖自动派发"的直接依据。
2. **`run_record_*_INF2`（repair 段）+ review_INF2_formal_v2.json**：确定性修复 3 连败未变策略的完整证据——"子 producer 决策点"的存在性证明。
3. **`run_record_*_INF*` concurrency_effect + timeline 区间并集**：容量 1/2/3 生效与峰值在途——"机制通、墙钟不动"的矛盾定位。

## 快照限制

- 单时刻快照：取证期间无运行中 run、无非终态 job（见 snapshot.json），但 6 个 run 跨越当日多次后端重启——跨 run 的时钟均为同一台主机 wall clock（可比），进程内状态无逐时刻记录。
- 私有媒体 URL 已剥离（chain JSON 内注明索引方式：project.json 的 video_versions.version_id）。
- 未包含：P3/六员臂/复验轮（尚未发生，见 MISSING.md）。

## 体积与完整性

- 核心 ZIP：`COLLAB_RESEARCH_EVIDENCE_CORE_20261018_1300.zip`（SHA-256 见包外回报）；MANIFEST.json 含全部 payload 的 SHA-256/来源/脱敏状态。
- 本包**不是**架构验证结论——是可独立阅读的证据底座；结构判断由研究 Agent 完成。
