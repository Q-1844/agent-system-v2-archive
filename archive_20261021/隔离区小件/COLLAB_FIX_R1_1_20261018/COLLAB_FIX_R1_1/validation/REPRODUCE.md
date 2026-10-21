# R1.1 验证说明

所有测试只对独立代码副本执行，禁用真实凭据并隔离外网。Windows 环境请使用项目已有环境，另外安装 pytest、pytest-asyncio、pytest-timeout；测试环境版本见 TEST_ENVIRONMENT.json，本包没有更新生产依赖。

## 相关回归（122 passed）

在独立项目源码根目录运行：

```powershell
python -m pytest tests/test_collab_safety_revision.py tests/test_p55_recovery.py tests/test_p56_a_mechanism.py tests/test_p39e_trace_hints.py tests/test_ai_6f_real_pipeline.py tests/test_ai_6f_shutdown.py -q --tb=short --timeout=45
```

其中 test_collab_safety_revision.py 展开参数后共 43 个用例。前端 SFC 编译记录是沿用 R1 的检查：R1.1 没有继续修改 Vue 组件；它不等于本机完整构建。

## 全量对照

分别从原交接包重新解压，建立一个原始基线副本和一个应用 R1.1 的副本，各自单独保留 projects/output/data 等运行目录。以同一套依赖运行：

```powershell
python "补丁完整路径\validation\run_offline.py" "独立项目源码目录" "证据目录\前缀" tests/ -q --tb=short --disable-warnings --timeout=10
```

交付方的 10 秒是受限离线对照时限，不是所有 E2E 用例合理的业务时限。该结果不能当生产验收；本机可另以更合理时限运行，需按 nodeid 及阶段比较。

run_offline.py 的网络拦截仅覆盖 pytest 主进程，子进程仍须使用系统级隔离。该脚本设置的 WF_STARTUP_RECOVERY_DISABLE 只覆盖项目已有的部分恢复入口；旧 Autopilot 恢复入口仍可能运行，所以不要复用前一轮生成的项目目录。

## 恢复差异复查（3 passed）

使用再次从原交接包解压并应用 R1.1 的新副本，不带全量运行遗留目录。运行：

```powershell
python -m pytest tests/test_project_autopilot.py::test_case4_recover_rebinds_child tests/test_project_autopilot.py::test_case6_run_consistency tests/test_full_project_autopilot.py::test_case7_production_child_crash_rebind -q --tb=short --timeout=60
```

该复查不替代对全量超时与测试状态相互影响的调查，也没有修改三个测试的断言。

## 效率模拟

在应用 R1.1 的独立项目根目录运行：

```powershell
python "补丁完整路径\validation\benchmark_review_overlap.py" "本机输出路径\benchmark.json"
```

实际审核调度代码参与运行，视觉与帧提取为假实现，固定延迟按脚本参数设置。共 6 镜头、3 帧/镜，三个模式各重复 3 次。结果只是软件调度实验，不能外推真实生成服务的吞吐量或成本。

## 证据分组

- review_baseline_final.* / review_r11_final.*：本次干净基线、最终代码的有效全量记录。
- review_final_comparison.json：逐节点失败差异、测试节点增减和事件完整性。
- review_r11_recovery_recheck.*：干净目录 60 秒时限的三用例复查。
- review_r11_targeted.log：122 项相关回归。
- review_r11_installer.json / review_r11_upgrade.json：完整安装器及增量升级/回滚。
- review_r11_benchmark.json：效率模拟每次采样和中位数。
- review_r11_integrity.json：原始源码逐文件检查，以及最终源码/交付文件一致性。
- full_baseline.* / full_final.* 等未带 review 前缀的文件：R1 首轮历史记录，仅供追溯，最新结论以 review 前缀文件为准。
