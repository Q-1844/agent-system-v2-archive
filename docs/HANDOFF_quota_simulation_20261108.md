# 压缩额度接续：最终验收与后续真实跨日测试

## 最新结论：多窗口测试已完整完成

`quota24x2m-20261108` 在合并本轮修复后，经过四次自动接续完成制作。
[最终运行 42453709415](https://github.com/Q-1844/agent-system-v2/actions/runs/42453709415) 为 success；B1 检查点及独立注册表均为 COMPLETE。

| 生产运行 | 测试窗口 cycle | 累计完成镜头 | 累计受理秒数 | 本窗口用量 |
| --- | ---: | ---: | ---: | ---: |
| 42449798562 | 0 | 3 | 22 | 22 |
| 42451698938 | 1 | 5 | 41 | 19 |
| 42452208391 | 2 | 8 | 62 | 21 |
| 42453175163 | 3 | 10 | 81 | 19 |
| 42453709415 | 4 | 11 | 91 | 10 |

前四跳 Actions 的 failure 来自预期的额度暂停；权威状态为 WAITING_QUOTA，均已排水并由自动链路接棒。每个测试窗口上限为24秒，等待2分钟，真实500秒日账本持续累计，没有随窗口刷新清零。

独立重新下载最终MP4、完整归档及四个源跳artifact，校验结果如下：

- 11镜最终成片95.245036秒，完整ffmpeg解码通过；11个供应商任务号与源视频SHA均唯一。
- 四个源跳的已选版本、供应商任务号与视频字节SHA逐一匹配最终归档，原素材全部保留。
- 所有11条提交意图为COMPLETED，没有SUBMITTING/UNKNOWN；所有额度暂停点无running视频Job。
- 归档129290240字节，完整恢复91个文件，restore_level=full，missing_required为空；检查点与注册表归档引用一致。
- [独立机读验收报告](evidence/quota24-complete-audit-20261108.json)记录下载哈希、各窗口进度及归档引用。

## 修复版本与回归证据

- [PR #55](https://github.com/Q-1844/agent-system-v2/pull/55)：持久化nonce限定的测试窗口、保留真实日用量、结构化暂停来源与安全压缩旧闸门。
- [PR #56](https://github.com/Q-1844/agent-system-v2/pull/56)：额度复检、视频POST与2xx记账互斥，消除并发透支窗口；生成与轮询仍可并行。
- [PR #57](https://github.com/Q-1844/agent-system-v2/pull/57)：仅对具备完整源证明且已排水的显式短测试跳过15分钟死链宽限；真实生产策略保持。

三项已合并，最新默认分支提交为 `f527e35940357f92061eb484d49c845f7fc66f5a`。最终全量回归 **3996 passed，0 failed/errors/skipped，438.68秒**；远端Linux恢复回归、pipeline smoke、Windows全量CI均已通过。

原二十分钟影片及旧三分钟接续事故也已独立验收完成，分别见下方历史过程及对应机读报告。此前确有故障并经修复，本结论指当前修复版本通过了上述验收。

## 下一轮验收

用户已明确授权补写本最终结果，并派发一部约1000秒的新片进行真实跨日测试。新任务将使用正常每日500秒额度、`quota_test_wait_minutes=0`，不再人工压缩闸门。新片已提交，GitHub返回204接受派发。

- 片名：《风雪中的最后一班夜车》，约1000秒（约16分40秒）。
- nonce：`real1000s-20261108T155648Z-fcc9`；提交时间：`2026-11-08T15:56:48.271984+00:00`。
- [运行 42497354788](https://github.com/Q-1844/agent-system-v2/actions/runs/42497354788)；派发默认分支：`chore/migration-readiness`；提交时源码：`f527e35940357f92061eb484d49c845f7fc66f5a`。
- `acceptance_scope=full-project-3min`，`target_duration_seconds=auto`，`media_inflight=2`，`driver_timeout_minutes=330`。
- `daily_video_seconds=500`，`quota_test_wait_minutes=0`；全新任务，未传resume_run_id、source_project或archive_release_id。
- 按此前用户授权，`confirm_uncertain_submissions=true`，接受此nonce后续UNKNOWN重提的可能重复计费；供应商回执与可能成本仍须保留。

完整创作请求：

> 请创作并完成一部约1000秒（约16分40秒）的独立电影《风雪中的最后一班夜车》。故事起点：山间小站的一位年轻夜班员收到一张几十年前未兑现的车票，他与一位退休机车师在暴风雪到来前修复废弃支线，帮助被困旅客回家，途中逐渐揭开这条铁路停运的往事。这是全新影片。由Producer自主发展剧情、人物、场景、镜头和节奏，并自行决定专家协作与制作方案；请保持人物与视觉连续性、清楚的因果和情绪递进，完成有铺垫、有转折、有结局的完整作品。

仅确认派发被接受并读取一次运行列表取得链接，未等待启动、生成或观察制作进度。此新任务的真实跨日结果尚未验收，留待次日检查。


派发确认后停止主动监控，留待次日核对真实额度暂停、自动接续、新有效视频、旧素材完整性与最终合成归档。不能将派发成功或RESTORED单独视为真实跨日终验通过。

---

## 历史过程记录

以下保留各阶段记录；其中“进行中/还需核对”等表述属于当时状态，以本文开头的最终验收为准。

## 当前工作

用户授权以小额度、较短间隔反复测试，失败就修复复测，直到链路正常或供应商当天500秒额度耗尽。本轮不把RESTORED或派发204当作通过。

GLM的215跳事故补丁已读（A仓`docs/HANDOFF_starter_zombie_and_quota_sim_20261108.md`、`bb1702a`）。旧测试nonce `film3m-42394136215`停在22/23镜，Job `f07d5b401e9e`/s05_c04明确not_sent，本地日账本173/500；原Job闸门16:10Z。仅压缩CP无法改变Job闸门，也不会刷新同日额度。

## 已合并修复

[PR #55](https://github.com/Q-1844/agent-system-v2/pull/55)，合并`56e982be8b1d99214edb9c7cdbf59745de3cc81b`，源码提交`24a96dba608efe74c16699d38a223093e70358cf`。

- 按nonce冻结quota_test_policy，测试窗口随cache/quota.json保存；窗口刷新不清除真实日用量，真实500秒/供应商daily拒收始终优先。
- 新任务显式daily_video_seconds小值+quota_test_wait_minutes非零启用；续跳从检查点继承，不因默认输入500丢失模拟策略。默认生产不会只凭缓存激活模拟。
- 原生预检与HTTP客户端传递结构化日期和来源，拿到限流槽后再次检查；两个worker共享暂停来源。
- 只有有效模拟WAITING_QUOTA启用现有一分钟环境timer，日期闸门照常复查；真实跨日仍20分钟timer。
- b1-test-ops的显式压缩留下原/新闸门、nonce、源owner证明。恢复只同步同项目、not_sent、无任务号、精确旧闸门的Job，保留历史；UNKNOWN/已受理不放行。
- 连续三次无媒体进展自动20分钟技术退避，resume_not_before独立于额度日期闸门，避免生命周期跳数上限再次造成热循环。

未改Asset结构、创作输入签名、文本输出上限或末帧3次重试+20分钟终试策略。

## 测试

新增21项行为测试；722项关联通过。最终全量**3985 passed、0 failed/errors/skipped，443.715秒**，含真实P55归档样本。Linux runtime-regression及pipeline-smoke通过，Windows全量最后检查仍在运行。

原生handler+真实JobQueue+真实客户端/本地HTTP替身跨三个生命周期、两次窗口刷新通过：闭闸零POST，开闸只重排下一镜，旧版本及SHA保留，真实日用量连续累计，零未知意图。原始108758180字节artifact（SHA256`41bccd898c097c12ef9be0556e67f74fc13fbc70507239081400c555190213ad`）回放只放行1个not_sent任务，48个done Job保持不变，零付费调用。

## 真实测试 A：修复旧压缩事故

- 原owner42443592275，使用b1-test-ops将CP闸门压至`2026-11-08T05:08:03Z`，原16:10Z闸门及来源证明保留。
- 取消旧长等待票据42449135522，派发短timer测试；[唤醒42449568289](https://github.com/Q-1844/agent-system-v2/actions/runs/42449568289)成功。
- 自动派发[接续42449663784](https://github.com/Q-1844/agent-system-v2/actions/runs/42449663784)，已RUNNING、error=null，22→23条ACCEPTED，原22条逐字段保留。新增视频及最终归档还需继续核对。

## 真实测试 B：多窗口短片

- nonce：`quota24x2m-20261108`
- 新任务[42449798562](https://github.com/Q-1844/agent-system-v2/actions/runs/42449798562)，同一默认分支，auto规划约90秒《灯塔修表师》。
- 显式24秒测试窗口、2分钟刷新、两路在途、30分钟driver；原有UNKNOWN风险授权在本nonce创建时保存。真实日账本500秒不清零。
- 排在旧片收尾后运行，不重复派发。必须跨越多次WAITING_QUOTA、完整排水和自动恢复，确认window.cycle递增、新有效视频增长、原回执及SHA保持。出现FAILED/blocked或空转就定位修复后从最新owner恢复。
- 若供应商真实daily quota拒收，停止短窗口测试，保留真实跨日等待，不能伪造刷新。

## 原二十分钟影片终验已完成

独立回读347322006字节MP4、2092421120字节重建tar，SHA与B1一致；MP4完整解码，视频1213.184001秒，音频/容器1213.205333秒。145镜顺序及选版、145个源SHA唯一、原137镜任务号/版本/SHA全部保持；882文件restore full、missing_required为空；B1与注册表COMPLETE。

机读报告：[ink-complete-audit-20261108.json](evidence/ink-complete-audit-20261108.json)。这确认修复后的影片最终完成，不等于此前全程无人干预无故障。

## 实测补充：首轮窗口与并发边界

旧三分钟片已COMPLETE并独立验收：23镜、视频181.983968秒，166文件restore full，原22镜版本和SHA全部保持。报告[evidence/quota-legacy-complete-20261108.json](evidence/quota-legacy-complete-20261108.json)。

新片首轮在22/24秒正常暂停，3个视频全部落盘，零running视频Job，闸门05:27:13Z。自动完成事件唤醒42450816469正确选中short_timer=true；但通用巡检15分钟死链宽限导致已开闸仍rearm。PR #57只为显式短测试、completed+drained+SHA/仓库/workflow匹配的源跳过该宽限，近期派发去重和全部存活检查保留；683项关联通过，最终全量进行中。

故障注入另复现POST回执重叠导致同一余额两次通过（12秒窗记16秒）。[PR #56](https://github.com/Q-1844/agent-system-v2/pull/56)已合并`f5ec4dfb26b62e7d6824a6aa495caeee16bf6658`，限流槽后把额度复检、POST和2xx记账串行化，生成及轮询仍并行。修复后该场景1 POST/8秒，第二请求安全等待；全量3987 passed、零失败/跳过，439.04秒。
