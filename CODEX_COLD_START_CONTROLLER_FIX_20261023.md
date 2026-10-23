# 冷启动重复生产控制器修复（2026-10-23）

**当前部署：PR #1–#5均已合入默认分支`chore/migration-readiness`，合并提交`488ffa7fbc76499bee8037ae1078aa0d12de3b95`。最新三分钟真实验收运行[40002008268](https://github.com/Q-1844/agent-system-v2/actions/runs/40002008268)；截至2026-10-23T18:24:41.931326+00:00，workflow=in_progress、检查点=RUNNING。最终成片尚未验收。**

## 真运行发现的问题

run 39998736879中，新FRAME_HOST_TOKEN已通过新内容地址的实际PUT与公网就绪校验，FFmpeg也通过。原FullProject开始后却被尚未结束的startup recovery再次发现并派发，形成两个控制器。

真实Actions日志原时间：

- 17:54:35.279：FullProjectRun启动frun_e624b1a36f。
- 17:54:35.280：恢复同一个frun_e624b1a36f。
- 17:54:38.898：s01 Director已应用，创建4镜头。
- 17:54:45.886：同一run blocked/EXTERNAL_SOURCE_CHANGED。

两次Director输出不同，磁盘已写入一份镜头，但manifest与run检查点被另一控制器覆盖；外部变更保护因此触发。该次4文本调用、0图片、0视频，无付费视频提交。下载的artifact SHA256为GitHub回执a70aa3e0ff40d875fbda6eb883d1fe94c856ab331c10d51e4a21af0c4fcc4756；镜头、manifest与检查点均已核对。该artifact仅16974字节，不包含成片。

## 修复

[PR #5](https://github.com/Q-1844/agent-system-v2/pull/5)，源码`d7bc39ae70b69e1d32322eeff54d0c80068d7681`。

- API startup依次await Scene、Project、FullProject的短恢复扫描，完成后才接受新生产；恢复后的制作仍在后台运行。
- 三个调度层的_launch_loop同一个run只能有一个活任务。
- recovery跳过已有活控制器，保留其暂停/取消请求与source检查点。
- done callback核对任务身份，旧任务收尾不能移除替代任务的跟踪。
- 外部内容变更保护、生成提交前检查点和不明结果禁重发机制保持有效。

## 验证

三个调度层的6个确定性用例在原实现全部失败，修复后全部通过；覆盖活任务重复恢复、检查点不可改写、以及旧done callback清掉新owner的窗口。

本机完整制作、场景、项目、取消保护及存储恢复组合：399通过、10跳过，零失败/错误；其中原外部源变更blocked用例保持通过。

| 云端运行 | 完整Mock | 存储/恢复 | Agent冒烟 | Linux媒体工具 |
| --- | --- | --- | --- | --- |
| [40001872646](https://github.com/Q-1844/agent-system-v2/actions/runs/40001872646) | 3198通过、10跳过 | 349通过、10跳过 | 28通过、0跳过 | 下载/SHA/编码/探测/解码通过 |
| [40001864912](https://github.com/Q-1844/agent-system-v2/actions/runs/40001864912) | 3198通过、10跳过 | 349通过、10跳过 | 28通过、0跳过 | 下载/SHA/编码/探测/解码通过 |


本机最终全量：3198通过、0失败、10跳过。此前两项取消断言差异已定位到旧soak测试在后台Planner结束前删除项目：现在在测试所属事件循环中取消并await这些测试自己的任务，再还原依赖、删除目录；取消用例的原断言未改。诊断原先遗留两个任务，修复后为零，相关前置用例、取消与资源组合175项通过。

另修复一项Windows随机假阳性：原持久化测试搜索任意b64子串，合法8位hex指纹也可能包含它。现在用确定包含b64的合法指纹作夹具，精确检查编码图片字段与data URL；没有放宽图片二进制不能持久化的要求。新一轮云端两轮完整结果见上表，各组合有重叠，不相加。

## 最新真实三分钟测试

运行[40002008268](https://github.com/Q-1844/agent-system-v2/actions/runs/40002008268)；排队2026-10-23T18:16:56Z；nonce=film3m-20261023-rescue5；source=d7bc39ae70b69e1d32322eeff54d0c80068d7681。测试从修复分支启动；其源码树与合入后的默认分支一致，不重复触发媒体生成。

截至2026-10-23T18:24:41.931326+00:00：检查点=RUNNING，进度={'action': None, 'scene': None, 'stage': 'production', 'status': 'producing'}，文本调用=13、图片调用=2、视频提交=1，其中已确认Provider ID=1。任务是否成功仍以最终视频、原始源镜头、解码及B/B1归档恢复为准。

范围仍是原FullProject→Director/Planner→ProjectProduction→5个SceneRun→composition。规划约200秒，最终真实视频流至少180秒；不循环、不用静帧补时长。视频提交预算240秒，生产内部期限150分钟，Actions job上限180分钟。已有付费提交或结果不明时先对账，不盲目重发。

FRAME_HOST_TOKEN的实际写入已在前次运行证实，不再向用户重复索取。新nonce在旧run明确0图片/0视频后启动，不重复旧媒体消耗。

旧5秒demo2保持enabled=false；原5.184秒t2v只证明单段路径。event=schedule最近API查询仍为0，定时实触发独立保留未验证。Producer新能力及预览页等扩展继续后置。

机器证据：[CODEX_COLD_START_CONTROLLER_EVIDENCE_20261023.json](CODEX_COLD_START_CONTROLLER_EVIDENCE_20261023.json)。此前环境与Windows锁批次见[PR #4报告](CODEX_RUNTIME_BOOTSTRAP_LOCK_FIX_20261023.md)。
