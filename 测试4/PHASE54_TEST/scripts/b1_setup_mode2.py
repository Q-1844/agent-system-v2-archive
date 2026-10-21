# -*- coding: utf-8 -*-
"""Phase 54 B1：模式② 单 Producer 全流程（granted）setup+驱动。
- 新项目 P54_M2（复用 F《灰塔》故事文本，对照基线=P53_F 六员链 4h48m/103s）；
- scoped grant 五族工具（ttl 12h，审计落盘）；
- 单 producer 会话一次性下发完整生产目标（D-12 教训：完整载荷）。
用法：python b1_setup_mode2.py          # 建项目+授权+建会话
      python b1_setup_mode2.py GO      # 发起生产 turn（阻塞长任务，建议后台跑）
"""
import json, sys, time, urllib.request, pathlib

BASE = "http://127.0.0.1:8000"
PROJ = "P54_M2"
ROOT = pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流\测试4\PHASE54_TEST")
EB = ROOT / "evidence"
FAMILIES = ["script_writer", "character_designer", "scene_designer",
            "director", "assembly"]

OBJECTIVE = """【工作方法】开始执行前先 skill.load "full-story-relay-calibration" 并严格遵循其制作方法（三查判据/时长配方/尾帧接续链策略均以 Skill v1.6.0 正文为准）。

【任务】你被项目级 scoped grant 授权直接执行全部生产工具族（script_writer/character_designer/scene_designer/director/assembly）。请独自完成写实战争悬疑短片《灰塔的错误信号》全流程生产，无需委派：
① 剧本：按下方【故事目标】写 story 六段（每段写清：剧情任务/起始状态/主动作/结果状态）。
② 资源：新建写实角色 队长/通信员/守军（装备轮廓互相明确区分，写实电影质感），用 resource.look.prepare 为各角色完成造型参考生产（含真实生成参考图与审批）。
③ 场景：建立「山口要塞外区域」单地点（闸门/出发掩体/中间掩体/控制箱+信号灯/进攻方向锚点+hero 视角+各段实例状态图）。若某视图生成反复不合格（连续多次仍不过审），允许如实跳过场景锚直接进入分镜——跳过决定写进最终汇报，不得悄悄跳过。
④ 分镜：六段各 2 个候选镜（共 12 镜左右，可按剧情需要 1-3 个/段），逐镜绑定角色 look 与场景资源；生成首帧候选并按三查判据选定。
⑤ 视频：逐镜真实生成视频（静态 5s/动态 8s/高运动 10s；镜间用尾帧接续或 intentional cut，由你按 Skill 判定）；每镜收货后核对回执与首中尾帧，不合格先修再交。
⑥ 装配：六段各选 1 镜组成 sequence 并渲染成片候选（目标成片 30-42 秒，横屏 16:9）。
⑦ 汇报：全部完成后给出总结——各步骤引用真实工具回执（changed_refs）、跳过项与原因、遗留问题；不要声称未发生的操作。

【故事目标】写实战争悬疑短片：虚构战争中的山口要塞，两名突击队员在进攻前发现约定信号异常；接近外侧控制点开启闸门时发现信号由守军伪造，最终切断假信号并取得进攻入口。六段：①交代要塞、封闭入口、掩体与两名突击队员位置；②通信员看到异常信号（约定信号不对），队长决定靠近控制点；③两人向指定掩体移动，行动方向可解释；④遭遇守军阻拦（守军短暂出现），队长掩护通信员接近控制箱，行为有因果；⑤通信员操作装置切断假信号，闸门开始打开；⑥两人进入已打开的入口，后续进攻具备条件，假信号悬念得到回应。角色=队长（深灰战术装+夜视盔+大方形背包）与通信员（橄榄色战术装+圆润软盔+电台天线）；守军=旧式制服大檐帽栓动步枪，非主角。控制箱/信号灯/闸门状态（闭→开）要能被看见。

【纪律】两名突击队员身份不串（不得分身）；守军短暂出现不计入主体人数；手部接触（装置操作/掩护动作）过程完整；闸门从闭到开状态可解释；行动方向与掩体空间关系连续；无画外旁白、无主动背景音乐，保留合格原生环境声。"""


def req(path, body=None, method="GET", timeout=120):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data,
                               headers={"Content-Type": "application/json"},
                               method=method)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.load(resp)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "SETUP"
    EB.mkdir(parents=True, exist_ok=True)
    if mode == "SETUP":
        try:
            req(f"/api/projects/create?name={PROJ}&render_family=photorealistic"
                f"&art_direction=%E5%86%99%E5%AE%9E%E7%9F%AD%E7%89%87", None, "POST")
            print(f"project {PROJ} created")
        except Exception as e:
            print(f"create: {e}")
        req(f"/api/project/{PROJ}/native-av-settings",
            {"spoken_language": "Mandarin Chinese"}, "PUT")
        g = req(f"/api/project/{PROJ}/agents/producer/grant",
                {"families": FAMILIES, "reason": "P54 B1 mode2 单Producer全流程测试",
                 "granted_by": "executor-daili", "ttl_s": 43200}, "POST")
        gid = (g.get("grant") or {}).get("grantId")
        print("grant:", gid, (g.get("grant") or {}).get("families"))
        s = req(f"/api/project/{PROJ}/agents/sessions",
                {"agent_id": "producer", "scope_type": "project",
                 "scope_id": PROJ}, "POST")
        sid = s.get("session_id") or s.get("sessionId") or s.get("id")
        print("session:", sid)
        (EB / "b1_state.json").write_text(json.dumps(
            {"project": PROJ, "grantId": gid, "sessionId": sid,
             "startedAt": time.time()}, ensure_ascii=False, indent=1),
            encoding="utf-8")
    elif mode == "GO":
        st = json.load(open(EB / "b1_state.json", encoding="utf-8"))
        sid = st["sessionId"]
        t0 = time.time()
        r = req(f"/api/project/{PROJ}/agents/sessions/{sid}/turn",
                {"content": OBJECTIVE, "thinking": True}, "POST", timeout=7200)
        took = time.time() - t0
        (EB / "b1_turn_result.json").write_text(json.dumps(
            r, ensure_ascii=False, indent=1)[:2000000], encoding="utf-8")
        print(f"turn done in {took/60:.1f}min -> evidence/b1_turn_result.json")


if __name__ == "__main__":
    main()
