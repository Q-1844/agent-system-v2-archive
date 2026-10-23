# 现有 GitHub 视频运行链整理与修复（2026-10-23）

> 后续部署与三分钟真实验收的当前状态见 [三分钟验收报告](CODEX_LONG_FILM_ACCEPTANCE_20261023.md)。PR #1已获用户批准并合入；以下为首轮复核原始记录，保留其当时的时间、提交与测试证据。

本轮按用户最新要求，优先修复和核实既有系统。Producer 自主工具、新素材体系、预览页和新任务入口留在后续设计；未把这些设想变成新的项目规则。

**首轮复核当时的部署状态（历史记录）：修复提交 `a929e758903b17a6d46f3ea4865a11edf5f8570d` 在 [PR #1](https://github.com/Q-1844/agent-system-v2/pull/1) 中待审；默认分支仍为 `061735c`。自动审批拒绝了默认分支更新，本轮没有合入。下面的修复说明指 PR 中的代码。**

## 1. 核实的范围

- A 仓审查基线：`061735c28a4f2c77850e28a60a5959e1377ece93`，默认分支 `chore/migration-readiness`。
- C 仓三份交接文档已读；指定两次真实运行的状态与事件类型均已通过 GitHub API 核实。
- 原始真实生成运行：[39961036358](https://github.com/Q-1844/agent-system-v2/actions/runs/39961036358)，`workflow_dispatch/success`。
- 原始巡检运行：[39962609983](https://github.com/Q-1844/agent-system-v2/actions/runs/39962609983)，`workflow_dispatch/success`。
- B 仓资产 `669214514` 已重新下载：1,954,214 字节；SHA256 为 `102b5a8acfbef74ab6d8a701c65d100397f83b184b1cdaec4eb76500d5b56523`，与交接报告一致。
- 原 MP4 已使用 FFprobe 核实为 5.184 秒、H.264、1280×720、AAC，并通过 FFmpeg 完整解码（退出码 0）。
- B1 `demo1` 状态文件已重新读取，blob SHA 为 `7e1ca53efe79afd37e7f2a9d262c575b97683edb`，记录是 `VERIFIED_RESTORABLE`。

已验证的云端生产仍然是 `tools/e2e_autonomous_run.py` 单段 t2v 路径。它没有经过完整的 Director → Planner → 多 SceneRun → composition 链。单段视频的归档可恢复状态也不能代替完整项目的可恢复性验收。每个 E2E 分支中的单项目 Registry 不等于全局六个活跃项目的调度已在云端验证。

## 2. 实际修复

| 原问题 | 本轮处理 |
| --- | --- |
| 只要 B1 state.json 存在就跳过任务 | 验证本任务 project_id、终态、SHA、快照指纹、B 仓和资产引用、字节数、依赖缺口 |
| 403/429/5xx 等读取失败可能被当成不存在 | 读取错误停止本任务，不能授权付费生成 |
| 生产失败仍返回退出码 0 | 文件异常、超时、非零子进程退出、回执异常均使巡检返回非零 |
| 共用 summary.json 可能把上一任务的 PASS 当成本任务结果 | 独立任务目录；执行前清理旧回执；复查 nonce、退出码和 B1 权威终态 |
| 重跑先重新生成，再发现 B1 分支已存在 | 在付费提交前保存 B1 CAS 检查点；已知 video_id 可接续查询、下载、保存和登记 |
| 提交回执丢失后可能重复付费 | durable SUBMITTING 意图保留；没有可确认 ID 时停止自动重发，等待对账 |
| B 已保存但 B1 中断不能正常续接 | 复用既有 Release/同名资产；Registry operation_id 幂等；恢复后重新核算下载 SHA |
| Registry 桥忽略 expected_revision，且提交后 GET 可能采纳其他写入者的 SHA | 同时检查 revision 与 blob SHA，使用本次提交回执继续 CAS；冲突不能当成功 |
| 两条生产工作流可同时进入生成 | 共用 `video-production` concurrency group；检查点 CAS 另行保护同一 nonce |
| 巡检缺少可下载的执行证据 | 保存逐任务状态和 `patrol-summary.json`，工作流 always 上传证据 |
| Windows CI 缺少媒体/图像测试依赖 | 显式安装 FFmpeg/FFprobe，锁定 Pillow 12.3.0、NumPy 2.3.5（已核实有 CPython 3.13 Windows wheels） |
| 测试 Fake 不接受生产调用增加的 max_tokens | 更新旧 Fake 签名，保留生产审核规则与断言 |
| API 测试依赖未入仓的 `_p4_accept` 开发项目 | 3 个相关 API 用例改用临时项目夹具，独立 10 项 API 测试通过 |

同一 nonce 绑定不可变请求摘要；已绑定请求改变时拒绝继续。所有远端凭据只从运行环境或本次会话读取，未写入提交。未修改任何现有 Secret 值。

## 3. 恢复边界

| 中断位置 | 下一轮行为 |
| --- | --- |
| 付费请求发送之前 | 争取 CAS 提交权；只有成功写入 SUBMITTING 的执行者可以发请求 |
| 提交可能成功，但缺少可确认 video_id | 停止自动重发；结合 Provider 记录人工对账 |
| video_id 已持久化 | 接续同一视频任务，不重新创建 |
| 下载中断 | 根据已保存视频 ID/URL 继续获取原视频 |
| B 上传完成，B1 任一提交失败或回执丢失 | 复用同一视频和 B 资产，按 operation_id 接续 Registry |
| 旧版本中断且没有检查点，但已有 B/B1 痕迹 | 停止自动生成，保留旧资料等待对账 |
| 内容 SHA 与先前记录冲突 | 停止，不能覆盖原资产 |

这提供的是可恢复和防自动重复提交，不宣称 Provider 具备 exactly-once 或跨仓库分布式事务。旧版本在没有留下任何持久痕迹前中断的付费请求，无法仅凭 GitHub 推断是否已被受理。

## 4. 验证记录

[机器可读证据](CODEX_RUNTIME_TEST_EVIDENCE_20261023.json) 包含逐节点结果和源码哈希。30 个最终修改文件均已与远端 Git blob 逐字节核对，全部一致。

| 环境与范围 | 通过 | 失败 | 前置错误 | 跳过 |
| --- | ---: | ---: | ---: | ---: |
| Linux 原始基线（061735c） | 2825 | 85 | 205 | 10 |
| Linux 中间修复版完整回归 | 3134 | 18 | 0 | 10 |
| Linux 最新恢复与 API 专项 | 325 | 0 | 0 | 10 |
| Windows 首版修复 CI（8172de5） | 3037 | 90 | 26 | 10 |
| Windows 最终完整 CI（a929e75，PR 与 push 两轮一致） | 3162 | 0 | 0 | 10 |

第一轮 Linux 剩余的 18 个失败节点均存在于原始基线，逐节点差集为空。随后已逐项完成定向修复和复测，包括：

- API 临时项目夹具；Vision Fake 的 max_tokens 参数；每次新提交对应独立 Provider ID。
- 尾帧接力测试准备真实 binding 与来源版本；首帧同步测试先附加并选中目标版本，保留生产选版保护。
- Native AV 测试隔离独立的人数约束开关；旧视频夹具改用符合当前 4 秒下限、无 negative_prompt 的参数。
- skill 断言校准到仓库当前 1.6.1；不修改 skill 实体。
- 完整项目恢复用例按同一 parent FullRun 验证唯一 child，并断言重新绑定原 ID。

最新专项为 325 passed/10 skipped，图像与 provenance 专项另有 13 passed。完整回归与专项有用例重叠，不把它们相加冒充独立测试数。上述均使用 Fake Provider；relstore 测试会话封锁外网 socket/DNS。没有通过删除失败用例或放宽生产审核来获得通过。

本机末轮完整回归遇到执行环境连接中断，没有终态结果，不计入完整通过数。随后我的 stdin 包装器启动方式造成 spawn 子进程无法导入 `<stdin>`，租约用例报队列超时；该启动问题已独立复现。该非标准包装器全量记录最终为 3161 passed、1 failed、10 skipped、0 errors，唯一失败就是无法导入 `<stdin>` 的跨进程租约用例；不将这个包装器结果当作正式源码验收。改用标准 `python -m pytest tests/test_collab_safety_revision.py::test_lease_cross_process_unique_holder -q` 后为 1 passed。没有修改租约逻辑或放宽断言。

最终验收使用标准入口运行的两轮 GitHub CI：每轮完整回归均为 3162 passed、10 skipped、0 failed、0 errors；运行恢复专项为 315 passed、10 skipped，Agent 冒烟为 28 passed。两轮均全部成功：

- [PR CI 39978055917](https://github.com/Q-1844/agent-system-v2/actions/runs/39978055917)
- [push CI 39978050453](https://github.com/Q-1844/agent-system-v2/actions/runs/39978050453)

云端已有任务去重验证两次成功，均为 demo1，零新增生成：

- [39973691508](https://github.com/Q-1844/agent-system-v2/actions/runs/39973691508)：summary 为 PASS/deduplicated=true。旧工作流安装 FFmpeg 从 14:55:06Z 到 15:05:27Z，约 10 分 20 秒；实际去重读取在同一秒完成。
- [39976409645](https://github.com/Q-1844/agent-system-v2/actions/runs/39976409645)：新只读预检返回 needs_media=false，跳过媒体安装；15:13:39Z 开始、15:13:40Z 完成去重。这里验证的是去重和安装路径，不把这个差异当作整条视频制作链的提速倍率。

## 5. 定时触发的判定

PR 中准备从演示用 `*/10` 改为 `7,27,47 * * * *`（UTC，每 20 分钟）。两条生产工作流共用并发组，runner 使用稀疏检出。空队列和已完成任务先做只读检查，省去媒体安装。上述修改尚未合入默认分支，线上仍是原有 cron。

GitHub 官方说明 schedule 可能延迟，负载高时部分排队任务可能被丢弃；它只在默认分支运行。错开整点可以降低部分负载风险，不能保证准点运行。一次 `event=schedule` 成功巡检只证明实际触发发生过，不证明长期调度 SLA。

[GitHub schedule 官方文档](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

本轮最近的 API 查询仍为 event=schedule 的 total_count=0，狭义单段基线保留 3/4。原因尚未确诊，不能只用“可能抖动”替代实际触发证据。

在 API 中尚未观察到 schedule run 时，继续保留该项未验证；手动 dispatch 不充当定时触发证据。

## 6. 仓库与接手

A 仓当前树有 3,179 个文件，文件逻辑字节合计 1,385,937,810；包含大量历史 MP4/图片。这个数字不是 Git pack 体积或运行内存。运行工作流先通过稀疏检出降低工作区素材负担；本轮保留历史证据，不重写 Git 历史。

已有本地分支与远端发生分叉时，先核对并保留未提交修改和分支。推荐从远端基线新建 worktree；交接文档中原先无条件执行 `reset --hard` 的建议应停止沿用。

完整项目云端真实验收、真实任务来源、使用生命周期、预览页和跨仓素材闭环仍是后续项目。它们与本轮运行恢复修复分别验收。
