# 前端测试发现

> 本目录记录**端到端真实测试**中发现的问题，供前端 / 后端分工修复。
> 测试方式：绕过 UI，直接调用后端 HTTP 接口跑完整链路（真实生成 + 真实审查），以区分"前端显示问题"与"后端能力问题"。
> 最近更新：2026-09-16（场景系统全链路压测）

---

## 一、场景系统（Scene System）

测试项目：`projects/场景封板_0916_2216`（专用测试项目，可随时删除）
覆盖内容：地点 / 锚点 / 平面布局 / 4 个视角（不同机位、不同可见锚点集合）/ 2 个布景状态（夜雨、清晨）/ 2 个实例视图，共 16 张生成图。

### S-1【✅ 已修复 2026-09-17】实例视图缺两个读接口 → 界面看不到任何实例图
- 现象：`GET /scene-instance-views/{id}/generations` 与 `GET /scene-instance-views/{id}/approvals` 均返回 **404**。
- 修复（后端，2026-09-17）：已补齐三个只读端点——
  `GET /scene-instance-views/{id}/generations|reviews|approvals`
  （`routers/scene_system.py`；复用 `generation_records.read_records(scene_instance_view_id=…)` 过滤，
  与 LocationView 同口径，含 style 兼容结论附加；canonical 零写入）。
- 前端（2026-09-17）：候选/审查/批准改为**正式读取优先**（三路并行），路径推导仅保留为老数据兜底；
  刷新后「已批准候选（精确到索引）」「已撤销需重新审查」均可恢复。

### S-2【后端】多机位构图趋同（参考图锚定）⚠️高
- 现象：`东→西`、`西→东`、`地面→仰视` 三个视角生成结果构图高度雷同，相机方位几乎没生效。
- 证据：生成 basis 中
  - `selected_references = { role: "approved_view_reference", view_id: "<第一个已批准视角>" }`
  - prompt 中 `Camera: viewed from the west of the space, looking toward the east.` 是**正确的**
  → 文字指令正确，但已批准的兄弟视角图作为参考图压过了文字。
- 对照实验：把已批准视角全部撤销后再生成 → `selected_references` 为空 → 生成结果**构图明显变化**，且审查 7 项全 pass。
- 代码：`src/scene_system/visual_basis.py:108 select_reference_views`（auto 策略），仅支持 `auto` / `explicit`，**没有"不使用参考"模式**。
- 建议：新增 `reference_selection_mode: "none"`（或"仅身份段、不附图"）；前端在生成时提供「使用已批准参考图 / 自由构图」开关。

### S-3【前端+后端】撤销批准后无法直接重新批准（409）→ 必须先复审
- 现象：`revoke` 之后调用 `approve` 返回 **409**；重新执行 `review` 后 `approve` 成功（`verified=True`）。
- 影响：界面上的「撤销批准」若不引导重新审查，用户会卡死。
- 前端要求：撤销后把「批准」按钮置灰，并提示"需重新审查后才能再次批准"。

### S-4【后端】布景状态无法"通用化"（`story_scene_id` 必填）
- `CreateSceneInstanceRequest.story_scene_id` 为必填，且 V1 规则为"同一 story_scene_id 至多一个 active 实例"。
- 后果：做不出"深夜·中雨"这类可被多场复用的通用布景状态；每做一个状态都要挂在某一场上。
- 建议：`story_scene_id` 改为可选；"同场次唯一 active"校验只对已归属实例生效；`list_scene_instances` 支持未归属过滤。

### S-5【后端/提示词】地点与状态字段必须用英文填写，否则生成质量崩坏 ⚠️高
- 对照实验（同一视角、同一提示词结构，只改字段语言）：
  - 字段用**中文** → 生成 "3D 材质风空房间"，审查 `project_style_consistency: concern` → `overall=uncertain` → **批准被 fail-closed 拦死**
  - 字段用**英文** → 3 个候选 **7 项维度全部 pass**，图像为标准 2D 赛璐璐风格
- 根因：字段被直接拼进英文模板（`src/scene_system/location_prompt.py`、`instance_view_prompt.py`），如 `Preserve the approved {name} exactly: {identity_description}`。
- 前端要求：地点「空间身份 / 风格注记」、布景状态「时段 / 天气 / 灯光 / 环境条件」输入框加英文示例提示；`label`（视角名）可用中文。

### S-6【后端】视觉审查的两个小毛病
- 偶发**返回无法解析的 JSON** → 记 `uncertain`（fail-closed，符合设计）；本次 3 轮里出现 2 次，该候选不可批准，需重新生成。
- 出现过**维度全 pass 但 `summary` 写 "requires a fix"** 的措辞不一致（以派生 `overall` 为门槛，不影响正确性）。

### S-7【已决策不做】按布景状态 / 视角反查引用它的分镜
- 服务层有 `read_binding(shot_id)`，缺反查方向端点；经确认该功能对本系统（面向 Agent）无必要，**不做**。

### S-8【✅ 已修复 2026-09-17】实例视图缺「历史审查记录」读接口
- `GET /scene-instance-views/{id}/reviews` 不存在（定位视角的 `/views/{id}/reviews` 存在且已接前端）。
- 影响：实例视图的"哪个候选审查通过"只在**当前会话内**可见（点过「视觉审查」才有）；刷新后批准按钮状态丢失，需重新点一次审查。
- 已随 S-1 一并修复：三读接口补齐 + 前端刷新时恢复审查徽章与批准门控。

---

## 二、前端显示逻辑问题（本次改造一并修）

| 编号 | 问题 | 处理 |
|---|---|---|
| F-1 | 视角卡封面只取"已批准图"，未批准但有候选的视角显示"未生成" | 改为：已批准图 → 否则取最新候选图 → 都没有才显示空态 |
| F-2 | 实例视图候选/已批准图全部不显示（因 S-1） | 前端按 S-1 的路径推导临时兜底 |
| F-3 | 撤销批准后按钮状态未跟随（S-3） | 撤销后置灰「批准」，提示需重新审查 |
| F-4 | 页面配色脱离设计系统 | 该页原使用**不存在的变量** `--text-1 / --bg-3`（全部落到硬编码 fallback），并硬编码 `#6ea8ff / #5a8dee / #9ec2ff / #c9bcff / #9fe0a8 / #ffb59d` 等蓝紫绿 → 全部换回 `global.scss` 的黑白灰 token |

---

## 三、角色模块（已完成改造，遗留项）

| 编号 | 问题 | 状态 |
|---|---|---|
| C-1 | 角色三视图无候选 / 无审批（后端将审批限定在资源域） | 已知设计；角色页的「候选与审查」借用 Look 能力实现 |
| C-2 | 资源页无深链到某个 Look 的能力 | 待资源模块合并时一并处理 |

---

## 四、资源模块（待合并时处理）

- 现行「生产资源」页面排版质量偏低，已确认**合并进角色式布局（左列表 + 右详情区块流）**；执行清单见另一份文档《资源模块合并执行清单》。
- `Prop` 无分类字段（角色手持物 vs 环境物件）无法从前端干净区分；建议后端补 `Prop.kind`，否则用"是否被组合参考/场景摆放引用"反推。
