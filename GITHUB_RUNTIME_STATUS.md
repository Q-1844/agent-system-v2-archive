# GitHub运行态（2026-10-23）

**部署更新：PR #1与PR #2均已合入默认分支`chore/migration-readiness`；当前合并提交`8f81b677e41082118cf7433e5278883c34fb5064`。最终源码`f77f4aa`的两轮完整CI均成功。三分钟真实验收仍被D图床凭据403阻塞，尚未生成成片。**

## 部署与绿色回归

- A默认分支：chore/migration-readiness；当前提交：8f81b677e41082118cf7433e5278883c34fb5064。
- PR #1：https://github.com/Q-1844/agent-system-v2/pull/1 ，已合入，修复巡检终态判定、失败退出码、CAS检查点及跨仓恢复。
- PR #2：https://github.com/Q-1844/agent-system-v2/pull/2 ，已合入，暂停旧短片demo2并增加至少180秒原制作链验收及保护。
- 最终源码f77f4aafc8a705888f9f32c7594c0284ffdcb8d3的两轮CI全部成功。实际run：39989582134, 39989572132。
- 本机离线恢复/存储/长片保护340 passed、10 skipped；FullProject/Project/图床相关36 passed。集合有重叠，不相加成独立用例数。
- 逐文件对账、统计与真实运行边界见[三分钟验收报告](CODEX_LONG_FILM_ACCEPTANCE_20261023.md)及其机器证据。

## 真实长片当前受阻

run [39988882623](https://github.com/Q-1844/agent-system-v2/actions/runs/39988882623)成功安装FFmpeg（17秒），随后在D图床PUT返回403后失败。发生在任何Agnes图片/视频调用之前，未生成视频，未消耗本轮Agnes生成配额。

需要在A仓Settings → Secrets and variables → Actions配置/修复FRAME_HOST_TOKEN，凭据需对Q-1844/agnes-frame-host具备Contents: Read and write。当前会话Secrets API也403，不能代填。配置完成后用新nonce启动full-project-3min；不得把失败预检当作长片已开始生产。

nonce film3m-20261023-rescue1留下STARTING记录。当前会话读到该记录，但对B1补记阻塞状态的CAS写入403，没有成功修改该记录；主程序仍拒绝对同nonce盲目重跑。完整项目自动恢复尚未验收。

## 已核实的单段历史证据

- 真实单段生产39961036358、手动巡检39962609983均success。
- 原B资产669214514：1,954,214字节；SHA256：102b5a8acfbef74ab6d8a701c65d100397f83b184b1cdaec4eb76500d5b56523；H.264、1280×720、5.184秒，完整解码通过。
- B1 demo1为VERIFIED_RESTORABLE；已有任务去重39973691508、39976409645成功，无新增生成。

## 调度与保留事项

video-patrol active，默认分支cron为7,27,47 * * * *（UTC，每20分钟）；最近查询event=schedule仍为0。Actions仓库权限enabled=true、allowed_actions=all。原因尚未确诊，不能仅用“可能抖动”作为结案证据。

完整三分钟成片、Director/Planner云端实际输出、跨场景素材一致性和完整项目归档恢复均仍待真实成功证据。人物/对白、多项目容量调度、Producer新能力、预览页及素材体系扩展不在本轮已验收范围。
