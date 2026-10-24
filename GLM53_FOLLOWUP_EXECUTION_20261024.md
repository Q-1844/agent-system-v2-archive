# GLM 5.3 后续执行清单

本轮成片已生成并完成独立核验；不要重做。nonce film3m-20261023-rescue5，原生FullRun frun_80b1bd5120；归档接续运行40081890414。最终以C仓CODEX_FILM_CLOSURE_REVIEW_20261024.md及机器证据为准。Codex负责本轮收尾与关键修复；以下较大联动交本地GLM实施。

## 先固定基线

1. 拉取A默认分支chore/migration-readiness，确认PR #10/#11/#12已合入。
2. 正常制作driver默认330分钟，job360分钟；至少保留30分钟外层缓冲、15分钟有界收尾；AGNES_VIDEO_INFLIGHT=1和240秒视频预算保持。
3. 本轮视频20个ID、累计200秒、图片41次、文本57次全部保持；已验证成片202.861秒，B Release422624439，final.mp4资产671782040，SHA256 e6c3a743f2d6453b1930ad3dbbf21fc0b546a97b42271c7cd166e392970ea49f。正确项目包资产671834416、project-40081890414.tar、SHA256 24cbce1725001f51c60495082945f077ab3889b31bcf8c957d517d7ce1990574。原partial project.tar保留，不作为full恢复凭证。

## P1：Registry制作生命周期联动

现状：生产检查点已COMPLETE、原生FullRun/ProjectRun/SceneRun已completed、归档状态VERIFIED_RESTORABLE/full，但独立Registry ProjectRecord.production_status仍保留默认IN_PROGRESS。源码tools/relstore/project_registry.py目前只有默认枚举与排名逻辑，没有正式制作完成事件。不能把归档成功直接等同于任意项目制作完成，因为系统允许对在制项目归档快照。

实施：

- 先读Registry现有CAS、operation_id去重和毒化实例规则，添加显式、可幂等的制作生命周期事件。
- 完成事件必须引用已确认的原生制作终态与对应版本/产物；不得仅根据archive_status或文件名推断。
- 对账当前真实项目后，通过正式事件把production_status同步为COMPLETE；保存旧值、证据、operation_id和CAS回执。不得直接手改JSON绕过状态机。
- 检查COMPLETE项目与六份活跃名额、后续有效编辑重新进入制作的关系；沿用既有G4-A规则，未定义之处先写清方案，不擅自删除或移出素材。
- 测试：重复完成、完成回执丢失、CAS冲突、仍有open_jobs、过期产物、仅归档未制作完成、完成后真实编辑。保持被拒绝路径零写入。

## P2：Actions取证包去重

现状：完整项目约258MB，e2e-evidence约1GB，包含项目、打包tar、重新下载tar和恢复副本。长期每天制作会重复保存相同媒体，不利于传输和取证。

实施：

- 长期原件继续保存在B Release，B1保存不可变引用、SHA及full恢复回执。
- 成功后Actions证据优先保留summary、source-videos、manifest、校验/恢复报告、运行日志和B/B1引用；避免在同一证据包放四份相同媒体。
- 失败时必须保留可接续的原生项目/队列/已受理素材，或先将完整失败快照上传B并重下载SHA核验，再用明确指针替代；不能为了瘦身丢掉唯一付费素材。
- 协同更新full_project_resume与watch_full_project读取新证据格式；保留旧ZIP格式兼容及严格路径/SHA/身份检查。
- 增加成功/失败/上传中断/指针丢失/旧包兼容测试，证明未知视频提交不会被补交。

## P3：一日一片的真实任务排产（后续范围）

本轮已补足单次6小时制作窗口；没有增加每日新建付费demo。若继续做自动排产，先接真实任务来源，明确每日去重键、输入/模型/片长、已有素材、预算与恢复策略，再复用FullProject与B1 CAS。不得每日换nonce清零，也不得提高视频并发绕过时限。按片长、模型和有无素材分别采样耗时，保留用户确认的3.2分钟从零约4.5–5小时作为当前口径。

## 验证与交付

- 分支逐项修改，每项给具体触发前后行为、测试和风险；只改必要范围。
- 跑相关保护测试与仓库要求的CI；保留原断言，不用Fake通过代替真实媒体验收。
- 较长监控使用tools/watch_full_project.py和固定运行配置，本地执行即可；不把视频二进制、全量日志或密钥塞进模型上下文。
- 更新C仓对应报告和入口。现有成片与归档保持可下载可恢复，Producer新能力继续后置。
