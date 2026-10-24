# 原长片收尾与时间窗口复核（2026-10-24T09:33:40.177589+00:00）

截至2026-10-24T09:32:08.508552+00:00：显式收尾运行40081890414，Actions=completed/success、B1=COMPLETE；累计仍20个视频/200秒，图片41次、文本57次，原20个视频回执完整未变。

## 原因与实物对账

已读GLM53_RUN40055563112_TERMINAL_RECONCILE_20261024.md。40055563112因旧150分钟驱动上限中断，没有发现新的生成/下载故障。API原归档ID12548693050，135,862,027字节，SHA256 e2d08aa8160901374974cec41ec11f15eea961564704b09a023333a63ed2fdb5；本轮独立重下载SHA一致。20段选中视频全部ffprobe和ffmpeg -xerror完整解码通过，移动视频流合计202.5秒。

最后一镜s05_c04的VideoVersion vv_b0c76b8f4bc3、final_video和本地完整文件已经落库；未完成的是队列f960e35cc110与SceneRun结束登记，现场位于endframe阶段。没有新建版本，也没有按文件名猜视频归属。

## 已合入

[PR #10](https://github.com/Q-1844/agent-system-v2/pull/10)，最终源码`88498aef0f8aba6bd08923914c073481bd29397c`，merge`c91a92fe12c1fc040f051476dd43a248a97d1cf9`。

- 显式resume_run_id + finalize_only；原nonce film3m-20261023-rescue5、FullRun frun_80b1bd5120、ProjectRun prun_4ddff9a28f、五个SceneRun和全部已完成素材保留。只有文件解码、选中版本、accepted ID、job和原生active_job_id全匹配后，才对账已提交结束但未落结束登记的任务。取消/未知/缺文件/选版不同仍拒绝恢复。
- finalize_only封锁Agnes chat/generate_image/create_video。只补齐末帧结束登记，原生合成、>=180秒完整解码、B Release保存、B1 Registry与项目恢复核验。累计200秒仍计入240秒预算。
- 正常制作默认driver330分钟、workflow360分钟，至少30分钟外层余量；driver支持30–330整数分钟。15分钟有限暂停收尾与AGNES_VIDEO_INFLIGHT=1保持；视频预算不改。当前收尾特设driver60分钟。
- 用户确认3.2分钟从零制作约4.5–5小时；不同模型、片长和有无素材分开评估。六小时窗口为单次作业容量，不等于新增每日自动付费任务。

## 回归

本机完整3283通过/10跳过，0失败/0错误；收尾/恢复/保险丝专项72通过。真实快照离线恢复复用了20段所有原字节，只对账f960e35cc110，累计200秒不变。
- 云端[40079629975](https://github.com/Q-1844/agent-system-v2/actions/runs/40079629975)：完整3283通过/10跳过，恢复434通过/10跳过，Agent冒烟28通过；Linux媒体编码/probe/解码通过。
- 云端[40079626325](https://github.com/Q-1844/agent-system-v2/actions/runs/40079626325)：完整3283通过/10跳过，恢复434通过/10跳过，Agent冒烟28通过；Linux媒体编码/probe/解码通过。

## 收尾终态

B1已COMPLETE，视频时长202.861003秒；云端归档/恢复证明在机器证据中。本地独立核验见film-closure-independent-verification.json；不能以回归测试代替实际成片验收。

Registry的production_status仍为默认IN_PROGRESS（独立于已COMPLETE的生产检查点与已VERIFIED_RESTORABLE的归档）；生命周期联动和约1GB证据包去重列入[GLM后续执行清单](GLM53_FOLLOWUP_EXECUTION_20261024.md)，不直接绕过CAS修改字段。

操作说明：[FILM_FINALIZATION_20261024.md](FILM_FINALIZATION_20261024.md)。Producer扩展继续后置。

补充[PR #12](https://github.com/Q-1844/agent-system-v2/pull/12)已合入：首次收尾40080231475已经合成202.861秒成片并保存B，随后因project_input:/input缺失被严格拒绝full归档。补存canonical真实故事/场景输入快照，保留来源说明和原输入；不放宽恢复校验。允许completed FullRun直接跳过制作和合成，仅重试归档；显式复用Release422624439、final.mp4资产671782040，保留原partial project.tar，以新运行专属包名保存正确归档。

PR #12最终本机完整3286通过/10跳过，0失败/0错误。
- 归档修复云端[40081233409](https://github.com/Q-1844/agent-system-v2/actions/runs/40081233409)：完整3286通过/10跳过；恢复437通过/10跳过；冒烟28通过。
- 归档修复云端[40081226907](https://github.com/Q-1844/agent-system-v2/actions/runs/40081226907)：完整3286通过/10跳过；恢复437通过/10跳过；冒烟28通过。

补充[PR #11](https://github.com/Q-1844/agent-system-v2/pull/11)已合入：RESTORED认领同时刷新心跳，避免初始化阶段沿用旧心跳造成只读监控误报。该一行元数据修复不改变当前收尾运行或预算。
