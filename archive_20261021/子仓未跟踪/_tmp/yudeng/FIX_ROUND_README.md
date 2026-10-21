# 修复轮执行手册（s01_c04 路径 c 样张）

## 运行

```
cd C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard
D:\Delta Force\python.exe _tmp\yudeng\fix_round_s01_c04.py            # v2.0 i2v 样张（约 4-6 分钟）
D:\Delta Force\python.exe _tmp\yudeng\fix_round_s01_c04.py --also25   # 追加 2.5 对照（再 +3-5 分钟）
```

前提：后端已运行（`start.bat`，健康检查 `http://localhost:8000/api/health`）；ffmpeg 在 PATH。
脚本幂等：可重复运行（每次 force 新批次，历史版本全部保留）。
日志：`_tmp/yudeng/fixround_log.txt`。

## 它做什么（对应 identity_audit.md 的修复方案一）

1. s01_c04 设 `opening_source=reference_previous`（来源 s01_c03，同场景 gate 允许）；
2. BOUND 融合首帧：refs = 场景 SIV + 批准 Look + 未点亮组合图 + **s01_c03 真实尾帧**（ref_layout=continuity_tail），显式 full+keep 覆盖 auto（MCU 的 auto 会丢身份参考）；
3. 自动选第一候选（想改选：`POST /api/project/雨灯归航/shot/s01_c04/first-frame/choose {"candidate_id":"<批次>_<n>"}`）；
4. 切 `link_mode=i2v` + 清 `video_reference_asset_id`（消除 i2v 上的 relay 残留）；
5. v2.0 i2v 出片（`--also25` 再加 2.5 keyframe 对照）；
6. 产物：`_tmp/yudeng/fix_strip_v20.jpg`（三联）、`fix_ab.jpg`（左=旧 relay 版 vv_0c52efca，右=新融合 i2v）。

## 验收清单（对着图看）

- 0.3s 帧 ≈ 选中融合首帧：白斑/围巾/橙色雨衣接近批准 Look（消除变体 C），空间承接 c03 尾态；
- 4s / 7.6s：身份不漂、灯为未点亮→（本镜无点亮动作，保持暗灯）；
- fix_ab.jpg：新右图是否明显更接近批准 Look（对照左图的变体 C）。

## 批量条件

样张合格 → 可按同配方批量重做漂移镜（s01_c02、s01_c04、s03_c02 为三个变体起点；彻底集 s01_c02..c06 + s03_c01..c03 共 8 镜）。
每镜成本：1 张融合首帧图 + 1 条 8s 视频（约 8s 配额）。

## 已完成并留档（无需重跑）

- 2.5 keyframe A/B（s02_c02）：`vv_b6a090d7`（2.5）vs `vv_3420c4b9`（v2.0），对照图 `_tmp/yudeng/ab_first/mid/last.jpg`——两契约首帧均近逐像素保真，2.5 略暖略净。
- 注意：出片 handler 自动 set-final——s02_c02 当前 final 已切到 2.5 版；如需切回 v2.0 版：
  `POST /api/project/雨灯归航/shot/s02_c02/video/set-final {"version_id":"vv_3420c4b9"}`。
