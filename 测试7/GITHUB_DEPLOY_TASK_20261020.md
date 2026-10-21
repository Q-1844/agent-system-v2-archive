# GitHub 仓库部署任务卡（2026-10-20，四仓定版·公开仓·Pages 全开）

## 架构（用户定版）

| 仓 | GitHub 名字 | 可见性 | 内容 | 来源 |
|---|---|---|---|---|
| A 主代码仓 | `agent-system-v2` | Public | 纯代码+测试；大视频/缓存/依赖/.env/活数据库**不进** | 子仓 animation-storyboard（全分支+12 tags+da123e2/fecfd5f） |
| B 运行数据/产物仓 | `agent-system-v2-rundata` | Public | 账本导出、run 快照导出、恢复包、成片/候选视频；**运行中 SQLite 永不进仓** | 新整理 |
| C 杂物/档案仓 | `agent-system-v2-archive` | Public | 测试1-7 报告、交接包、反馈材料（reference/ 216M 第三方克隆不进） | 父仓 ai工作流 |
| D 图床仓 | agnes-frame-host | Public（已有） | 维持原用途 | 无需新建 |

每仓开通 **GitHub Pages**（`https://用户名.github.io/仓库名/`）——预览页/看片页/任意 HTML 随时可挂，灵活变通用。

## 安全闸结论（10-20 全历史扫描，已完结）

- .env 从未入史 ✓；config.yaml 全 `${ENV_VAR}` 占位符 ✓；HEAD 0 密钥 ✓；交接 zip 0 密钥 ✓
- 子仓历史含 1 枚 Agnes key（sk-jC7GlV***）——**用户裁定：该 key 便宜泄露无所谓，不轮换不追提**；公开仓保持 `${AGNES_API_KEY}` 引用形态，真值只在本地 .env
- 真名路径串 67+2 文件=已知接受
- **公开推送无任何前置条件。**

## 用户操作（详细步骤已单独给出，摘要）

1. 建 3 个 Public 空仓（名字如上表；初始化勾选框**全不勾**）
2. 建 fine-grained PAT `collab-rw`（90 天）：Repository access 选 **All repositories**（覆盖全部仓含 agnes-frame-host 与未来新仓）；权限 **Contents / Pull requests / Pages = Read and write**；token 写入 `C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard\.env` 的 `GITHUB_TOKEN=`（覆盖旧值）
3. 回传 3 个仓库 URL

## 用户回传 URL 后我接手

1. **A ← animation-storyboard**：skill 1.6.1 单独提交（GPT §2 建议）→ 配 remote → 推送全部分支+12 tags → 设默认分支（da123e2 所在线）。⚠️ pack 1.02GB，首推 10–60 分钟，分步汇报。
2. **C ← ai工作流**：整理提交 测试1-7 报告/交接/反馈材料（排除 reference/、大视频）→ 推送。
3. **B ← 新整理**：首批=账本导出+关键成片/候选+run 快照（脱敏口径）；单文件 >100MB 不进；活 SQLite 留本地。
4. **三仓 Pages**：各推一个起始 index.html 后用 PAT 的 Pages 权限经 API 开通（无需用户点击）。
5. 产出**《GPT 接入说明》**（仓地址+分支约定+PAT 用法+Pages 网址+恢复后第一批任务）交用户转 GPT。

## GPT 恢复日第一批任务（预告）

1. 补发 COLLAB_REPAIR 缺失的 81 文件（截断证据+清单待打包成反馈包）。
2. 按 03 文档 §2：从 `da123e2` 建 production-p1 修复分支、从 `fecfd5f` 建 r2-p2 实验分支 → 本机回归 → 提交到 A 仓。
3. §4 优先顺序逐项推进。

## 分工（定版）

- **GPT**（配额恢复后）：代码修改（A 仓分支打补丁/实现+回归+提交）、补发缺件、审查。
- **执行侧 Claude**：push/merge、本机回归、B 仓归档、Pages 维护、报告与证据（C 仓）。
- **您**：建仓/PAT、看片验收、裁决。
