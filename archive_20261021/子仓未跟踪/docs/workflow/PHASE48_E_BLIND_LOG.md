# PHASE48 E 盲测生产日志（P48_E_Blind /《铃铛与鹊巢》）

盲测 Agent 记录。时间起点 2026-10-06。项目 Python：`D:\Delta Force\python.exe`。

## 决定与事实记录

### 0. 启动前事实核对（真实读取，非假设）
- 后端健康：`GET /api/health` → `{"status":"ok","controller_ready":true}`。
- 项目视觉基调（读 `projects/P48_E_Blind/output/project_profile.json`）：
  `render_family=2d_animation`，`art_direction="warm gouache storybook animation, soft rounded shapes, gentle outlines, pastoral palette"`。**未做任何修改。**
- Skill catalog 实测（`GET /api/project/P48_E_Blind/workflow/catalog`）：
  - `full-story-relay-calibration` version=1.4.0 contentHash=sha256:30a4d8e88e3b8edd71f3eafe
  - `keyframes-bridge-repair` version=1.4.0 contentHash=sha256:c7f8e313abdab60a42a94993
- 项目此时为空壳（仅 project.json / project_profile.json），故事/角色/场景均需工作流真实生产。

### 1. 定义创建与启动
- 用 **W09 模板**创建定义 `wf_e_blind_bell`（rev=1，validation ok；仅 REVIEW_NO_TARGET 类 warning，与既往 run 一致）。
- 关键参数决定：
  - `writerObjective` 内嵌简报故事全文（段落数由叙事决定，画面化、无旁白）；
  - `characterObjective`：小杏（红头绳/靛蓝布衫）、石头（圆脸寸头/灰白条纹衫）+ 道具铜铃铛/长竹竿/长柄火钳，缺参考如实列缺项；
  - `sceneObjective`：沿用 state_view.prepare 为空间依据的标准目标；
  - `boardObjective`：镜头数量由动作决定（≥6，预计 8 镜），要求含同地点连续动作、一次换场、一次中近景身份检查；
  - `videoObjective`/`assemblyObjective`：显式写明"全片无旁白""保留合格原生环境声与动作声""不加配乐"；
  - `videoCount=6`（模板下限，镜头数以分镜实际为准）；`bindRelaySkill=true`。
- 启动 run：`run_240a4e34419e`，status=running，reused=False，幂等键 `p48e_blind_bell_v1`。
- 驱动脚本：`_p48_e_blind_driver.py`（只调工作流 REST：create/start/poll/decision/continue；生产本身全部由工作流 Agent 完成）。

### 2. run 进度
（随轮询追加）

## 轮 1（run 启动后 ~1 分钟）
- n_producer ✅ att_4fc7a0d782；n_sw ✅ att_f216a18e40（真实产出 6 个故事段，canonical 落在
  `projects/P48_E_Blind/output/project.json` 的 scenes s01-s06）。
- n_rv_sw（故事审定，requestId=rev_7c8ab2ed94）停靠 → **目检过程**：读 `project.json` 逐段核对。
  - 判定：六段忠实覆盖简报全部关键节拍（喜鹊叼铃→掉大青石石缝→竹竿第一次尝试失败
    （铃滑向更深处、竹竿头裂）→小杏抉择搬碎石→缝里发现去年冬天丢的长柄火钳→夹出铃铛
    系回头鸭→傍晚赶鸭回家铃铛一路叮当）；角色外观符合设定；无旁白、无台词文本。
  - 如实记录缺陷（不阻塞）：s02 出现"去年被雷劈裂开的石缝"为简报外少量世界观补充；
    s04"赤着的水田鞋"措辞含混，留分镜阶段注意。
  - 决定：approve，note 前缀"盲测中间关口"，回执 rcp_51ebb429。
- n_cd（角色生产）att_ead52e4c86 派发中（character_designer.delegate 委派已开始）。

## 轮 2（~6 分钟）
- n_cd ✅ att_ead52e4c86（约 5.5 分钟）：产出角色 小杏/石头 各 1 Look + 服装 + 多张参考
  （provider=agnes i2i job url + checksum 落库；resources.json reference_assets 共 10 条）。
- n_rv_cd（资源审定，rev_ab30279068）停靠 → **目检过程**：
  - Read 直读两张已批 Look PNG：
    小杏 ref_e6e99f252e01（红头巾/侧辫/靛蓝立领布衫/卷袖/深色卷裤/黑布鞋）、
    石头 ref_8d6d77a2a740（寸头/圆脸/灰白横条纹衫/卷裤/棕胶靴）。两图风格与项目
    warm gouache storybook 基调一致、互洽、无伪影。
  - 如实记录缺陷（不阻塞）：①小杏"红头绳"被渲染为红头巾（头饰形态偏差）；
    ②道具（铜铃铛/长竹竿/长柄火钳/头鸭）无参考图——角色 Agent 已在
    missingRequirements 如实列缺（原因：系统无道具生成端点），不是谎报完成。
  - 决定：approve + withSelection（items 双 Look：look_5b57a958edfe→ref_e6e99f252e01、
    look_36bb0514a0ed→ref_8d6d77a2a740），回执 rcp_c2f0132f。
- n_sc（场景生产）已派发。参考既往 run 该节点约 17 分钟，继续轮询。

## 轮 3（~30 分钟）
- n_sc ✅ att_9078459123：产出 2 Location（loc_5b848f3f87b4 村口大青石一带=石缝+碎石堆+
  老柳树+水渠；loc_97685e6de627 村道=晚霞芦苇+湿润田埂）、6 SceneInstance（状态随剧情节拍
  递进：鸭群四散→石缝铜光→裂竹竿落地→碎石被部分搬开→石缝敞开→傍晚归途）、6 anchor、
  2 layout、location/instance 视图若干（真实生成图像落盘）。
- n_rv_sc（场景审定，rev_3e430a4098）停靠 → **目检过程**：
  - 读 scene_system.json 核对 Location/SceneInstance 语义（见上）；
  - Read 直读两张状态图：scin_36368e15b5c6（大青石+石缝铜光+石顶碎石堆+水渠鸭群，
    清晨）、scin_0343735dcb70（晚霞金红芦苇+湿润村道+院墙）——构图与 warm gouache
    基调一致，无伪影；
  - 如实记录缺陷（不阻塞）：青石主缝旁另有一道小裂缝（轻微冗余细节）。
  - 决定：approve（本关口无选用要求），回执 rcp_c9c91646。
- n_dir_board（分镜）派发中。本节点需产出 ≥6 镜分镜图，属长操作。

## 轮 4（45 分钟预算到，收尾）
- 最后一次轮询（~44 min）：run_240a4e34419e status=**running**（worker=True），无 failed 节点，
  n_dir_board att_6f4f176626 仍在真实生产（分镜图像长操作未结算）。
- 按简报 45 分钟上限，本轮在此收笔，未停靠新关口。已完成节点链：
  n_producer ✅ → n_sw ✅ → n_rv_sw ✅（目检通过）→ n_cd ✅ → n_rv_cd ✅（目检+双 Look 选用）→
  n_sc ✅ → n_rv_sc ✅（目检通过）→ n_dir_board 🔄 运行中。
- 待办（下一会话接续）：
  1. 轮询至 n_rv_board（分镜审定+首帧选用）停靠 → 用 Read/ffmpeg 目检分镜图与首帧候选，
     以 selectionOverride items [{shotId, candidateId}] 选用首帧后 approve（注记"盲测中间关口"）。
  2. n_dir_video（视频，绑定 relay skill v1.4.0，videoCount≥6）→ n_rv_v1/n_rv_v2（二审含
     video_version 多选用）→ n_asm 装配（无旁白/保留合格原生音效/不加配乐）→ n_rv_final。
  3. **n_rv_final 成片审定保持 pending，不做**，留给用户。
  4. 接续工具：`D:\Delta Force\python.exe _p48_e_blind_driver.py status|events|approve|continue`；
     轮询间隔 ≥30s。
- 本轮无任何节点失败，无需 continue 重试；所有 approve 均先读真实 canonical/图像再决定，
  缺陷（红头巾形态偏差、道具无参考图如实列缺、青石冗余小裂缝、s02/s04 文本小瑕）已如实记录在案。

# 盲测续跑轮（第二轮会话，预算 50 分钟）

## 轮 5（分镜关口）
- n_dir_board ✅ att_6f4f176626（约 10 分钟）：8 镜（s01_c01/s02_c01/s03_c01/s04_c01/
  s04_c02/s05_c01/s06_c01/s06_c02），每镜 canonical 含景别/光线/动作/运镜/6s 时长，
  8 个 binding 落齐；每镜 1 张首帧候选（agnes t2i job + 本地 frames/sXX_cXX_first_v1.png）。
- n_rv_board（rev_8f06fc9e4d）停靠 → **目检过程**：Read 直读全部 8 张首帧 + 读镜头 canonical。
  合格面：人物与已批 Look 一致、风格一致、景别构图有区分。
  **缺陷如实记录（逐镜，实验重点口径——分身/漂移类）**：
  - s01_c01：喜鹊两只（实体重复）；头鸭颈铜铃不可辨。
  - s02_c01：石头手中无竹竿（道具缺席）；石缝铜光弱。
  - s03_c01：空间漂移——大青石石缝被画成圆形石砌井口；铃铛反常挂在竿头可见（因果错误）。
  - s04_c01：**小杏分身**（站姿+蹲姿两个同装小杏同框）。
  - s04_c02：火钳形制偏叉勺；场景为石墙根而非大青石。
  - s05_c01：**铃铛两只**（道具重复）；场景在村巷。
  - s06_c01：鸭群缺席。
  - s06_c02：门楣多余铃铛；木牌伪汉字"稍片束于"；禽群似鸡鸭混杂。
- 决定：approve + withSelection（items 8 项，逐镜指向 selected_first_frame 的 ff_* 精确版本），
  回执 rcp_f3852056。服务端选用执行成功，run 继续（n_dir_video 派发）。
  说明：本关口按简报只有通过/选用权限，缺陷留给视频一审/二审与修复路径核对。

## 轮 6（续跑 ~48 分钟，收笔）
- n_dir_video att_f10d0bf012 运行全程健康：事件账本见 skill.load（接力 Skill 绑定）→
  shot.list → director.delegate 长回合；视频真实落盘 `output/videos/`：
  至收笔时 **5/8**（s01_c01、s02_c01、s03_c01、s06_c01、s06_c02），其余 3 镜
  （s04_c01、s04_c02、s05_c01）在队列/生成中，节点未结算。
- 无 failed 节点，未动用 continue；n_rv_v1 / n_rv_v2 / n_asm / n_rv_final 本轮未到达。
- **遗留事项（下一会话按序）**：
  1. 轮询至 n_dir_video 结算 → n_rv_v1（视频一审）：用 ffmpeg 抽帧（首/中/尾）+ Read 目检
     8 条视频，重点核对分镜关口记录的缺陷是否在视频里复现/恶化（尤其 s03_c01 井口空间漂移、
     s04_c01 分身、s05_c01 双铃铛、s06_c02 伪汉字与多余门铃），如实记录。
  2. n_rv_v2（视频二审）：selectionOverride items=[{entityId: shotId, versionId: video versionId}]
     逐镜选用装配版本（缺 versionId 会被拒，不得默认最新）。
  3. n_asm 装配：确认无旁白/保留合格原生音效/不加配乐传导到位 → render 完成。
  4. **n_rv_final 成片审定出现即停，保持 pending，留给用户。**
  5. 接续工具不变：`_p48_e_blind_driver.py status|events|approve|continue|node`，轮询间隔 ≥30s。

# 盲测续跑轮 2（第三会话，预算 50 分钟）

## 轮 7（视频阶段预检 + 收笔）
- n_dir_video att_f10d0bf012 全程 running（无失败）；至 ~35 分钟时 8/8 视频全部落盘
  `output/videos/`（s01_c01/s02_c01/s03_c01/s04_c01/s04_c02/s05_c01/s06_c01/s06_c02.mp4，
  时长 4.48s–7.33s）。节点结算（中尾帧核对/完成校验）尚未完成——事件账本停留在
  skill.load→shot.list 之后，导演长回合未写回。
- **视频预检（为 n_rv_v1 前置）**：ffprobe 实测时长；ffmpeg 对 8 条视频各抽首/中/尾 3 帧
  （存 `output/videos/_rv1_frames/`，24 张）+ Read 全部目检。结论（诚实记录）：
  - 视频阶段实际修复了多数分镜缺陷：s01 头鸭颈铜铃清晰可辨（分镜"不可辨"已修复）、
    铃终态落在石旁地面；s02 石头持竹竿探石缝（分镜"无竹竿"已修复）；s03 空间恢复为
    大青石石缝（分镜"井口"漂移已修复）且竹竿尖裂开/断段落地（剧情尾态正确）；
    s04_c01 全程单个 小杏（分镜"分身"已消失）；s04_c02 火钳为正确双柄钳形（分镜"叉勺"
    已修复）且钳口夹铃拖出；s05 单铃铛（分镜"双铃"已修复）、系铃回头鸭动作完整；
    s06_c01 鸭群在场跟人过院门（分镜"鸭群缺席"已修复）；s06_c02 木牌为空白木板
    （伪汉字已消失）、门楣无多余铃铛。
  - 仍存/新现缺陷（如实）：s01 抽样帧未见喜鹊、衔铃飞向石缝的因果未确认（铃终态为
    地面而非缝口）；s03 首帧铃铛挂在竿头可见（沿承分镜的因果怪点）；s04_c02 铃铛体量
    偏大（近牛铃尺度，比例漂移）；s05 中/尾帧小杏发饰由红头巾漂移为红蝴蝶结（人物
    配饰漂移，辫子保持）；s06_c01 抽样帧头鸭铃铛不可辨。
- 收笔时（~50 分钟）n_rv_v1 关口尚未开启（n_dir_video 未结算），本轮未做任何 approve。
- **遗留（下一会话）**：
  1. 轮询至 n_dir_video 结算（若 failed：读失败原因→核对 8 条视频真实在盘状态→continue 重试）。
  2. n_rv_v1 开启后：以上述预检为基础复核（必要时重抽帧），注记"盲测中间关口"通过；
     预检明细已记本日志。
  3. n_rv_v2：selectionOverride items=[{entityId: shotId, versionId: <视频版本ID>}] 逐镜选用
     （版本 ID 以 run JSON reviews[].selectionCandidates 为准）。
  4. n_asm：核验装配目标含"禁止自动旁白/保留合格原生音效/不加配乐"，render 完成即可通过。
  5. **n_rv_final 出现即停，保持 pending 留用户。**

# 盲测续跑轮 3（第四会话，预算 50 分钟）

## 轮 8（视频两审 + 装配 + 停靠 n_rv_final）—— 达成简报交付条件
- n_dir_video ✅ att_f10d0bf012 结算成功（8/8 视频服务端核验通过，全部 status=done）。
- **n_rv_v1（rev_c96e599688）**：核对 8 镜 final_video 版本 ID（vv_addc4dc2/vv_98ce4a92/
  vv_df6430e6/vv_bf3f4d1a/vv_a8dc7e6a/vv_e181d1c7/vv_a98f2022/vv_d8667fe9）与
  output/videos 8 个 mp4 一一对应后，以轮 7 预检为依据 approve（本关无选用），
  回执 rcp_11b89085，注记"盲测中间关口"，一审缺陷清单原样保留在案。
- **n_rv_v2（rev_ac96b76443，selectionRequired=True）**：withSelection items 8 项，逐镜
  选用上列精确版本（不默认最新、不选未检版本），回执 rcp_7dabcaa5。
- n_asm ✅ att_3acfffaf7a：Sequence `seq_c02c1d94` + 完成渲染
  `output/sequences/seq_c02c1d94/srender_a9727fd2.mp4`（ffprobe 实测 45.75s、10.5MB、
  **含 aac 立体声原生音轨**——与"禁自动旁白/保留合格原生音效/不加配乐"政策一致）。
- **n_rv_final（rev_1d29a80a21）已停靠 pending** —— 用户关口，**本轮不做任何决定**，
  证据链齐备：sequence artifact fingerprint sha256:7e5255730f51...，目标 n_asm att_3acfffaf7a。
- 简报交付判定达成：run 走到 n_rv_final（成片审定 pending、等用户）。
- 全程无失败节点、无 continue 重试；全部中间关口 approve 均基于读工具目检真实工件
  （canonical JSON / PNG / ffmpeg 抽帧），注记统一为"盲测中间关口"。

## 最终链路
n_producer ✅ → n_sw ✅ → n_rv_sw ✅ → n_cd ✅ → n_rv_cd ✅（选用）→ n_sc ✅ → n_rv_sc ✅ →
n_dir_board ✅ → n_rv_board ✅（8 镜首帧选用）→ n_dir_video ✅ → n_rv_v1 ✅ → n_rv_v2 ✅（8 镜
版本选用）→ n_asm ✅ → **n_rv_final ⏸ pending（等用户）**
成片：`projects/P48_E_Blind/output/sequences/seq_c02c1d94/srender_a9727fd2.mp4`（45.7s）








