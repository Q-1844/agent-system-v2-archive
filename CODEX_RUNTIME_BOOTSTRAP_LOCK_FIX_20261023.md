> 最新状态：run 39998736879于17:54:46Z记为FAILED，0图片/0视频；下文早期RUNNING快照仅保留历史。修复分支collab/full-project-preparation-20261023，PR #5。

# 运行环境与Windows并发锁修复（2026-10-23）

**当前部署：PR #1–#4已合入默认分支。真实长片39998736879已在文本规划阶段停止：启动恢复重复派发同一FullRun，触发外部变更保护。图床新Secret与FFmpeg已通过；4次文本、0图片、0视频。PR #5修复控制器重复派发，当前待CI，暂不等待长片完成。**

## 本次修复

PR #4：https://github.com/Q-1844/agent-system-v2/pull/4 。源码 `6a30ec94bfa56c2cf2743a2bb097af5e60e87480`。

1. 默认分支CI 39994646693实际出现Windows `PermissionError`：两个进程同时观察到空锁文件，其中一个先锁住首字节，另一个再flush初始化字节时失败。移除锁前初始化写入，直接锁住空文件首字节；Python官方明确支持锁区间延伸到EOF之外。保留跨进程独占、超时、重入和异常释放。新增双spawn进程在12个全新空文件上竞争，逐个验证计数无丢失且锁文件始终为空；原租约唯一持有者断言和15秒超时不变。
2. 真长片39994958081于2026-10-23T17:32:04Z在Install ffmpeg退出124；实际媒体步骤skipped、B1检查点不存在，未调用Agnes。Apt安装路径替换为共用的有界下载脚本，长片与patrol均采用同一路径。固定BtbN月末保留版本及SHA256，只提取ffmpeg/ffprobe两个工具。CI强制走下载分支，再实际编码、探测和完整解码1秒H.264夹具；该夹具仅验证环境，不计作用户要求的真实成片。
3. 最终成片的完整解码启用`-xerror`：出现损坏帧时必须失败，不能只因容器和视频流时长达到180秒而通过。

固定发行：autobuild-2026-09-30-13-08；包ffmpeg-n8.1.3-9-g29e619e767-linux64-gpl-8.1.tar.xz；150,360,944字节；SHA256 `97ce978979194b5cf7e06a5e68020dbdaa7a4f3294c5452b6a1bc347100dbb79`。已在本机下载核算并列出精确归档成员；云端实际执行通过。上游月末发行保留两年，后续更新必须同步固定URL与校验和。

## 验证

| CI运行 | 完整Mock回归 | 存储/恢复专项 | Agent冒烟 | Linux媒体工具 |
| --- | --- | --- | --- | --- |
| [39997455184](https://github.com/Q-1844/agent-system-v2/actions/runs/39997455184) | 3192通过、10跳过 | 343通过、10跳过 | 28通过、0跳过 | 下载/SHA/编码/探测/解码通过 |
| [39997447886](https://github.com/Q-1844/agent-system-v2/actions/runs/39997447886) | 3192通过、10跳过 | 343通过、10跳过 | 28通过、0跳过 | 下载/SHA/编码/探测/解码通过 |


本机最终源码存储/恢复、长片保护与并发组合：388 passed、10 skipped，零失败/错误。统计集合有重叠，不相加。

本机首次全量在前一提交5f5878c上为3188 passed、3 failed、10 skipped：一项因本机venv缺NumPy，已安装仓库锁定版本2.3.5；两项取消测试在全量时断言全局inflight字典为空，但其中包含其他测试的后台任务；同文件隔离运行12项通过。未因此修改生产取消逻辑或放宽断言。相关裁剪和取消完整文件重测20 passed，零失败。最终源码的两轮GitHub Windows全量结果见上表；本机首次全量不能写成全绿。

## 新Secret与真实长片

用户已创建并保存Repository Secret FRAME_HOST_TOKEN。新runner已通过每次新内容地址的图床上传与公网就绪预检，随后进入原制作链。 不读取或展示Secret值。

运行：[39998736879](https://github.com/Q-1844/agent-system-v2/actions/runs/39998736879)；排队：2026-10-23T17:53:07Z；nonce：film3m-20261023-rescue4；source：2ce24eac5005378c32ac5a484009329d037538e3。

截至2026-10-23T17:54:37.819275+00:00，阶段：['Real FullProject → Director/Planner → SceneRuns → >=180s final film → restore verification']；检查点：RUNNING；图像调用：0；视频提交：0。这只是进行中的生产证据，不能当作最终长片成功。

测试仍走原FullProject→Director/Planner→ProjectProduction→五个SceneRun→composition；目标约200秒，真实最终视频流必须至少180秒；不循环、不使用静帧补时长，每个源镜头须对应独立已确认Provider ID及选中版本。视频提交预算240秒，生产内部期限150分钟，Actions job上限180分钟。完整视频还须通过全解码、B Release下载SHA对账、项目包恢复和B1 VERIFIED_RESTORABLE终态。已有付费提交或结果不明时先对账，不盲目以新nonce重做。

## 保留边界

旧5秒demo2保持enabled=false。原5.184秒单段成片只证明单段路径；不算本次三分钟验收。最近schedule仍未实证；手动workflow_dispatch不能替代schedule证据。Producer新能力、预览页、跨仓素材扩展、新任务来源仍后置。

## 依据与机器回执

- [机器回执](CODEX_RUNTIME_BOOTSTRAP_LOCK_EVIDENCE_20261023.json)
- https://docs.python.org/3/library/msvcrt.html
- https://github.com/BtbN/FFmpeg-Builds#release-retention-policy
- https://www.ffmpeg.org/ffmpeg.html （-xerror）
