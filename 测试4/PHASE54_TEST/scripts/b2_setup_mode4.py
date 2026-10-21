# -*- coding: utf-8 -*-
"""Phase 54 B2：模式④ Producer 主执行+困难上交（granted + delegate 上交通道）。
- 新项目 P54_M3（复用 M《第三道回声》故事文本，对照基线=P53_M 六员链 4h40m/94s）；
- grant 五族工具（同 B1）；目标=主执行，真实困难才上交 specialist（保留 delegate）；
- 单 producer 会话一次性下发完整生产目标；turn 阻塞长任务建议后台跑。
用法：python b2_setup_mode4.py SETUP / GO
"""
import json, sys, time, urllib.request, pathlib

BASE = "http://127.0.0.1:8000"
PROJ = "P54_M3"
ROOT = pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流\测试4\PHASE54_TEST")
EB = ROOT / "evidence"
FAMILIES = ["script_writer", "character_designer", "scene_designer",
            "director", "assembly"]

OBJECTIVE = """【工作方法】开始执行前先 skill.load "full-story-relay-calibration" 并严格遵循其制作方法（三查判据/时长配方/尾帧接续链策略均以 Skill v1.6.0 正文为准）。

【任务】你是本片主执行者（模式④）：你被 scoped grant 授权直接执行全部生产工具族。优先亲自完成以下全流程；仅当某一步**真实卡住**（同一问题连续 3 次真实失败，或需要你工具面之外的专项能力）才用对应 *.delegate 上交给专业 Agent，并在总结中列出上交清单与原因：
① 剧本：按下方【故事目标】写 story 六段（每段：剧情任务/起始状态/主动作/结果状态）。
② 资源：新建写实角色 探索者林远/探索者苏然/标本库异常人形（外形互相明确区分，写实电影质感），用 resource.look.prepare 完成造型参考生产（真实生成+审批）。
③ 场景：建立「地下设施：入口走廊（红色管道标志）+标本库+防护门」空间（走廊/库房两地点或单地点多锚点，由你判断）；若某视图反复不合格，如实跳过场景锚并记录。
④ 分镜：六段各 1-2 候选镜（共 6-12 镜），逐镜绑定 look/场景资源；生成首帧候选并按三查判据选定。
⑤ 视频：逐镜真实生成（静态 5s/动态 8s/高运动 10s；镜间尾帧接续或 intentional cut 按 Skill 判定）；逐镜收货核对首中尾帧，不合格先修再交。
⑥ 装配：六段各选 1 镜组成 sequence 并渲染成片候选（目标 30-42 秒，横屏 16:9）。
⑦ 汇报：总结（真实回执引用/上交清单/跳过项/遗留问题）。

【故事目标】写实悬疑短片《第三道回声》：有异常生物活动的地下标本库，两名探索者进入找回记录匣，听到第三道回声，误以为同伴落后，直到同伴从前方回答，才意识到怪物正在模仿脚步。六段：①两人进入走廊，交代手电归属、标志物（红色管道）和前进方向；②听到额外脚步，一人回头确认同伴位置；③正常转入相邻标本库，找到记录匣；④怪物出现在可解释的位置，模仿脚步的线索成立（最多一个个体）；⑤两人带着记录匣撤向防护门，一人操作关门，关键动作和接触可见；⑥门关闭、两人及记录匣均在安全一侧；门外再响起第三道回声，形成悬疑结尾。角色=林远（深色外套+手电）与苏然（橙色反光背心+短发）；怪物=瘦长人形剪影（同一实体、最多一个个体，以剪影/远景出现即可，不要求实体直出）。

【纪律】两名探索者身份不串（不得分身）；怪物始终同一实体且最多一个个体；手电与记录匣归属固定（手电=林远，记录匣=苏然取得）；光源方向连续；关门动作与结果可见；低照度不掩盖关键动作；无画外旁白、无主动背景音乐。"""


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
                {"families": FAMILIES, "reason": "P54 B2 mode4 主执行+困难上交测试",
                 "granted_by": "executor-daili", "ttl_s": 43200}, "POST")
        gid = (g.get("grant") or {}).get("grantId")
        s = req(f"/api/project/{PROJ}/agents/sessions",
                {"agent_id": "producer", "scope_type": "project",
                 "scope_id": PROJ}, "POST")
        sid = s.get("session_id") or s.get("sessionId") or s.get("id")
        print("grant:", gid, "| session:", sid)
        (EB / "b2_state.json").write_text(json.dumps(
            {"project": PROJ, "grantId": gid, "sessionId": sid,
             "startedAt": time.time()}, ensure_ascii=False, indent=1),
            encoding="utf-8")
    elif mode == "GO":
        st = json.load(open(EB / "b2_state.json", encoding="utf-8"))
        sid = st["sessionId"]
        t0 = time.time()
        r = req(f"/api/project/{PROJ}/agents/sessions/{sid}/turn",
                {"content": OBJECTIVE, "thinking": True}, "POST", timeout=7200)
        took = time.time() - t0
        (EB / "b2_turn_result.json").write_text(json.dumps(
            r, ensure_ascii=False, indent=1)[:2000000], encoding="utf-8")
        print(f"turn done in {took/60:.1f}min -> evidence/b2_turn_result.json")


if __name__ == "__main__":
    main()
