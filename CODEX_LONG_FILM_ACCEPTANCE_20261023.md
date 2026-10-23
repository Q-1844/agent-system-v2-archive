# 三分钟原制作链真实验收与运行整理（2026-10-23）

**部署更新：PR #1与PR #2均已合入默认分支`chore/migration-readiness`；当前合并提交`8f81b677e41082118cf7433e5278883c34fb5064`。最终源码`f77f4aa`的两轮完整CI均成功。三分钟真实验收仍被D图床凭据403阻塞，尚未生成成片。**

当前结论：代码和离线保护已修正，真实长片尚未通过。云端运行在D图床写入预检返回403，发生在任何Agnes图片/视频生成调用之前。不要等待一个并未继续生产的三分钟成片。

## 用户决定与范围

- 用户已批准整顿现有系统及合入修复；真实生成测试的最终视频至少180秒。
- Producer自主工具、预览页、新任务来源及新协作能力继续后置。
- 本次使用原FullProject → Director → Planner → ProjectProduction → SceneRun → composition，不把单段t2v演示当作完整项目验收。
- 测试剧情为《失联深海站》：水下救援无人机入站、取回记录匣、脱险与回收。只覆盖设备动作、跨场景制作和存储恢复，不声称覆盖人物与对白一致性。

## 代码状态

PR #1已于2026-10-23T16:08:27Z合入默认分支，合并提交6f62dbf88ff79ae0eab1cd12b6ccdf03e49f906a。

本轮PR #2及最终部署状态见本报告顶部的部署更新；提交f77f4aafc8a705888f9f32c7594c0284ffdcb8d3包含以下修正：

1. 保留并暂停旧5秒demo2；巡检和媒体预检共同识别enabled=false。此任务不得用于满足长片验收。
2. 长片驱动规划五段、约20镜、约200秒；只有规划总长192–220秒才授权进入媒体生成。
3. 视频提交总预算240秒；付费POST前持久化CAS意图；提交结果或ID持久化回执不明时阻止再次POST。既有nonce拒绝盲目重跑；这不是完整项目自动恢复已验收的声明。
4. 成片必须有一个真正的视频流，视频流与容器时长均为有限值且至少180秒，并经FFmpeg完整解码。长音轨、封面图、NaN或Infinity不能满足验收。
5. 合成清单必须对应本轮真实任务ID、每镜选中版本及互不重复的源文件哈希；不使用循环、静帧或补帧凑时长。
6. 成功后还需B仓MP4与项目包上传、重下载SHA对账、解包逐文件验证，以及B1 Registry VERIFIED_RESTORABLE。上述长片成功条件仍待实测。
7. Linux媒体环境优先使用现有APT索引；安装和仅发行版源的更新有进程超时，固定ubuntu-24.04。实测安装从先前超过15分钟空等降为本次17秒；不将此写成视频生成提速倍率。
8. 显式要求FRAME_HOST_TOKEN，不再将B1_ARCHIVE_TOKEN隐式用于D图床。图床失败记为生成前阻塞，不能转为生产成功。
9. Project恢复测试只统计同一parent_project_run_id的child，同时断言两个镜头恰好两次视频提交。

九个修改文件已经与PR远端Git blob逐字节对账，全部一致。机器证据见CODEX_LONG_FILM_TEST_EVIDENCE_20261023.json。

## 实际云端运行

- 39986068914：旧长片入口运行，停在FFmpeg安装，于2026-10-23T16:36:41Z取消；媒体生成步骤未执行。
- 39988882623：修正后启动，2026-10-23T16:41:34Z创建；FFmpeg安装16:41:50Z–16:42:07Z，17秒；长片步骤16:42:08Z–16:42:12Z。
- 第二次运行的D仓Contents PUT返回403 Resource not accessible by personal access token，随后运行失败。失败点位于应用启动、Director、图片和视频生成之前；未消耗本轮Agnes生成配额。
- nonce：film3m-20261023-rescue1。B1留下STARTING检查点，后续主程序拒绝对同一nonce盲目重跑。当前会话读到该记录，但尝试按证据补记阻塞状态的CAS写入也返回403，因此没有声称该检查点已成功更新。
- 不把CI成功、安装成功或预检成功当作三分钟成片成功；当前没有三分钟成片、最终时长、成片哈希或完整恢复成功记录。

## 已完成验证

本机Python3.12离线运行：存储/恢复/长片保护340 passed、10 skipped；FullProject/Project/图床相关36 passed；相关恢复两项另外定向通过（与前述集合有重叠，不相加）。首次扩展相关回归35 passed/1 failed，失败是统计其他parent的child；修正测试身份范围并增加提交次数断言后，同一36项组合全过。

最终源码两轮云端CI均成功：[run 39989582134](https://github.com/Q-1844/agent-system-v2/actions/runs/39989582134)；[run 39989572132](https://github.com/Q-1844/agent-system-v2/actions/runs/39989572132)。Windows完整Mock回归、Linux恢复专项和Agent冒烟均通过；具体统计见机器证据。所有Mock回归均不替代真实视频验收。

## 当前配置阻塞及继续方法

在A仓Settings → Secrets and variables → Actions配置或修复repository secret FRAME_HOST_TOKEN。其值需要是能够写入Q-1844/agnes-frame-host的凭据，最小仓库权限为Contents: Read and write。不要把值写入工作流、文档或聊天。

当前会话凭据调用A仓Get repository public key与List repository secrets均403，不能通过API补写Secret；GitHub的细粒度token需要独立的Secrets权限。用户批准继续工作不能替代GitHub凭据本身的权限。

配置就绪后，从默认分支手动启动video-autoproduction-e2e，选择full-project-3min，task_nonce留空以生成新nonce。仅重启本次生成前失败的验收，不重启任何可能已提交媒体的旧nonce。启动后根据实际阶段重新估算；此前60–120分钟只是串行生产估算，当前因配置阻塞没有完成时间。

## 定时巡检

最新查询event=schedule仍为0；保持未验证。默认分支已部署错峰7,27,47 * * * *。是否出现真正schedule事件应独立查证，手动运行不能替代。

## 链接与依据

- PR #1：https://github.com/Q-1844/agent-system-v2/pull/1
- PR #2：https://github.com/Q-1844/agent-system-v2/pull/2
- 真实预检失败：https://github.com/Q-1844/agent-system-v2/actions/runs/39988882623
- Actions Secrets设置：https://github.com/Q-1844/agent-system-v2/settings/secrets/actions
- 官方Secrets API权限：https://docs.github.com/en/rest/actions/secrets
- 官方schedule边界：https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule

部署后手动巡检 [39991006999](https://github.com/Q-1844/agent-system-v2/actions/runs/39991006999) 已成功：produced=0、skipped=2、failed=0；只读预检needs_media=false，跳过FFmpeg安装。对应合并提交8f81b677e41082118cf7433e5278883c34fb5064；此为workflow_dispatch，不计为schedule实触发。

## 当前collab-rw凭据的补充核验

用户再次提供同一collab-rw后，已直接用它向D仓上传原有8×8校准图，PUT返回201，提交3e84ade68d5f9a74063df39385239c142fad8573。这证明该会话凭据能写D；不能把上次Actions中注入凭据的403解释为它没有D仓Contents写权限。它可以直接用作FRAME_HOST_TOKEN，无须另找一枚不同的图床token。

但同一凭据访问A仓Get repository public key和List repository secrets仍403，响应头要求secrets=read。管理Repository Secrets是独立权限，Actions:write不包含它。当前并未新增或修改任何Actions Secret。

继续路径：用户可直接把同一token保存到A仓名为FRAME_HOST_TOKEN的Repository Secret；或者为当前token补充Secrets: Read and write后，由Codex完成保存。无需再次把值贴入聊天。三分钟生成仍未启动；配置成功后再启动新的验收nonce。逐项HTTP回执见[权限核验记录](CODEX_TOKEN_PERMISSION_CHECK_20261023.json)。
