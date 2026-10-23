> 最新状态：run 39998736879于17:54:46Z记为FAILED，0图片/0视频；下文早期RUNNING快照仅保留历史。修复分支collab/full-project-preparation-20261023，PR #5。

# GitHub当前运行态（2026-10-23）

**当前部署：PR #1–#4已合入默认分支。真实长片39998736879已在文本规划阶段停止：启动恢复重复派发同一FullRun，触发外部变更保护。图床新Secret与FFmpeg已通过；4次文本、0图片、0视频。PR #5修复控制器重复派发，当前待CI，暂不等待长片完成。**

最新修复、测试与真实运行状态见 [CODEX_RUNTIME_BOOTSTRAP_LOCK_FIX_20261023.md](CODEX_RUNTIME_BOOTSTRAP_LOCK_FIX_20261023.md)。

- PR #1巡检与恢复、#2三分钟验收及旧任务暂停、#3真实图床写权限预检、#4环境安装和Windows锁修复均已合入。
- FRAME_HOST_TOKEN已由用户创建保存。新runner已通过每次新内容地址的图床上传与公网就绪预检，随后进入原制作链。
- 真实运行nonce=film3m-20261023-rescue4；当前阶段=['Real FullProject → Director/Planner → SceneRuns → >=180s final film → restore verification']；视频提交=0；最终成片尚未验收。
- 前次39994958081仅FFmpeg安装超时，媒体步骤skipped，未调用Agnes；新nonce不会重复该次媒体消耗。

| CI运行 | 完整Mock回归 | 存储/恢复专项 | Agent冒烟 | Linux媒体工具 |
| --- | --- | --- | --- | --- |
| [39997455184](https://github.com/Q-1844/agent-system-v2/actions/runs/39997455184) | 3192通过、10跳过 | 343通过、10跳过 | 28通过、0跳过 | 下载/SHA/编码/探测/解码通过 |
| [39997447886](https://github.com/Q-1844/agent-system-v2/actions/runs/39997447886) | 3192通过、10跳过 | 343通过、10跳过 | 28通过、0跳过 | 下载/SHA/编码/探测/解码通过 |


本机最终专项388通过、10跳过。首次全量3项失败及定向复核已在最新报告如实区分；不能把它写成本机全绿。

原单段39961036358和手动patrol39962609983成功；部署后零生成巡检39991006999成功。原成片5.184秒/H.264/1280×720、1,954,214字节、SHA256 102b5a8acfbef74ab6d8a701c65d100397f83b184b1cdaec4eb76500d5b56523，仍只证明单段路径。

schedule最近仍无实触发证据；继续保留未验证。新Producer能力和预览页等扩展后置。
