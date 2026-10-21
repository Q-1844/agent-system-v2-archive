# 本机取消修复 R1.1.1：collab_modes.save_run 终态保护

日期：2026-10-18（Asia/Shanghai 晚）。性质：执行侧自修，经用户口头批准回装；本包供补丁作者复核。
正式目录现应记作：**R1.1 + 本机取消修复（R1.1.1）**。

## 问题（A3 集成驱动实证复现）

取消落在 producer turn 执行中时：`cancel_run` 落盘 `cancelled` → 执行侧内存 run 快照（仍
`running`）在后续 `save_run` 中整本覆盖盘上状态 → run 最终被标 `completed`——用户取消被
静默复活。复现链：集成驱动 F4（取消确认 cancelled）→ F7（盘上重查变 completed）。
根因：`save_run` 无条件原子覆盖，执行长流程与盘上状态无 CAS。

## 修复内容（单 hunk，src/agents/collab_modes.py）

`save_run` 写入前读盘上现态：若为终态（`cancelled / completed / completed_with_issues /
failed`）且与内存态不同 → 保留盘上终态（连同 `finished_at`/`result`），仅随本次写入合并
步骤/结果增量；终态→终态改写同样不允许。读旧态失败时按原行为写入（不新增故障面）。
不变量：**终态只进不出；状态机不得被陈旧内存快照逆转。**

## 验证

- A3 集成驱动（真实路由+假 Provider）：修复前 F7 复活复现 → 修复后 **34/34 flows passed，
  network_attempts=0**（D:\isolated\evidence\a3_integration.json）。
- 122 关键切片复跑：除既有 Windows flake（见主报告 §四.2）外无新失败。
- code-only 与隔离副本验证版逐行等同（仅注释措辞差异，注明批准来源）。

## 哈希

| 版本 | SHA256 |
|---|---|
| R1.1 交付版（修复前） | `ffc8e289e5dc59e2699fcfd780659e4cd693fb40527f762f72c14805325b90af` |
| R1.1.1 修复版（正式目录现行） | 见 `fixed_hashes.txt` |

## 包内文件

- `collab_modes_cancel_fix.diff`：R1.1 交付版 → R1.1.1 的统一差异（基线文件取自补丁包
  `changed_files/src/agents/collab_modes.py`）。
- `collab_modes.py`：修复后完整文件（正式目录现行字节）。
- `fixed_hashes.txt`：修复版 SHA256 与来源路径。

## 回滚说明

1. 仅撤销本修复（保留 R1.1）：把 `collab_modes.py` 恢复为 R1.1 交付版
   （SHA256 `ffc8e289…`，字节见补丁包 `COLLAB_FIX_R1_1_20261018.zip` 内
   `changed_files/src/agents/collab_modes.py`），然后重启后端。
2. 连 R1.1 一起回滚：先停后端，执行
   `python apply_patch.py --project-root "<正式源码根>" --rollback "<正式源码根>\.collab_patch_backups\20261018T124333Z_c2c35c9b"`
   （注意：该备份是 R1.1 应用前状态，回滚会同时撤销 R1.1 与本修复，之后 `src/core/file_lock.py`、
   `src/generation/video_commit.py`、`tests/test_collab_safety_revision.py` 三个新增文件将由
   安装器删除）。
3. 修复无数据迁移、无接口变更；旧 run 记录兼容（只读盘上 status，不要求新字段）。
