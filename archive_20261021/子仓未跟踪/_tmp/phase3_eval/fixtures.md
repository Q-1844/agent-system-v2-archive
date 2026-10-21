# 视频生产决策模拟——只读项目事实（九例）

通用背景（每例相同）：视频模型 agnes-video-v2.0；multi 模式向 provider 发
`extra_body.image=[恰好 1 张公网 URL]`（服务端 ti2vid 上限 1 张）；i2v 发顶层
`image=1 张公网 URL` 作首帧；keyframes 发 `extra_body.image=[首,尾]`。图片生成
接口 image_refs ≤6 张（可同时放多张参考）。角色"大鹤"批准 Look 特征：黑颈、
红冠、白体、黑次级飞羽及腿。

---

## 例 A：s01_c02 待生成

- s01_c01（medium shot）：final_video=vv_a1（done，8s），video_end_frame=
  `https://host/tail_a1.jpg`，end_source_version=vv_a1。尾帧目检：丹顶鹤中景
  滑翔下降，黑颈/红冠/黑次级飞羽清晰，湖面占画面下方，姿态与预期一致。
- s01_c02（medium shot，同场景同地点）：description="大鹤继续下降接近水面"；
  expected_tail="双脚伸出准备触水"；opening_source=independent；link_mode 未定；
  video_reference_asset_id 未设；binding READY（look/SIV 已批准）。
- 任务：决定 s01_c02 的视频怎么起步，给出执行前决策。

## 例 B：s02_c02 待生成

- s02_c01（extreme wide shot）：final_video=vv_b1（done），video_end_frame=
  `https://host/tail_b1.jpg`。尾帧目检：鹤为湖面上方小剪影（约占画面 5%），
  身份特征不可读；湖泊镜面反光/森林/逆光清晰；滑翔下降动作明确。
- s02_c02（medium shot）：description="承接下降，湖面逐渐扩大至充满画面"；
  expected_tail="大鹤在高空调整姿态，双翼准备减速"；opening_source=independent；
  source_shot_id=s02_c01；link_mode 未定；binding READY（look/SIV 已批准）。
- 任务：决定 s02_c02 的视频怎么起步，给出执行前决策。

## 例 C：s04_c02 待生成（上一镜尾帧已画错）

- s04_c01（medium shot）：final_video=vv_c1（done），video_end_frame=
  `https://host/tail_c1.jpg`。尾帧目检：鸟浮在水面，头颈全红、无黑颈、翅全白、
  体态似天鹅——与批准 Look 明显不符（身份已画错）。
- s04_c02（medium close-up）：要求第 0 帧起就是正确的大鹤；binding READY。
- 任务：决定 s04_c02 的视频怎么起步，给出执行前决策。

## 例 D：s03_c01 待生成（新故事段首镜，正常切镜）

- 上一组 s02 三镜全部完成；s02_c02 video_end_frame=`https://host/tail_d.jpg`。
- s03_c01（new scene 首镜）：叙事=切到新的观察位置重新建立环境（正常电影
  切镜，剧情明确不承接上一动作）；opening_source=independent；link_mode 未定；
  video_reference_asset_id 未设；binding READY。
- 任务：决定 s03_c01 的视频怎么起步，给出执行前决策。

## 例 E：s03_c01 待生成（新故事段首镜，但确需跨组接续）

- 上一组末镜 s02_c02：final_video=vv_e9（done），video_end_frame=
  `https://host/tail_e.jpg`（end_source_version=vv_e9）。
- s03_c01：剧情要求从 s02_c02 结尾的动作状态直接继续；shot 字段残留
  video_reference_asset_id="prev_tail"（按全片展平顺序解析，上一镜=s02_c02，
  跨段）；opening_source=independent；link_mode 未定；binding READY。
- 任务：决定 s03_c01 的视频怎么起步，给出执行前决策。

## 例 F：s05_c02 从 multi 改 i2v

- s05_c02 曾用 link_mode=multi + video_reference_asset_id=prev_tail 生成视频
  （final_video=vv_f2，done）。生成完成后系统把上镜真实尾帧同步进首帧槽：
  selected_first_frame=cand_ffsync_77（local/url=上一镜尾帧图），该批次
  prompt_snapshot="[接力边界] 实际首帧 = 上镜真实尾帧（版本 vv_f2）"。
- 现在用户要求：把这镜改成 link_mode=i2v 重新生成一条视频。
- 任务：给出执行决策（这镜的视频会用哪张图作什么、是否需要先做什么）。

## 例 G：上游改选新视频后的下游复核

- s06_c01：final_video 已从 vv_g1 改选为 vv_g2（重生成，尾帧 URL 由
  `https://host/tail_g1.jpg` 变为 `https://host/tail_g2.jpg`）。
- s06_c02（下游，已有视频 vv_g2d）：其视频记录 input_visuals 引用
  source_shot_id=s06_c01、end_source_version=vv_g1、url=`.../tail_g1.jpg`。
- 任务：给出下一步决策（s06_c02 与后续生产怎么处理）。

## 例 H：两处接缝的处置评估

- 接缝 1：s07_c01 尾帧（合格）→ s07_c02 首帧，测量 MAE=88；事实：两镜端点
  各自画面合格且值得保留，但中间发生了跨地点+大姿态反转，叙事要求连续过渡。
- 接缝 2：s08_c01 尾帧（合格）→ s08_c02 首帧，测量 MAE=35；事实：s08_c02 是
  剧本写明的反应镜切机位（intentional cut），叙事不需逐帧衔接。
- 任务：分别给出两处接缝的处置决策。

## 例 I：融合首帧实验候选的处置

- 实验克隆项目里有候选视频 vv_i1（未进正式项目 canonical）：用 Look+上镜
  真实尾帧合成新首帧后 i2v 生成。目检：身份（黑颈/红冠/黑飞羽）全程合格、
  景别符合目标、动作流畅；但结尾已双脚触水站立，而剧本 expected_tail="空中
  减速双翼收拢"。用户看过后口头评价"效果非常不错"。正式项目里该镜的
  final_video 仍是旧版裸尾帧接力结果（身份漂移）。
- 任务：给出这个候选的下一步处置决策。
