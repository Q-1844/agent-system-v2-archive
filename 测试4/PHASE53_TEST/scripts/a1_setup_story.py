# -*- coding: utf-8 -*-
"""Phase 53 A1 探索基线 setup：三故事（I 室内/F 要塞/M 怪物）W09 六员完整生产。
- 目标级 brief（PHASE53_03 叙事负荷），逐镜技术答案完全留给系统 Agent；
- collab v2（用户 2026-10-11 定版）：前置 4 审核卡 autoApprove=true；
- 正式 Skill 绑定 full-story-relay-calibration v1.6.0（n_dir_video + n_dir_board）；
- 时长政策：按冻结 Skill v1.6.0 时长配方 + 尾帧接续链策略（不在简报自创秒数）。
用法：python a1_setup_story.py I|F|M
"""
import json, sys, time, urllib.request, pathlib

BASE = "http://127.0.0.1:8000"
RELAY_SKILL = "full-story-relay-calibration"
RELAY_VER = "1.6.0"
ROOT = pathlib.Path(__file__).resolve().parents[2]   # 测试4/
EB = ROOT / "PHASE53_TEST" / "evidence"

STORY_KEY = sys.argv[1] if len(sys.argv) > 1 else "I"
SUFFIX = sys.argv[2] if len(sys.argv) > 2 else ""   # 重启用：项目名后缀（如 "2"）

SKILL_HINT = ('【工作方法】开始执行前先 skill.load "full-story-relay-calibration" 并严格遵循'
              '其制作方法（审核三查判据/时长配方/尾帧接续链策略均以该 Skill v1.6.0 正文为准，'
              '不使用其他秒数政策）。\n')

STORIES = {
 "I": dict(
  proj="P53_I", film="《杯沿的断层》",
  producer=("生产计划：写实电影短片《杯沿的断层》——傍晚的古生物研究室，三位研究人员围坐木桌，"
            "围绕一件虚构标本的裂纹争论：它看似支持某个旧判断，却发现修补痕迹，三人决定重新核验。"
            "目标成片约 30–42 秒（完整叙事，短而完整可评审），横屏 16:9，写实电影质感。"
            "测试负荷目标 6 个镜头；若剧情确需增减镜头，请在生成开始前明确提出并冻结，否则按 6 镜规划。"
            "本片有简短人物对白（室内讨论），无画外旁白、无主动背景音乐；保留合格原生环境声与音效。"
            "逐镜技术方法由各专业 Agent 自主决定，你不需要给出逐镜答案。"),
  writer=("【作品目标】研究室争论短片（虚构科学讨论，不把编造内容讲成真实古生物学结论）。地点："
          "傍晚的古生物研究室——一张木桌、标本托盘、茶具、窗侧柜，三个研究人员围坐。故事：①交代三人、"
          "研究室与桌上标本；②负责人林澄指出标本裂纹并提出简短推测；③年轻研究员周野拿起自己那侧的"
          "茶杯提出反问；④负责标本保存的顾宁指出标本上的修补痕迹（视线与指向确实落在标本上）；"
          "⑤周野把茶杯放回桌面，林澄改变判断；⑥三人达成重新核验的决定，标本与茶杯最终状态符合此前动作。"
          "要求：人物=林澄（负责人）/周野（年轻研究员）/顾宁（标本保存），年龄/发型/服装轮廓明确区分，"
          "不靠姓名字幕辨识；对白简短、每轮意思讲清，至少两个明确说话者，第三人（顾宁）有独立叙事作用；"
          "茶杯起始在周野一侧、归属固定；每段写清剧情任务、起始状态、主动作、结果状态。"
          "全片镜头数以 Producer 生产计划的冻结值为准（测试负荷目标 6 镜；增减须在生成前报备并冻结），"
          "你按该负荷写故事段，不预先规定分镜。"),
  character=("新建写实资产（全部真实生成参考图）：①林澄——负责人，年龄/发型/服装与另两人明确区分，"
             "写实皮肤质感；②周野——年轻研究员，与林澄可区分；③顾宁——标本保存负责人，第三人形象可区分；"
             "④茶杯道具参考——一只带小缺口、特定把手方向的茶杯（同一只杯贯穿全片）；"
             "⑤标本参考——一件固定形态的虚构古生物标本（含细微裂纹与修补痕迹特征）。"
             "参考图必须是写实电影质感（不许插画风/游戏质感）。缺项如实列出，不伪造。"),
  scene=("建立场景：傍晚的古生物研究室（内景）——木桌（三人围坐位置固定：三人各有稳定座位）、"
         "标本托盘、茶具、窗侧柜、傍晚窗光。维护简明空间定义（时段=傍晚/光源=窗侧暖光/座位布局/"
         "桌面物件摆放）。每个故事段的具体状态用 scene.state_view.prepare 生成 SceneInstanceView "
         "并绑定正确 SceneInstance——后续分镜首帧与视频以状态图为空间依据。"),
  board=(SKILL_HINT + "【任务】按已写好的故事自主设计分镜：镜头清单、资源绑定、分镜图（首帧候选）。"
         "上述六个叙事事件必须全部发生在镜间且有因果；每镜规划含：功能与主动作、起止状态（人物座位/"
         "茶杯在谁手或何处/标本状态）、机位与空间关系、预计可见人物、必须保留的关键事件。"
         "对白轮次的说话者必须明确；正常正反打与机位变化由你按规则决定；三人身份镜用已批准 Look 参考；"
         "人物总数纪律：全片只有三位人类。"),
  video=(SKILL_HINT + "【任务】按已选首帧与镜头清单真实生成全部视频：逐镜自主决定模式与接续方式，"
         "完成后核对回执、文件真实时长与首中尾帧。素材时长与接续一律按正式 Skill v1.6.0 的时长配方与"
         "尾帧接续链策略执行。生成前先完整审看各镜已选首帧；首帧不合格的镜头先修首帧再提交。"
         "视频过程纪律：人物总数不得超过三人、不得出现分身；茶杯的抓握/拿起/放回过程完整，"
         "杯子不能瞬移到另一人手上；对白说话者与口型对象一致；视线与指向落在被谈对象上。"),
  videoCount=6,
 ),
 "F": dict(
  proj="P53_F", film="《灰塔的错误信号》",
  producer=("生产计划：写实战争悬疑短片《灰塔的错误信号》——虚构战争中的山口要塞，两名突击队员在进攻前"
            "发现约定信号异常；接近外侧控制点开启闸门时发现信号由守军伪造，最终切断假信号并取得进攻入口。"
            "目标成片约 30–42 秒（完整叙事），横屏 16:9，写实电影质感（战争氛围，但不堆群众与持续爆炸）。"
            "测试负荷目标 6 个镜头；若剧情确需增减，请在生成开始前提出并冻结。"
            "以动作为主、允许短交流，无画外旁白、无主动背景音乐；保留合格原生环境声与音效。"),
  writer=("【作品目标】要塞夜袭悬疑短片。地点：虚构战争中的山口要塞外——封闭入口、掩体、外侧控制点。"
          "故事：①交代要塞、封闭入口、掩体与两名突击队员位置；②通信员看到异常信号（约定信号不对），"
          "队长决定靠近控制点；③两人向指定掩体移动，行动方向可解释；④遭遇守军阻拦（守军短暂出现），"
          "队长掩护通信员接近控制箱，行为有因果；⑤通信员操作装置切断假信号，闸门开始打开；"
          "⑥两人进入已打开的入口，后续进攻具备条件，假信号悬念得到回应。"
          "要求：角色=队长与通信员（装备外形明确区分），守军不是主任务主角；控制箱/信号灯/通信设备/闸门"
          "状态（闭→开）要能被看见；每段写清剧情任务、起始状态、主动作、结果状态。"
          "全片镜头数以 Producer 生产计划的冻结值为准（测试负荷目标 6 镜；增减须在生成前报备并冻结），"
          "你按该负荷写故事段，不预先规定分镜。"),
  character=("新建写实资产（全部真实生成参考图）：①队长——突击装备轮廓与通信员明确区分（写实军品质感）；"
             "②通信员——与队长可区分（装备/头盔/背包差异）；③守军——可短暂出现的守方士兵；"
             "④控制箱装置参考——外侧控制箱与信号灯（同一装置贯穿）；⑤闸门参考——要塞入口闸门（闭合状态）。"
             "参考图必须是写实电影质感。缺项如实列出，不伪造。"),
  scene=("建立场景：山口要塞外区域——要塞入口（闸门关闭）、突击队员出发掩体、中间掩体、外侧控制点"
         "（控制箱+信号灯）。维护空间定义（夜/光源/进攻方向/掩体相对位置/闸门状态）。每个故事段的具体"
         "状态用 scene.state_view.prepare 生成 SceneInstanceView 并绑定正确 SceneInstance。"),
  board=(SKILL_HINT + "【任务】按已写好的故事自主设计分镜：镜头清单、资源绑定、分镜图（首帧候选）。"
         "六个叙事事件必须全部发生在镜间且有因果；每镜规划含：功能与主动作、起止状态（人物位置/装备/"
         "闸门状态/信号状态）、机位与空间关系、预计可见人物、必须保留的关键事件（装置操作与闸门开闭）。"
         "两人身份镜用已批准 Look 参考；人物纪律：主要任务只跟两名突击队员，守军短暂出现不计入主体人数。"),
  video=(SKILL_HINT + "【任务】按已选首帧与镜头清单真实生成全部视频：逐镜自主决定模式与接续方式，"
         "完成后核对回执、文件真实时长与首中尾帧。素材时长与接续一律按正式 Skill v1.6.0 执行。"
         "生成前先完整审看各镜已选首帧；首帧不合格的镜头先修首帧再提交。"
         "视频过程纪律：两名队员身份不串；手部接触（装置操作/掩护动作）过程完整；"
         "闸门从闭到开状态可解释；行动方向与掩体空间关系连续。"),
  videoCount=6,
 ),
 "M": dict(
  proj="P53_M", film="《第三道回声》",
  producer=("生产计划：写实悬疑短片《第三道回声》——有异常生物活动的地下标本库，两名探索者进入找回记录匣，"
            "听到第三道回声，误以为同伴落后，直到同伴从前方回答，才意识到怪物正在模仿脚步。目标成片约 "
            "30–42 秒（完整叙事），横屏 16:9，写实电影质感（低照度氛围，但不能以黑屏隐藏关键动作）。"
            "测试负荷目标 6 个镜头；若剧情确需增减，请在生成开始前提出并冻结。"
            "以动作为主、允许短交流，无画外旁白、无主动背景音乐；保留合格原生环境声与音效。"),
  writer=("【作品目标】地下标本库探索悬疑短片。地点：地下设施——入口走廊与相连的标本库，以红色管道和"
          "一道防护门建立空间记忆。故事：①两人进入走廊，交代手电归属、标志物（红色管道）和前进方向；"
          "②听到额外脚步，一人回头确认同伴位置；③正常转入相邻标本库，找到记录匣；④怪物出现在可解释的"
          "位置，模仿脚步的线索成立（最多一个个体）；⑤两人带着记录匣撤向防护门，一人操作关门，关键动作"
          "和接触可见；⑥门关闭、两人及记录匣均在安全一侧；门外再响起第三道回声，形成悬疑结尾。"
          "要求：两名探索者外形明确区分；怪物一种固定外形、出现时最多一个个体；手电与记录匣归属固定；"
          "每段写清剧情任务、起始状态、主动作、结果状态。全片镜头数以 Producer 生产计划的冻结值为准"
          "（测试负荷目标 6 镜；增减须在生成前报备并冻结），你按该负荷写故事段，不预先规定分镜。"),
  character=("新建写实资产（全部真实生成参考图）：①探索者A——与B明确区分（装备/服装轮廓）；"
             "②探索者B——与A可区分；③怪物参考——一种固定外形的异常生物（同一实体、可识别、最多一个个体）；"
             "④手电参考——同一支手电（归属固定）；⑤记录匣参考——同一只记录匣。"
             "参考图必须是写实电影质感。缺项如实列出，不伪造。"),
  scene=("建立场景：地下设施——入口走廊（红色管道标志）与相连的标本库、防护门。维护空间定义（低照度光源/"
         "管道走向/门的位置与开闭状态）。每个故事段的具体状态用 scene.state_view.prepare 生成 "
         "SceneInstanceView 并绑定正确 SceneInstance。"),
  board=(SKILL_HINT + "【任务】按已写好的故事自主设计分镜：镜头清单、资源绑定、分镜图（首帧候选）。"
         "六个叙事事件必须全部发生在镜间且有因果；每镜规划含：功能与主动作、起止状态（人物位置/手电与"
         "记录匣归属/怪物是否可见/门状态）、机位与光源方向、预计可见人物、必须保留的关键事件。"
         "两人身份镜用已批准 Look 参考；人物纪律：两名探索者+至多一只怪物，不得人群化。"),
  video=(SKILL_HINT + "【任务】按已选首帧与镜头清单真实生成全部视频：逐镜自主决定模式与接续方式，"
         "完成后核对回执、文件真实时长与首中尾帧。素材时长与接续一律按正式 Skill v1.6.0 执行。"
         "生成前先完整审看各镜已选首帧；首帧不合格的镜头先修首帧再提交。"
         "视频过程纪律：探索者身份不串；怪物始终同一实体且最多一个个体；手电/记录匣归属与接触完整；"
         "光源方向连续；关门动作与结果可见；低照度不掩盖关键动作。"),
  videoCount=6,
 ),
}

S = STORIES[STORY_KEY]
PROJ, WID = S["proj"] + SUFFIX, f"{S['proj']}{SUFFIX}_W53"
# 单地点故事（I）完成契约 location×1；F/M 默认模板值 ×2
if STORY_KEY == "I":
    S = dict(S)
    S["_loc_min"] = 1
MANUAL_REVIEW_NODES = {"n_rv_v1", "n_rv_v2", "n_rv_final"}   # 执行侧代行（帧证据）
AUTO_FRONT = ["n_rv_sw", "n_rv_cd", "n_rv_sc", "n_rv_board"]  # collab v2 autoApprove


def req(path, body=None, method="GET", timeout=120):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data,
                               headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.load(resp)


def main():
    t0 = time.time()
    log = []
    def P(x):
        print(x, flush=True); log.append(x)

    # 1) 项目
    try:
        req(f"/api/projects/create?name={PROJ}&render_family=photorealistic"
            f"&art_direction=%E5%86%99%E5%AE%9E%E7%9F%AD%E7%89%87", None, "POST")
        P(f"project {PROJ} created")
        # D-08 修正：对白语言预配（fail-closed 闸要求）
        req(f"/api/project/{PROJ}/native-av-settings",
            {"spoken_language": "Mandarin Chinese"}, "PUT")
        P("native_av.spoken_language=Mandarin Chinese set")
    except Exception as e:
        P(f"create: {e}")

    # 2) W53 定义（W09 模板 + 目标级参数）
    params = {
        "producerObjective": S["producer"], "writerObjective": S["writer"],
        "characterObjective": S["character"], "sceneObjective": S["scene"],
        "boardObjective": S["board"], "videoObjective": S["video"],
        "videoCount": S["videoCount"], "bindRelaySkill": True,
    }
    r = req(f"/api/project/{PROJ}/workflow/templates/W09/create",
            {"workflowId": WID, "params": params}, "POST")
    P(f"template create rev={r.get('revision')} ok={r.get('validation', {}).get('ok')}")

    # 3) 定义编辑：autoApprove 前置 4 卡 + Skill v1.6.0 双绑定
    d = None
    for cand in (f"projects/{PROJ}/output/workflows/definitions/{WID}.json",
                 f"projects/{PROJ}/output/workflow/definitions/{WID}.json"):
        p = pathlib.Path(cand)
        if p.exists():
            d = json.load(open(p, encoding="utf-8")); break
    assert d, "definition file not found"
    for n in d["nodes"]:
        if n.get("type") == "human_review" and n.get("id") in AUTO_FRONT:
            n.setdefault("config", {})["autoApprove"] = True
        if n.get("id") == "n_sc" and S.get("_loc_min"):
            comp = n.setdefault("config", {}).setdefault("completion", {})
            for o in comp.setdefault("outputs", []):
                if o.get("kind") == "location":
                    o["minCount"] = S["_loc_min"]
    sn = next((n for n in d["nodes"] if n.get("type") == "skill"), None)
    targets = {e.get("target") for e in d.get("edges", []) if e.get("type") == "skill_binding"}
    if sn and "n_dir_board" not in targets:
        d["edges"].append({"id": "e_skill_board", "type": "skill_binding",
                           "source": sn["id"], "target": "n_dir_board",
                           "skillVersion": RELAY_VER})
    for e in d.get("edges", []):
        if e.get("type") == "skill_binding":
            e["skillVersion"] = RELAY_VER
    r = req(f"/api/project/{PROJ}/workflow/definitions/{WID}",
            {"definition": d, "expectedRevision": d["revision"]}, "PUT")
    P(f"PUT ok={r.get('validation', {}).get('ok')}")

    # 4) compile + start
    r = req(f"/api/project/{PROJ}/workflow/definitions/{WID}/compile", {}, "POST")
    P(f"compile ok={r.get('ok')}")
    r = req(f"/api/project/{PROJ}/workflow/definitions/{WID}/runs",
            {"idempotencyKey": f"p53_{STORY_KEY}_run1"}, "POST")
    run = r.get("run") or {}
    P(f"run: {run.get('runId')} status: {run.get('status')}")

    EB.mkdir(parents=True, exist_ok=True)
    (EB / f"a1_{STORY_KEY}_setup_log.json").write_text(
        json.dumps({"story": STORY_KEY, "project": PROJ, "workflow": WID,
                    "runId": run.get("runId"), "started_at": t0,
                    "skill": [RELAY_SKILL, RELAY_VER], "log": log},
                   ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
