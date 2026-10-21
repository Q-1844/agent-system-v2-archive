# -*- coding: utf-8 -*-
"""探查 Producer 对扩展意图 schema（remove/fill）的原始输出。"""
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

PROJ = "我的动画短片"
BASE = "http://127.0.0.1:8000"


def req(path, data=None, timeout=180):
    r = urllib.request.Request(
        BASE + path,
        data=json.dumps(data).encode("utf-8") if data is not None else None,
        headers={"Content-Type": "application/json"},
        method="POST" if data is not None else "GET",
    )
    return json.loads(urllib.request.urlopen(r, timeout=timeout).read().decode("utf-8"))


qp = urllib.request.quote(PROJ)
sessions = req(f"/api/project/{qp}/agents/sessions")["sessions"]
prod = [s for s in sessions if s["agent_id"] == "producer"]
sid = prod[0]["session_id"] if prod else req(
    f"/api/project/{qp}/agents/sessions",
    {"agent_id": "producer", "scope_type": "project", "scope_id": PROJ},
)["session_id"]
print("SID=" + sid)

prompt = "\n".join([
    "你是「工作流搭建助手」的需求解析器。这是纯文本生成任务：不要调用任何工具、不要执行任何修改、不要声称已执行任何操作；理解需求后只输出一个 JSON 对象，不要输出 JSON 以外的任何文字。",
    "",
    "可用注册项（ref 只能取自这里）：",
    "Agent: producer(总协调), script_writer(剧本/编剧), character_designer(角色/资源/造型/道具), scene_designer(场景), director(导演/分镜), assembly(成片/装配/剪辑)",
    "Skill: full-story-relay-calibration(接力/校准/连续性), keyframes-bridge-repair(桥/keyframes/过渡)",
    "",
    "输出 schema：",
    "{",
    '  "chain": ["script_writer", "character_designer"],  // 按执行顺序的 Agent ref 数组；用户没表达链就给 []',
    '  "reviews": [{"after": "director", "before": "assembly", "label": "分镜抽检", "count": 1}],  // 在 after 与 before 之间插 count 道人工审核；before 可省略=追加在 after 之后；无审核给 []',
    '  "bindings": [{"skill": "full-story-relay-calibration", "agent": "director"}],  // 无绑定给 []',
    '  "withBoundary": false,  // 仅当用户明确要求首尾「开始/结束」边界时才为 true，否则保持 false',
    '  "remove": {  // 删除/解绑/断开类操作；用户没表达删除就整个省略',
    '    "agents": ["director"],',
    '    "skills": ["keyframes-bridge-repair"],',
    '    "reviews": "all",  // "all"=删全部审核；或 [{"after": "director", "before": "assembly"}] 只删这两站之间的',
    '    "boundaries": ["start"],',
    '    "bindings": [{"skill": "full-story-relay-calibration", "agent": "director"}],  // 解绑（节点保留）；agent 省略=解绑全部',
    '    "connections": [{"from": "script_writer", "to": "character_designer"}]  // 断开执行连线',
    "  },",
    '  "fill": [{"target": "review", "after": "director", "label": "分镜抽检", "instructions": "重点查运镜与角色一致性", "reviewer": "制作人"}],  // 给已有审核填内容；after=定位某 Agent 之后的审核，缺省=第一道；没填内容就省略',
    '  "note": "一句话说明你的理解"',
    "}",
    "注意：ref 只能取自上面的注册项清单；用户提到清单外的新职责时，不要发明新 ref——在 note 里说明该职责应归入哪个现有 Agent（如旁白/配音归 assembly）。",
    "",
    "当前画布已有节点概要：script_writer, character_designer, scene_designer, director, assembly, skill:full-story-relay-calibration, review, review, end",
    "用户需求：把导演和装配之间的两道审核删掉，然后重新在导演和装配之间插一道审核，审核说明写「重点检查镜头衔接」，审核者写「分镜组长」",
    "",
    "只输出 JSON。",
])

turn = req(
    f"/api/project/{qp}/agents/sessions/{sid}/turn",
    {"content": prompt},
)
msg = turn.get("assistant_message") or ""
print("LINKED=" + json.dumps(turn.get("linked_task_ids", []), ensure_ascii=False))
print("RAW_MESSAGE_BEGIN")
print(msg[:1500])
print("RAW_MESSAGE_END")
