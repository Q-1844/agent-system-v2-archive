# 压缩额度接续：可重复测试与真实验收

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
