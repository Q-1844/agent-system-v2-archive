# Phase52 修订版：系统效率优化与 WorkBuddy 独立视频测试

修订日期：2026-10-11。交付方式：所有文件单独下载，无需解压。

本版根据最新要求重新整理：CodeBuddy 优化我们的系统；WorkBuddy 按我们的实际 Skill，在自己的创作平台中完成视频。平台调查为视频测试提供依据，并随成片一起反馈。

## 文件与分工

| 文件 | 用途 | 接收客户端 |
|---|---|---|
| PHASE52_00_START_HERE.md | 总控、启动顺序、交付索引 | 两边 |
| PHASE52_01_CODEBUDDY_EFFICIENCY.md | 计时、恢复、推进、轮询与代码修复 | CodeBuddy |
| PHASE52_02_WORKBUDDY_SKILL_VIDEO_TEST.md | 加载我们的 Skill，独立制作克苏鲁追船视频 | WorkBuddy |
| PHASE52_03_SYNC_AND_COMPARISON.md | 冻结输入、额度隔离、交换结果、解释差异 | 两边 |
| PHASE52_04_IMAGE_TEST_AND_ACCEPTANCE.md | 无新视频提交的系统与图片测试 | CodeBuddy |
| PHASE52_CODEBUDDY_START_PROMPT.txt | 新窗口开工提示词 | CodeBuddy |
| PHASE52_WORKBUDDY_START_PROMPT.txt | 新窗口开工提示词 | WorkBuddy |
| PHASE52_05_PLAN_VERIFICATION.md | 本版方案与文件的验证范围 | 两边参考 |

这些文件是修订执行说明。正式 Skill 原文、真实项目素材、原始运行日志与项目代码需要在执行端读取；本版没有用历史描述代替这些原件。

## 默认客户端与智能体

| 工作 | 客户端 | 默认智能体 | 实际能力核验 |
|---|---|---|---|
| 日志分析、代码修改、系统和图片链路测试 | CodeBuddy | GLM-5.3-Flash，开启思考 | 工具调用、代码执行、真实出站请求 |
| Skill 阅读、创作推进、图片审查 | WorkBuddy | GLM-5.3，开启思考 | 工具调用、图片输入、素材实际被传入 |
| 难定位的架构问题 | 原客户端 | 必要时 Kimi-K3 | 记录切换原因，避免无依据增加成本 |
| 图片或视频生成 | 各自的生成平台 | 记录真实生成模型 | 不把对话智能体名称写成视频模型 |

客户端列表与账号权限以本机实际状态为准。默认模型不可用时，选择具有所需能力的可用模型并记录；文字模型不能冒充视觉审查器。两边都应核验思考模式，平台内部 Agent 的设置不可见时记录未知。

## 开始执行

可以同时打开两个窗口。

CodeBuddy 先核验真实仓库，导出当前正式 Skill 及其被引用的规则文件，冻结现有剧本、分镜和合格参考素材；然后在自己的分支上继续诊断、修改和图片测试。先完成这个轻量交接，不必等优化完成才让 WorkBuddy 开片。

WorkBuddy 同时核验自身可用工具、Flova 或其他已有创作平台、账号和额度；收到冻结输入后，完成 Skill 加载核验，独立制作视频、审片、局部修复、装配及导出。

如果现成剧本或分镜不存在，WorkBuddy 可以根据实际 Skill 自主规划克苏鲁追船，并在生成素材前冻结自己的规划。这属于独立生产测试，不能标成同分镜对照。CodeBuddy 的工程优化继续执行。

## 哪些可以同步

独立工作区、独立项目和已核实的独立生成额度下，CodeBuddy 图片测试与 WorkBuddy 视频制作可以同时进行。WorkBuddy 不写我们的生产仓库，CodeBuddy 不修改 WorkBuddy 的测试项目。

若两边共用同一个生成账号、API Key、配额池或资源锁，生成请求由一个明确的调度方串行安排。只读分析、日志整理和本地故障测试仍可同步。

我们的 Agnes 视频额度不足时，本地系统不提交新视频；WorkBuddy 若有独立可用视频额度，可以继续制作。客户端不同并不自动代表额度独立。

## 本轮如何结束

CodeBuddy 交出真实修复、前后计时、恢复证据、图片链路结果及回滚点。

WorkBuddy 交出可播放成片、首次结果、源素材、裁切记录、实际 Skill 加载证据、真实生成模型与耗时，并提出能回溯到测试证据的系统建议。

分别判断系统效率、Skill 执行、画面质量和用户看片。视频模型不同或输入不同的结果可以提供方向，但不足以单独证明我们的系统无问题。

## 当前公开依据

- [Flova CLI 官方说明](https://flova.tv/zh-CN/docs/features/flova-cli/)：支持外部 Agent 推进完整项目，包括素材、故事板和导出，制作过程会与 Flova Agent 协作。
- [Flova Skill 官方说明](https://www.flova.ai/en/docs/features/skills/)：支持自定义工作流及新项目测试；项目文档区可以查看生效的 Skill。
- [WorkBuddy 模型配置官方说明](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Model)：目前列出 GLM-5.3 的图片输入与思考能力，GLM-5.3-Flash 列出思考能力。执行端仍需检查实际配置。

公开能力说明不等于当前账号已接入，也不证明视频质量已经通过。
