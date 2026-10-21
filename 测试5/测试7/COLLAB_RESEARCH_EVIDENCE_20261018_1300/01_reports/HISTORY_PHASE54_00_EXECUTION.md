# PHASE54 执行文档——Producer 扩权 + 协作模式对照（2026-10-15 启动，用户批准「继续下一阶段」）

## 任务来源
用户 10-15 指令：继续下一阶段；Producer 单独生成以及其它模式测试；全部做完再看片。
依据：A 报告 §0 用户四模式原话、B 报告 §5 scoped grant 前置条件、C 报告 §5/§8 顺序、F/M 追加缺陷（§12.1/§12.2）。

## A 批（工程前置，零媒体）
- **A1 scoped grant**：`src/agents/grant.py`——项目级可撤销授权（families→工具面合并+审计 jsonl+TTL+revoke）；producer turn 挂钩（合并后工具面+系统提示 grant 通知+零工具谎报闸门措辞适配）；REST 端点 grant/revoke/list（routers/agents.py）。
- **A2 prior-credit 豁口修复**（executor.py）：rejected 修复 attempt 的目标镜必须产出**新 versionId**（writeSource=prior 不再计入修复目标 spec）。
- **A3 终审卡重开入口**：POST /runs/{id}/reviews/{rid}/refresh——重算内容快照+指纹+事件留痕（409 首拒语义不变，重开须附 reason）。
- 回归：全量测试零回归后重启后端。

## B 批（模式对照测试，串行）
- **B1 模式② 单 Producer 全流程**：新项目 P54_M2，**复用 F《灰塔》故事文本**（与六员链基线 F 4h48m/103s 直接对照）；grant 五族工具；单 producer 会话完成 故事→look→场景(墙则跳锚)→分镜→视频→装配；执行侧终审（帧验三查）。额度预算 ~100s。
- **B2 模式④ Producer 主执行+困难上交**：复用 M《回声》故事文本（对照 M 4h40m/94s）；grant 同 B1 + 保留 5 delegate（上交通道）；同口径终审。额度预算 ~100s。
- **B3 模式③+多线程**：需并行委派调度开发，工程量最大——视 B1/B2 结果与剩余额度/时间决定当日是否启动（不默认做）。
- 判定口径：与 A 批基线同表（墙钟/额度/节点干预/成片三查）；「快」的来源必须可归因（协调开销 vs 生成延迟 vs 审核在环）。

## 度量
- 每模式：全程墙钟、LLM 会话数（模式②应=1）、tool calls、text/video/images 用量、成片时长、执行侧终审帧验判定、干预次数。
- 环境约束：额度 video 500s/day（今日已用 197s，剩 ~300s——B1+B2 约 200-260s 可当日完成，超则按运行手册次日续）；后端改动须重启；Python 用 D:/Delta Force/python.exe。

## 报告
- PHASE54_REPORT.md（测试4/），含「吞吐与额度利用」独立章；执行侧终审帧证据 evidence/；完成或额度耗尽即向用户总汇报。
