# HANDOFF CP-Heal 锁定末帧补挂（修复重排接力死锁）2026-11-18

## 事件
anime750s-20261116a run 343/344/345 三跳全灭：Producer 修复（PR#59）把 s03_c09 改 keyframes 并重排 s03 计划后，新计划下游需要 s03_c10 末帧接力；但 c10 完成于旧计划（下游 i2v 无需接力 → 按 2026-10-27 C2 配额决策末帧 local-only 不托管）。锁定镜不重生 + 末帧无公网 URL → preflight 永久卡 LOCKED_SOURCE_NO_VIDEO_END。real720s 同期正常收片（COMPLETE 88 镜）。

## 修复（A 仓 8a5ae3b）
routers/shots.py 新增 heal_locked_video_ends：锁定+成片+下游计划要求接力+末帧无 URL → 本地文件补 Pages 托管 / 缺文件从成品视频补提取（复用 _extract_video_end_frame 全纪律）。接入 full_project_autopilot._handoff_to_production 与 SceneAutopilot ensure 两处 preflight 前。幂等；失败不吞（preflight 继续拦截，fail-loud）。

## 防回退锚（tests/test_cp_heal.py）
补挂得 URL（run 345 s03_c10 形态）/ ready 与无需求跳过 / 缺文件不静默。

## 后续 agent 警告
1. CP-Heal 与 10-27「无下游不托管」配额决策是互补而非冲突：托管决策基于【当时】计划，计划可被修复重排改变——heal 只在「新计划要求 + 锁定不重生」时补挂，不恢复全量托管。
2. s03_c09 本体内容拒未解（修复版提示词仍拒两发）——接续跳走 Producer 修复循环第二轮属设计行为（不限次修订），勿当成死循环误修。
3. url_ready 是计算属性（status==done 且有 url），JSON 工件里没有该字段——取证读数时勿按字段读。
