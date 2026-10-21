# -*- coding: utf-8 -*-
"""Phase 53 B2 能力探针（无媒体生成）：Producer 会话内 skill.load + 工具面对账取证。
探针问题：
  P1 Producer 能否加载正式 workflow Skill（记录 actor/skill/version/加载证据）
  P2 capability_check 对 Producer 的真实结论（缺哪些工具，是否如实 declared）
  P3 Producer 对「直接执行 shot 生产」的自主响应（不预设答案：让它自己判断并陈述路径）
  P4 skill trace 是否落盘（output/agents/skills/trace.jsonl）
不调用任何生成工具；不修改任何 canonical。
"""
import json, sys, time, urllib.request

BASE = "http://127.0.0.1:8000"
PROJ = "P53_PROBE"
OUT = r"c:\Users\曹文淇\Desktop\ai工作流\测试4\PHASE53_TEST\evidence\b2_probe_result.json"

def api(method, path, body=None, timeout=600):
    req = urllib.request.Request(BASE + path, method=method,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

ev = {"started_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "project": PROJ}

# 1) 建 Producer 会话
s = api("POST", f"/api/project/{PROJ}/agents/sessions",
        {"agent_id": "producer", "scope_type": "project", "scope_id": ""})
sid = s["session_id"] if isinstance(s, dict) and "session_id" in s else s.get("id", s)
ev["session"] = s
print("[1] producer session:", sid)

# 2) 探针 turn（thinking=true 与正式运行一致；不喂逐镜技术答案）
prompt = (
    "【Phase 53 B2 能力探针·只读，不生成】请依次完成并如实汇报：\n"
    "1. 调用 skill.load 加载 full-story-relay-calibration，报告你收到的 capability_check "
    "结果（若声明 missing，逐项列出工具名）。\n"
    "2. 基于该 Skill 的总体工作流：如果现在要求你【不委派、由你自己直接】完成某场景 "
    "6 个镜头的首帧图与视频生成并保存候选，你的工具面是否支持？请逐个所需步骤说明"
    "「我有该工具/我没有该工具只能 delegate」，不得虚构工具名。\n"
    "3. 结论：把你的最终路径选择（直接执行 / 必须委派 / 受阻）和理由写成三行以内。"
)
t0 = time.time()
turn = api("POST", f"/api/project/{PROJ}/agents/sessions/{sid}/turn",
           {"content": prompt, "thinking": True}, timeout=900)
ev["turn_elapsed_s"] = round(time.time() - t0, 1)
msg = turn.get("assistant_message") or {}
ev["assistant_status"] = msg.get("status")
ev["assistant_text"] = (msg.get("content") or "")[:4000]
ev["events_n"] = len(turn.get("events") or [])
ev["events_names"] = [e.get("type") or e.get("name") for e in (turn.get("events") or [])][:60]
print("[2] turn done in", ev["turn_elapsed_s"], "s; status:", ev["assistant_status"])

# 3) skill trace 落盘核验
try:
    with open("output/agents/skills/trace.jsonl", encoding="utf-8") as f:
        lines = [json.loads(x) for x in f if x.strip()]
    ev["skill_trace_tail"] = lines[-8:]
    ev["skill_trace_total"] = len(lines)
except Exception as e:
    ev["skill_trace_error"] = str(e)
print("[3] skill trace entries:", ev.get("skill_trace_total", "ERR"))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(ev, f, ensure_ascii=False, indent=1)
print("saved ->", OUT)
