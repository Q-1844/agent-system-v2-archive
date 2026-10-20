# G0/G1 只读清点报告（2026-10-20）

## 双基线与 refs 对账

- 生产基线：`da123e22e0b413b5118c6d87632cda72204422d7` @ `feat/phase55-collab-parallel`（tip 一致 ✓）
- R2 基线：`fecfd5f5bb90b59abb432abec4f5e166674205f2` @ `feat/r2-collab-pool`（tip 一致 ✓）
- 子仓 refs 共 **27 条**（15 heads + 12 tags），逐条 SHA 已存档 `refs_before_child.csv`（推送后据此对账）
- 父仓 refs 2 条：`master`@21df16d、`branch-NFb8kS`@877391f
  - ⚠️ **新发现 1**：`branch-NFb8kS` 是**独立历史**（cancel restart race 修复，非 master 祖先）→ 按「全部 refs 原样迁移」纪律，推 C 仓时须一并推上去

## 远端状态（实测）

- A `agent-system-v2`：空仓 ✓ ／ B `agent-system-v2-rundata`：空仓 ✓ ／ C `agent-system-v2-archive`：空仓 ✓
- D `agnes-frame-host`：`main`@`a9c26f07de331c9495d9d3138680f3cced3e2881`（只读验收基线，迁移后复测不变）

## 体积红线复核

- 全 refs 扫描：**无 >50MB 对象**（最大单 blob 25MB）→ 无 GitHub 100MB 阻断风险；pack 1020.72 MiB < 单次 push 2GiB 上限（接近 1GB 推荐线，分步推送预案在案）

## 测试体系实测（CI 基线锚点）

- **pytest 收集实测：2847 tests collected in 12.58s**（入口 `python -m pytest tests/`）——与交接包基线数字完全一致 ✓
- 本机 Python 3.13.0 → CI windows-latest 锁 Python 3.13 与本机对齐
- 网络前提：Steam++ 关闭（已实测）；Workflows 推送权限待首次 workflow 推送实测（用户已补勾）

## 工作区 1173 项拆分（4M + 393D + 776??）

### 4 个已修改文件（M）
| 文件 | 处置 |
|---|---|
| `src/agents/skill_system/builtin/full-story-relay-calibration/SKILL.md` | ✅ **skill 1.6.1**，与授权 diff（测试7/skill_v1_6_1_衔接延长授权.diff）逐文件对应 → 推送前单独提交 `chore(skill): preserve authorized v1.6.1 change` |
| `src/agents/skill_system/builtin/full-story-relay-calibration/skill.json` | ✅ 同上，同一提交 |
| `_p51_va_multiview_video.py` | ⏸ 探针脚本——GPT 03 §1 明令「探针不混成生产核心修改」→ 不随迁移提交，留本地待 G7 判定 |
| `components.d.ts` | ⏸ 前端自动生成文件 → 不随迁移提交，待 G7 判定（候选 gitignore） |

### 393 个已删 tracked（D）——全部为历史证据目录 ✓
`_video25_probe` 289 ／ `_b1_dialogue_probe` 54 ／ `_c1_native_av_e2e` 37 ／ `_phase_d2_*`+`_31_*`+`_p50_b_review` 13 → G7 以正向清理提交收编（旧历史 SHA 不变）

### 776 个未跟踪（??）——顶层分类
`_tmp` 229 ／ `_44a` 49 ／ `_37_fable` 14 ／ `_41_redo` 9 ／ `_43_blind` 7 ／ `docs` 6 ／ `_44c` 5 ／ `详细流程文件` 4 ／ `_41_repair` 3 ／ `gp_*` 探针与散件 ~15 ／ 其余长尾单件（PHASE44_D_REPORT.md 等）
→ G4/G7 前按「归 B/C 白名单 / 保留 / 删除」三分类成文，删除部分走审批

## G0/G1 结论

**全绿，无阻塞。** 具备进入 G2（C 真实历史试推）条件，等待用户授权 G2-G6+G8（非破坏性批次）。
