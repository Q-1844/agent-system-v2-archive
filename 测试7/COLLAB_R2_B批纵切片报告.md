# R2 B 批纵切片报告（候选过渡池 / 接纳协调器 / 确定性派发）

日期：2026-10-18 晚（Asia/Shanghai）。分支：`feat/r2-collab-pool` @ `fecfd5f`（父提交 = 生产分支 `feat/phase55-collab-parallel` @ `da123e2` = R1.1+R1.1.1）。
性质：**实验实现，全部假服务（零网络/零模型/零配额）**。生产工作区已切回 R1.1 分支并重启——B 批实验代码不进生产运行面，旧模式与在途 run 不受影响。

---

## 一、已实现（代码入口与证据）

### B0.1 项目实例身份（incarnation_id）
- `src/core/models.py`：`Project.incarnation_id` 字段 + to_dict/from_dict 序列化（旧项目缺失 → ""）。
- `src/core/store.py`：`save()` 惰性赋值一次（空时生成 `pi_<hex>`；已持久化恒定）。
- 删除后同名重建 → 不同实例（测试 `test_b01_delete_recreate_new_identity`）。

### B1 协调账本 + 候选池 + 接纳协调器（`src/agents/collab_execution/`）
- `ledger.py`（~430 行）：标准库 sqlite3；WAL + busy_timeout + 进程内写锁；表 = tasks /
  candidates / review_receipts / promotions / events；唯一键（task_id、dispatch_key UNIQUE、
  candidate_id、promotion_id、event_id）；状态 CAS（条件 from_statuses + revision 递增）；
  **终态粘性**（done/failed/cancelled 不可回退，账本级强制）；审核回执与候选三维度状态
  （execution/review/acceptance）分开；invalid_reason 哨兵区分「未提供/显式清空」。
- `promotion.py`：接纳协议 = 前置校验（候选未失效/acceptance=pending/审核回执 pass 且内容
  摘要对准产物/产物哈希重验/**项目实例双向匹配**[账本记录 + 盘上 Project 实测]/输入签名
  与当前项目重编译一致）→ 意图持久化 → 产物预备到不可变正式位（`output/formal/<promo_id>/`，
  复制+哈希校验，正式写锁外）→ committing → **Project 原子写**（`update_shot` + guard 内
  选版 CAS：`base_final_video` 不符即拒绝，不抢回用户选版；版本携带 promotion_id 标识于
  `generation_basis`）→ 账本结算 accepted + 待投递事件。
- **崩溃恢复 `recover()`**：按 promotion_id 对账——正式 JSON 已有标记 → 补结算/补事件；
  未落盘 → 重新校验幂等重做；项目读失败/实例未知 → `recovery_required`（不猜）。
  绝不先标 accepted 再写正式项目。
- `pool.py`：后代级联失效（`invalidate_cascade`，祖先失效 → 全部后代 stale 且不得接纳）、
  适用性摘要。
- 事件：`enqueue_event` / `pending_events` / `deliver_events`（handler 抛错留待重试，
  exactly-once 由 delivered 标记 + 消费方幂等键保证）。

### B2 最小确定性派发（`scheduler.py`）
- 依赖节点：无依赖登记即 ready；有依赖 waiting_dependency；**依赖满足（依赖 shot 存在
  accepted 候选）由程序推进并入现有 JobQueue——不调用 Producer/LLM**（B08 硬断言
  llm_calls=0）。
- 稳定派发键 `project_instance_id:run_id:task_id:attempt:input_signature`；账本唯一约束
  先领取（ready→queued）再投递原队列；job_id 关联落账。
- **崩溃恢复 `recover()`**：queued 无 job_id → 按 `origin_dispatch_key` 从 JobQueue 扫描
  找回（不重复制造 Job）；队列确无（投递前崩溃）→ 重新投递（首次创建语义）。
- `watch_queue`：订阅 JobQueue 广播，job 终态 → 任务状态推进（on_job_terminal 条件更新）。
- 依赖等待不占 worker 槽；派发键含实例身份。

## 二、验收矩阵覆盖（12 测试全绿，`tests/test_r2_collab_execution.py`，2.7s）

| 矩阵 | 测试 | 结果 |
|---|---|---|
| B01 身份隔离 | 删除重建不同实例；旧候选写新项目被拒（code=identity） | ✓ |
| B04 选版 CAS | 用户切选版 → 拒绝（code=selection_changed）、选版不被抢回；恢复后重新接纳成功 | ✓ |
| B05 审核闸 | 无回执/uncertain/摘要错位/产物漂移/输入漂移 五路全拒，正式项目零写入 | ✓ |
| B06 三窗口崩溃 | 意图后崩溃→恢复重做幂等；正式写后崩溃→按标记补结算；结算后事件 exactly-once | ✓ |
| B07 重复接纳 | 同 candidate 两次 promote → 同 promotion_id、单版本、单 accepted | ✓ |
| B08 程序派发 | 上游接纳→事件→下游自动入队→执行→done；**llm_calls=0** | ✓ |
| B09 派发键找回 | submit 后未存 job_id 崩溃 → 按 key 找回原 Job，队列 Job 数不增 | ✓ |
| B10 级联失效 | 祖先 stale → 三代全 stale 且拒接纳；独立分支照常接纳 | ✓ |
| 账本不变量 | CAS 条件更新 / 终态粘性 / 状态不倒退 | ✓ |

既有关键切片（122 项）在 B 批改动后复跑 **122 passed**（23.79s）——incarnation_id 向后兼容零回归。

## 三、部分完成 / 未做（如实）

**部分完成**：
- B0.3 统一 ExecutionContext：接纳入口已做身份/guard 等价校验，但**未改造为所有生产工具
  的统一上下文**（服务端解析 actor/路径/域）——C 批接线时补全。
- B0.4 已开放工具最终写权限/锁顺序审计：仅覆盖接纳入口；工具面逐个审计未做。
- B1 生产路由：候选登记/审核/接纳链目前由**假 handler 模拟 settlement**；真实 video handler
  的"执行成功、候选待审"写回接点未改造（settlement 返回候选引用未接）。
- B1 `unattached_*` 存量导入：未做。
- B2 取消传播：`on_candidates_invalidated` 仅回退未派发的 ready 节点；**已入队 Job 的真实
  取消不在本批**（D 批）。
- B2 blocked_decision 决策单：状态已定义，决策单持久化/答复唤醒未做（C 批）。

**未做（不冒充存在）**：
- REST/OpenAPI 面：候选 list/get、request_review、promote/reject、decision 等接口**均未
  注册**——本批只有 Python 层 API 与测试；`r2_pool_auto`/`r2_child_producer` 模式名**未注册**，
  collab-modes 不会返回它们。
- 预算预留（video_seconds/image_count）：账本无 budget 表（D 批）。
- 多项目调度/公平轮转/全局容量：未做（D 批）。
- C 批宽权限子 Producer / skill 执行路由：未动。
- SQLite 账本的全局实例接入 api_server 启动：未接（实验包独立构造，避免影响生产启动路径）。

## 四、运行归属与指标

- 测试进程：真实仓开发迭代（tmp_path 隔离 + WF_STARTUP_RECOVERY_DISABLE=1）+ 隔离副本全量对照（见 A 批报告）。
- Provider 调用数：**0（假 handler 计数位实证）**；网络尝试 0。
- 任务/候选/接纳归属：账本每行携带 project_instance_id + run_id（B07/D07 归属污染测试待 D 批多 run 场景）。
- 计时事件：ready_at / enqueued_at 已落账（B08 的 P95≤1s 派发目标待假服务批量实验采证）。

## 五、结论

- **B 批门槛：部分达成（passed with scope）**——B01/B04/B05/B06/B07/B08/B09/B10 假服务
  断言全过、零回归；"生成候选→审核→接纳→自动派发→崩溃恢复"最小纵向链在假服务下走通。
- 距 03 文档 B 批完整出口还差：真实 settlement 接线、unattached 导入、决策单、取消传播、
  ExecutionContext 统一——继续于 `feat/r2-collab-pool` 推进。
- "B 批纵切片已实现" ≠ "B 批验收通过" ≠ "全系统已验收"。明天真实视频测试按计划只验证
  R1.1 路径（生产分支），R2 实验组 not_implemented 如实报告。
