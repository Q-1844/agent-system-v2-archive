# Codex 接手入口（2026-10-23，继续整顿）

> 补充核验：会话中的collab-rw已成功写入D（201），可以直接用作FRAME_HOST_TOKEN；目前缺的是把它存入A仓Actions Secret的管理权限（Secrets API 403）。无需另外寻找图床token，详见[权限回执](CODEX_TOKEN_PERMISSION_CHECK_20261023.json)。

**部署更新：PR #1与PR #2均已合入默认分支`chore/migration-readiness`；当前合并提交`8f81b677e41082118cf7433e5278883c34fb5064`。最终源码`f77f4aa`的两轮完整CI均成功。三分钟真实验收仍被D图床凭据403阻塞，尚未生成成片。**

先读[三分钟真实验收与阻塞报告](CODEX_LONG_FILM_ACCEPTANCE_20261023.md)，再读[GITHUB_RUNTIME_STATUS.md](GITHUB_RUNTIME_STATUS.md)。首轮[运行链修复报告](CODEX_RUNTIME_REVIEW_20261023.md)及[GITHUB_AUTONOMY_E2E_REPORT.md](GITHUB_AUTONOMY_E2E_REPORT.md)保留历史证据，不能用其中“待合入”的历史状态覆盖当前部署事实。

## 当前决策与下一步

- 用户已批准整顿和合入现有系统修复；任何真实视频验收成片至少180秒。
- Producer新工具、预览页、跨仓素材扩展和新任务来源继续后置。
- PR #1已合入；PR #2已合入，旧5秒demo2保留且enabled=false。
- 长片测试使用原FullProject/Director/Planner/SceneRun/合成链，视频提交预算240秒、规划约200秒、最终视频流至少180秒；完整真实长片尚未通过。
- 当前阻塞：A仓Actions Secret FRAME_HOST_TOKEN需要能够写入D仓的Contents:write凭据。现有云端写入D返回403；当前会话也没有A仓Secrets管理权限。应在GitHub设置页修复，凭据值不要入仓或贴入聊天。
- 配置完成后用默认分支的video-autoproduction-e2e手动启动full-project-3min，task_nonce留空。不要盲目重跑可能已有付费提交的旧nonce。
- event=schedule最近查询仍为0，继续单独保留未验证；手动运行不算定时触发。

## 仓库职责

| 仓库 | 默认分支 | 职责 |
| --- | --- | --- |
| Q-1844/agent-system-v2（A） | chore/migration-readiness | 代码、测试、调度、验收驱动 |
| Q-1844/agent-system-v2-rundata（B） | main | Release成品与完整项目归档 |
| Q-1844/agent-system-v2-rundata-1（B1） | main | Registry与运行检查点；当前验收使用隔离test/e2e-*分支 |
| Q-1844/agent-system-v2-archive（C） | main | 报告；当前交接在feat/codex-handoff-20261023 |
| Q-1844/agnes-frame-host（D） | main | 公网图片参考托管 |

## 凭据名称与验证边界

A仓Secrets：AGNES_API_KEY、B1_ARCHIVE_TOKEN、FRAME_HOST_TOKEN。B/B1归档凭据不再隐式当作D图床凭据。只记录名称，不记录值。

原真实5.184秒t2v成片、B Release保存与B1 VERIFIED_RESTORABLE已由原字节与SHA复核；它不是本轮三分钟完整制作验收。Mock绿色也不是实际视频成功。

本轮九个修改文件已与远端Git blob逐字节核对，结果和CI记录见[机器证据](CODEX_LONG_FILM_TEST_EVIDENCE_20261023.json)。

本地接手先fetch并保留分叉和未提交修改，尤其已有skill改动；使用独立worktree，不无条件reset --hard。
