# Claude Code：协作修复 R1.1 本机回装与验收

你接手的是已经修改且经过离线测试的源码补丁。请直接执行回装准备和隔离验收，不消耗真实视频/图片配额。用户已授权修复；遇到源码冲突时停止覆盖并说明具体文件，不需要为普通只读检查反复确认。

## A. 先确认基线

1. 阅读本包 00、01、03 文档和 PATCH_MANIFEST.json。尚未安装 R1 时使用根目录安装器；已经安装 R1 时使用 upgrade_from_R1 安装器，勿混用两种基线。找到本机实际源码根目录，确认 api_server.py、src、tests；查看本地 AGENTS/CLAUDE 指令。
2. 记录本机分支、提交与工作区差异，不 reset、不清理用户修改。补丁基线为子仓库 feat/phase55-collab-parallel@82e305019f37a089f6499504954b5abfc4a4cb9b 加交接包原有工作区修改；不能只按提交号判断。
3. 运行 apply_patch.py 默认预检查。文件哈希不一致时进行三方人工合并，参考交接包原始文件与 changes.patch；不得跳过检查后整体覆盖。

## B. 在隔离副本中回装

1. 将代码复制到独立临时目录，不带真实项目、.env、真实队列和媒体；不共享线上 projects/data/cache 路径。测试环境禁用外网并使用 Fake Provider。
2. 对该副本执行预检查和 --apply，记录 backup。安装器不安装新依赖，本批运行代码未新增第三方依赖；使用原项目环境并单独补齐测试工具即可。
3. 执行新增安全测试，示例：

```powershell
python -m pytest tests/test_collab_safety_revision.py -q --timeout=60
```

4. 编译前端并运行项目规定的类型检查。交付方只检查过修改组件的 SFC 编译，所以本机应补完整构建。
5. 在无旧项目数据的新副本中，单独运行两个恢复测试：

```powershell
python -m pytest tests/test_project_autopilot.py::test_case4_recover_rebinds_child tests/test_full_project_autopilot.py::test_case7_production_child_crash_rebind -q --timeout=60
```

6. 再执行项目既定回归。若复现 child 数量差异，逐个记录 child 的 run_id、parent_project_run_id/parent_full_run_id、scene_id、创建时间以及 fixture 清理和后台任务生命周期。查明是同父重复创建还是跨测试残留，先保留原断言，不以修改期望数量消除失败。
7. 可用 validation/run_offline.py 对独立副本生成逐用例证据。示例（在补丁目录运行，参数路径按实际替换）：

```powershell
python validation/run_offline.py "D:\isolated\animation-storyboard" "D:\isolated\evidence\local" tests/ -q --tb=short --timeout=60
```

它只拦截当前 Python 主进程网络，必须另配操作系统级外网隔离。不要在真实项目目录运行全量测试。超时不同的结果不能只按总数与交付证据比较，需按 nodeid 和阶段核对。

## C. 本机验收重点

新增审查用例还覆盖：审核最终读盘失败、缓存命中后输入改变、先审完的镜头在其他镜头审核期间变化、提交前修改输入、提交/下载中切换选版、精确 Provider ID 恢复、保留原来源与基线，以及阻止已拒绝挂接/取消结果自动恢复。

- 两个并发更新不丢字段；旧项目快照保存报冲突。
- 同一个视频回调多次到达，不抢回 final_video；每个新版本文件独立。
- 下载过程中改变输入，旧产物留存但不挂接。
- 提交超时且无 ID 时不自动重发；有 ID 时只恢复原任务。
- 审核缺帧/超时/版本切换时不通过；任务执行期间审核可并发；最后阶段复用有效回执。
- 失败/取消/无新版本的修复不审核旧视频；身份错误提出策略决策。
- 队列损坏不清空，取消窗口可恢复，租约缺失/代际过时拒绝。
- UI 显示“执行结束，仍有问题”；完成状态不等于用户验收。

## D. 正式目录与回报

隔离验证完成后，停止正式后端、保留运行状态备份，再按 00 文档应用。若尚有未解释的新回归，保持修复分支可审查，不以正式启动代替验收。回报：文件差异、安装器结果、测试命令及环境、逐用例新增/消失失败、恢复差异结论、是否已应用正式目录和实际备份位置。

本批不要自行扩大到子 Producer 的真实执行或提高 Provider 并发。下一批按 01 文档单独实现过渡池、提交协调器和子 Producer 工具域；保持用户已认可的大权限目标，不把 decision_requests 元数据误写成已完成的子 Producer。
