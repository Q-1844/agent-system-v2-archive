# HANDOFF 内容驳回 agent 修订机制（CP-3）2026-11-17

## 事件
anime750s-20261116a（搞笑对白番）run 336/337/338 三跳 12 发首帧候选全部 content_policy_violation 400 拒死（s03_c09 描述内嵌台词原文触发供应商过滤），两次 gateless 静默停摆各 4h+。额度墙机制全程正常（337 撞墙→设闸→00:14 自动接续均正确）。

## 用户拍板设计（三轮迭代定稿）
1. 服务端内容驳回=审核意见，与自有审片打回同类——走反馈→修订→重提
2. 不同平台限制不同，绝不写死「哪句话不能用」；不做任何提示词预限制（服务端已把关）
3. 台词是 NDC 语音对话的合法语义输入，默认批次原文保留
4. 驳回反馈交给 agent（文本模型）动态改写提示词，LLM 失败降级原样重试

被否决中间方案留档：机械剥离引语两版（fb8d181 无条件/1266ba9 参数化）均撤除——写死规则必错 + 无需预审查。

## 交付（A 仓 agent-system-v2，分支 chore/migration-readiness）
- fb8d181 → 1266ba9（三闸绿）→ 0d40113（终稿 agent 反馈修订）+ d64344d（交接文档）
- 新模块 src/ai/content_policy_revision.py；autopilot 批三带 content_policy_feedback；routers/shots 两 handler 收口；patrol gateless FAILED 红警隔离（AWAITING_HUMAN+exit 1）
- 防回退 9 测锚点（无预过滤原则/反馈必进指令/降级护栏/批三参数/红警语义）
- 完整交接文档：A 仓 docs/REVIEW_content_policy_fix_20261117.md

## 后续 agent 警告
删批三/红警前必读 A 仓交接文档第四节——CP-3 管审核驳回、quota wakeup 管额度墙，两套互补；看到「冗余重试」删掉会回到静默停摆。
