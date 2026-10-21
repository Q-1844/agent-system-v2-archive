# 视频生成能力事实表（按日期维护——生成前必读，判断用 SKILL.md，事实用本表）

> 维护纪律：本表只记【带来源与日期的事实】，不写操作规则；每次真实调用/官方
> 公告变化后更新对应行。任何空白写"未确认"。六状态含义：
> 设计可选（本系统架构有此概念）/ 官方支持（provider 文档）/ 本地编译可用
> （本仓库编译器+client 实际能发出的请求）/ 最近服务端成功（真实调用回执）/
> 视觉已验证（人工/工具看过成片帧）/ 项目资产已批准（Look/SIV/版本选中）。

## 模型与服务状态

| 事实 | 状态 | 日期 | 来源 |
|---|---|---|---|
| `agnes-video-v2.0` 官方公告下线（迁移至 2.5 系列） | 已证实（公告） | 2026-09-25 23:59:59 UTC+8 | wiki.agnes-ai.com/zh-Hans/docs/agnes-video-v20（2026-09-27 核读） |
| v2.0 实际仍受理并出片 | 已证实（真实回执） | 2026-09-27 | expB `vv_6e26ffbc` URL `…/videos/agnes-video-v2.0/video_d2266f81….mp4` |
| v2.0 持续可用性 | **未确认** | — | 公告与实测并存；每次付费生成前先小样核验 |
| `agnes-video-2.5-flash` /v1/models 存在；text/keyframe 模式实测出片 | 已证实 | 2026-09-06 | `_video25_probe/`（smoke.log、v25.*.json） |
| 2.5 双帧 keyframes（首+尾）契约 | 未验证（勿发） | 2026-09-06 | FACTS §3.0；本地 `_video25_mode` 显式拒绝 |
| 2.5 reference 模式：≤8 图（单图<15MB、请求<50MB、媒体总数≤12），与 keyframe 的 first_frame/last_frame 互斥；**参考不锁首帧**（may recompose） | 已证实（官方文档） | 2026-09-27 核读 | wiki.agnes-ai.com/en/docs/agnes-video-25 |
| 2.5 reference 本地编译 | **未实现**（`_video25_mode` 对非 t2v/i2v 显式 raise） | 2026-09-27 核对 | src/api/agnes_client.py:544-568 |
| 图片 i2i：`extra_body.image` 数组，本仓库 cap=6 张（URL 或 data URI） | 已证实 | 长期 | AGNES_API_FACTS §2；image_adapter MAX_PROVIDER_INPUT_IMAGES |

## 路径能力表

| 路径 | 设计可选 | 官方支持 | 本地编译可用 | 最近服务端成功 | 视觉已验证 | 项目资产已批准 |
|---|---|---|---|---|---|---|
| v2.0 i2v（首帧硬边界，顶层 `image`） | 是 | 是 | 是 | 是（P40A 全部存量，最近 2026-09-27 expB） | 是（expB 融合首帧起步） | Look/SIV 已批（P40A 2026-09-26/27） |
| v2.0 keyframes（`extra_body.image=[first,last]`+mode） | 是 | 是 | 是 | 是（P40A s03_c02 实验版等） | 部分（s03_c02 CU 未达成为负例） | 同上 |
| v2.0 multi 单语义参考（`extra_body.image=[1张]`；服务端 ti2vid 上限 1 张） | 是 | 是（勘误后口径） | 是（恰好 1 张，多张结构化拒绝） | 是（P40A 存量 relay 链） | 是（但身份漂移=负例，2026-09-26/27 目检） | Look 已批但**未进**这些请求 |
| v2.0 双参考（Look+尾帧同发） | 是 | 否（ti2vid 1 图上限，2 张 400） | 否（编译层拒绝） | 否（400，32.md X005） | — | — |
| 2.5 keyframe（顶层 `image`+seconds） | 是 | 是 | 是（显式选模型） | 是（2026-09-06 探针） | 未（正式镜头未用） | — |
| 2.5 reference 多图 | 是 | 是（≤8 图，不锁首帧） | **否（未实现）** | 否 | 否 | — |
| keyframes 桥（`shot.bridge_create`：首=锚点尾帧，尾=后继首帧） | 是 | 是 | 是 | 是（38 桥实证） | 部分（桥帧检纪律成档） | 端点须逐案批 |
| 融合首帧起步（Look+尾帧经图片 i2i 合成新首帧→i2v） | 是 | 是（图片接口） | 是（BOUND reference_previous 链路） | 是（2026-09-27） | **是（正例：身份/景别/动作显著优于裸尾帧接力；已知瑕疵=结尾提前触水、末帧颈前偏粉）** | 实验候选（expB），**未正式选片** |
| inherit_previous（来源真实末帧直接作视频首帧） | 是 | 是 | 是 | 是（历史项目） | 部分 | 逐案 |

## 本仓库关键守卫（2026-09-27 起）

- `_resolve_boundary_frame`：首帧槽批次带 `slot_semantics=multi_reference_only`（multi 接力同步产物）→ i2v/keyframes 消费被 `first_frame_slot_not_hard_boundary` 结构化拒绝（routers/shots 写标记，video_adapter 拦截）。
- `resolve_multi_relay_source`：跨段接力返回 `cross_segment=true` → 诊断 `prev_tail_cross_segment_relay` + 进 visual basis 指纹（组首 prev_tail 残留不再静默）。
- `_extract_video_end_frame`：末帧文件名带来源版本 id（`{shot_id}_video_end_{version_id}.jpg`），重提取不再覆盖旧字节。
- BOUND 首帧批次 `generation_basis.continuity_tail` 记录实际发送的尾帧身份（source_shot_id/end_source_version/url）。
