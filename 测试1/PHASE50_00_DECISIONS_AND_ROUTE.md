# Phase 50｜从规则测试转向写实作品生产

编制日期：2026-10-08。状态：执行方案，尚未在项目仓库或视频服务上实施。

## 1. 本轮决定

开始制作写实风格短片：克苏鲁追赶一艘船，船上只有船长与大副两名人类角色。具体剧情、结局、分镜和生成方法交给系统 Agent 根据实际加载的 Skill 完成。

Skill 继续随实际作品修订，但不再以“覆盖所有可能情况”为开片前提。本轮只先处理会使任务失踪、Skill 加载错误、错误素材进入装配的阻塞项。其余测试进入待办，后续由作品中的真实失败触发。

本轮要分别回答：能否自主制作、写实效果是否合格、时间花在哪里、独立任务能否重叠运行。四项结论单独出具；生成成功不等于画面合格。

## 2. 单线程与 Token Plan 不是同一个问题

| 层次 | 需要确认的事情 | 当前判断 |
| --- | --- | --- |
| Agent 推理 | 一个会话是否等待一个长任务返回后才继续 | 取决于现有 Agent 工具与调度器，需看真实轨迹 |
| 项目调度 | 独立镜头是否可以分别提交、持久记录和收货 | 可以设计成有依赖的异步队列；当前实现未独立核验 |
| 服务端生成 | 多个已受理任务是否实际同时推理 | 本次未找到明确公开的在途并发上限，需要账户实测 |
| RPM | 每分钟提交或执行频率 | 属于频率限制，不等同于同时生成任务数量 |
| 额度与价格 | 使用哪个 key 类型、免费模型、时长池 | 影响可执行量，不能直接解释为只能串行 |

[官方事实] Agnes Video 2.5 Flash 使用“创建任务，再查询结果”的异步接口。客户端可以将提交与收货分开；异步接口本身不保证服务端同时推理，也不证明当前系统已实现并行。[S1]

[官方参考值] Token Plan FAQ 列出视频实际可执行频率为 5 RPM。额度表明确列出的旧模型 `agnes-video-v2.0` 为每日 500 秒；不能据此直接断定 `agnes-video-2.5-flash` 使用同一个时长池。多把同类型 key 共享限制池。[S2]

[实施推断] 没有依据将本项目“约一分钟成片耗时约两小时”认定为行业统一标准。它可能包含规划、素材制作、服务排队、返工、审查、人工等待与装配；先计时，再判断。宣传片的生成时间也不能直接作为整片生产对照。

不能承诺开几个线程就等比例加速。真实动作接力有前后依赖；独立镜头有机会重叠；服务排队、共享 GPU 与失败返工都可能抵消收益。

## 3. 文件与顺序

| 文件 | 执行者 | 作用 |
| --- | --- | --- |
| [PHASE50_A_CONCURRENCY_AND_MINIMAL_REPAIR.md](PHASE50_A_CONCURRENCY_AND_MINIMAL_REPAIR.md) | Zcode | 查串行点、最小修复、并发探针、真实计时 |
| [PHASE50_B_REALISTIC_CTHULHU_CHASE.md](PHASE50_B_REALISTIC_CTHULHU_CHASE.md) | Zcode 编排现有系统 Agent | 从故事意图到写实参考、分镜、视频、审片、装配 |
| [PHASE50_C_COMPARISON_AND_ACCEPTANCE.md](PHASE50_C_COMPARISON_AND_ACCEPTANCE.md) | Zcode、用户、跨模型测试者 | 导出共同任务，对比 Agnes 与 Grok，归因和收口 |
| [PHASE50_ZCODE_START_PROMPT.txt](PHASE50_ZCODE_START_PROMPT.txt) | 新 Zcode 会话 | 直接开工 |
| [PHASE50_WORKBUDDY_EXPERT_PROMPT.txt](PHASE50_WORKBUDDY_EXPERT_PROMPT.txt) | 用户选择的专业 Agent | 按需补写实动作、审查或并发方面的专业方法 |
| [PHASE50_DOUBAO_GROK_COMPARISON_PROMPT.txt](PHASE50_DOUBAO_GROK_COMPARISON_PROMPT.txt) | 豆包规划、Grok 执行会话 | 对齐故事目标，使用各自真实可用能力 |

A 先完成关键阻塞项与计时接线；B 随即开始，不等待全部并发级别测完。并发探针优先复用 B 中已经批准、确实独立的任务。C 的比较包随 B 的规划与产物陆续导出。

WorkBuddy 专业研究可以独立进行。未拿到新 Skill 时，使用已核验的现有 Skill 开片；拿到后另开候选分支，不能在同一冻结运行中途替换。

## 4. 保留的项目约束

- 保留现有六个 Agent：Producer、编剧、角色资源、场景、导演、装配；保留 canonical、OCC/revision、receipts、resource locks 和任务治理。
- 通过正式生产入口执行。Zcode 做修复、观测与核验，故事和逐镜方法由系统 Agent 判断。
- 原始 Skill 必须可读、版本可追踪。不能根据旧修订表重建一个包后，声称测试了原始包。
- 所有适用的文本与视觉审查调用开启 Thinking，核对实际出站请求；采用当前模型真实支持的开关。
- 免费主链不自动切收费模型。价格、模型 ID 和账户权限只做一次必要核对，随后聚焦方法与成片。
- 源视频至少 8 秒，默认 10 秒；本轮常规在 8–12 秒内安排。[S1] 成片片段时长另定。
- 无旁白、无主动 TTS。第一版无人物对白，以保留合格原生环境声和同步音效为主。
- 产生审片候选属于本轮执行范围；涉及现有用户专用正式选版入口时，沿用现有规则。

## 5. 本轮先做与后做

| 现在必须做 | 可以后续做 |
| --- | --- |
| 提交、收货、恢复与 Skill 绑定的实际阻塞 | 全部模型、全部模式与风格的笛卡尔积测试 |
| 写实参考素材与输出风格一致 | 长对白、声线、口型和独立音乐系统 |
| 双人物身份与人数、船和怪物、关键动作的审片闭环 | 大规模多角色、复杂连续长镜头 |
| 实际裁切端点、上游版本与下游失效处理 | 每一种海况、机位、道具的完整覆盖 |
| 独立任务能否并发及耗时分类 | 通用工作流 Fork/Join 产品化与画布重设计 |
| 首次结果、修复后结果、介入与用户看片 | 每镜大量候选，或者预先批量生成二十张首帧 |

“可以后做”须进入未测清单，不能被报告成已支持。片中遇到的新错误先保存证据，只修对本轮有效的规则。

## 6. 本轮收口条件

交出完整可播放写实候选、逐镜原片与裁切版本、真实 Skill 加载证据、首次失败和返工账本、计时与并发结论、跨模型共同任务包。用户对审美与剧情作最终判断。

若合格写实输入、正确请求和可恢复执行已落实，少量定点复验仍达不到要求，而用户同任务 Grok 结果明显更好，就将主线转为更好模型接入与作品生产。无需再为 Agnes 扩大一轮通用规则工程。

## 7. 官方依据与边界

- S1：[Agnes Video 2.5 Flash 官方文档](https://wiki.agnes-ai.com/zh-Hans/docs/agnes-video-25-flash)。本次确认异步创建/查询、源时长区间和模式限制。免费状态属于可变化事实，执行日再核对。
- S2：[Token Plan FAQ 官方仓库](https://github.com/AgnesAI-Labs/AgnesAI-Models/blob/main/docs/TOKEN_PLAN_FAQ.md)。本次读取页面标记更新时间 2026-06-28；它是公开参考值，不代替账户控制台与响应。
- S3：[Agnes 官方模型参考](https://github.com/AgnesAI-Labs/skills/blob/main/agnes-ai-models/references/model_catalog.md)。页面标记更新时间 2026-09-24，说明新旧模型和查询标识应区分。
- S4：[Grok 视频生成官方文档](https://docs.x.ai/developers/model-capabilities/video/generation)。说明异步生成及耗时受任务规格影响；不构成一分钟成片的耗时承诺。
- S5：[Grok Reference-to-Video 官方文档](https://docs.x.ai/developers/model-capabilities/video/reference-to-video)。当前 1.5 官方支持首帧与参考组合，以及首尾与内部关键帧；用户所在平台是否开放需另核对。
- S6：[WorkBuddy 官方产品介绍](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Product-Guide)。官方列有多智能体并行场景；不能据此推定其专家已具有本项目所需 Skill 或视频质量保证。

当前编制环境没有项目仓库、原始 Skill 包和实际视频。此前报告中的执行缺口与效果判断均是待执行者核验的历史线索。本文件没有宣称这些缺口已经修复，也没有宣称任何视频测试已经通过。
