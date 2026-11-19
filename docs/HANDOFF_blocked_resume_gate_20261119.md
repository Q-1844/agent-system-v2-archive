# HANDOFF 修复续跑链接通 blocked 终态（9434d27）2026-11-19

## 事件链（anime750s-20261116a，四层洋葱取证）
1. run 343/344/345：Producer 修复生效（c09 改 keyframes+重排 s03）但撞「修复重排 × 旧末帧不托管」死锁 → CP-Heal 修复（8a5ae3b，CI 三闸绿）
2. run 346（23:11 北京哨兵自动派）：43 秒死于「native FullRun is not safely resumable」——run 345 的 FullRun 落 blocked（EXTERNAL_SOURCE_CHANGED），放行集 {failed,paused,pausing} 不含 blocked → **PR#59 修复续跑链（technical_wait→唤醒→接续）死在恢复门口自锁**，CP-Heal 根本没机会触发
3. 修复（9434d27）：blocked 与 failed 同级放行（源 run 已终态=无活控制器；对账/收据纪律照常；阻塞原因由恢复后的 CP-Heal 与修复循环消化，恢复验证自身拒绝真结构异常）

## 防回退
tests/relstore/test_finalize_only_resume.py::test_repair_blocked_fullrun_is_resumable——红了先怀疑自己改了不该改的。

## 用户拍板（2026-11-19 09:28）
搞笑对白番本体可弃（「删除也行」），继续做完亦可；核心目标是**系统稳定运行**。本轮两个修复（CP-Heal + blocked 放行）是修复链闭环的最后两环：修复重排→blocked→接续→补挂→Producer 循环修订。哨兵守 CI 三闸全绿后自动派 resume 346 实弹验证全链。

## 后续 agent 警告
- blocked 放行不等于无条件信任：恢复验证（manifest 对账/结构校验/paid-retry 纪律）仍然全量执行，只放行「死控制器+账面可对」的形态
- real720s-20261117T094444Z 已 COMPLETE（88 镜/2 hops）正常收官，可交付
