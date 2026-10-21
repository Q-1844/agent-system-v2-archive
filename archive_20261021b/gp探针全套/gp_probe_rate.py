# gp_probe_rate.py — SCRATCH（不提交）。
# 量化：①中毒会话（先有1轮真实编辑）中，琐碎小修改是否真的调工具；②提问 turn 是否被闸门干扰。
# 2 个夹具 × (1 投毒轮 + 2 小修改 + 1 提问) = 8 turn，全部磁盘核对。
import json, shutil, sys, time, io
from pathlib import Path
import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent
BASE = "http://localhost:8000"
SRC = ROOT / "projects" / "__sw_streamtest"
LOG = ROOT / "gp_probe_rate.txt"
log = io.StringIO()
def w(*a):
    line = " ".join(str(x) for x in a)
    print(line); log.write(line + "\n")

def make_fixture(name):
    dst = ROOT / "projects" / name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(SRC, dst)
    ad = dst / "output" / "agents"
    if ad.exists():
        shutil.rmtree(ad)
    pj = dst / "output" / "project.json"
    data = json.loads(pj.read_text(encoding="utf-8"))
    data["name"] = name
    pj.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    r = httpx.post(f"{BASE}/api/project/{name}/agents/sessions",
                   json={"agent_id": "script_writer", "scope_type": "project", "scope_id": name}, timeout=30)
    r.raise_for_status()
    return name, r.json()["session_id"]

def stream_turn(proj, sid, content):
    tools = []; result = None; err = None
    for _ in range(3):
        tools = []; result = None; err = None
        try:
            with httpx.stream("POST", f"{BASE}/api/project/{proj}/agents/sessions/{sid}/turn/stream",
                              json={"content": content, "thinking": False},
                              timeout=httpx.Timeout(connect=30, read=600, write=60, pool=30)) as resp:
                if resp.status_code != 200:
                    err = f"HTTP {resp.status_code}: {resp.read().decode('utf-8','replace')[:150]}"
                else:
                    for line in resp.iter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        payload = line[5:].strip()
                        if payload == "[DONE]":
                            break
                        try:
                            ev = json.loads(payload)
                        except Exception:
                            continue
                        t = ev.get("type")
                        if t in ("tool.completed", "tool.failed"):
                            tools.append(ev.get("name"))
                        elif t == "turn.completed":
                            result = ev.get("result")
                        elif t == "turn.failed":
                            err = ev.get("error")
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
        if err and "429" in str(err):
            w("  429，等45s"); time.sleep(45); continue
        break
    return tools, result, err

def disk(proj):
    d = json.loads((ROOT / "projects" / proj / "output" / "project.json").read_text(encoding="utf-8"))
    sc = {s["scene_id"]: s for s in d["scenes"]}
    return sc

POISON_A = "请把 s02 这个故事段的 summary 改写得更生动、更有画面感一些，只改 s02 这一段，其它段不要动。"
POISON_B = "请给 s09 这个故事段的出场角色加上「邻居」，只改 s09，其它段不要动。"
TASKS = [
    ("小改-时段字段", "请把第 4 个故事段的时段（time_of_day）改成「清晨」，只改这一段，其它不要动。"),
    ("小改-两段加角色", "请给 s01 和 s05 两个故事段的出场角色都加上「奶奶」，两个段一起改完，其它段不要动。"),
    ("提问-要看法", "不用修改任何内容，只告诉我你的看法：你觉得这个故事目前有什么问题？"),
]

stats = {"tool_ok": 0, "tool_none": 0, "chat_ok": 0, "chat_bad": 0}
for fx, (fxname, poison) in enumerate([("__sw_rate_A", POISON_A), ("__sw_rate_B", POISON_B)], start=1):
    proj, sid = make_fixture(fxname)
    w(f"\n##### 夹具{fx} {fxname} #####")
    tools, res, err = stream_turn(proj, sid, poison)
    sc = disk(proj)
    w(f"[投毒轮] tools={tools} err={err} s02/s09 变化检查: s09chars={sc['s09'].get('characters')}")
    time.sleep(4)
    for tag, content in TASKS:
        tools, res, err = stream_turn(proj, sid, content)
        sc = disk(proj)
        reply = ((res or {}).get("assistant_message") or "")
        intent = (res or {}).get("intent")
        n_tools = len(tools)
        s04_tod = sc["s04"].get("time_of_day")
        grandma = ("奶奶" in (sc["s01"].get("characters") or [])) and ("奶奶" in (sc["s05"].get("characters") or []))
        if tag.startswith("小改"):
            if tag == "小改-时段字段":
                landed = (s04_tod == "清晨")
            else:
                landed = grandma
            verdict = "✅真调工具且落盘" if (n_tools > 0 and landed) else ("❌零工具假成功" if n_tools == 0 else "⚠️调了工具但未达预期")
            if n_tools > 0 and landed: stats["tool_ok"] += 1
            else: stats["tool_none"] += 1
        else:
            bad = ("没有真正执行修改" in reply) or ("请再说一次" in reply) or n_tools > 0
            verdict = "✅正常聊天回答" if not bad else "❌被闸门干扰/被迫调工具"
            if not bad: stats["chat_ok"] += 1
            else: stats["chat_bad"] += 1
        w(f"[{tag}] tools={tools} intent={intent} {verdict}")
        w(f"   磁盘: s04时段={s04_tod!r} s01/s05有奶奶={grandma}")
        w(f"   回复({len(reply)}字): {reply[:120]}")
        time.sleep(4)

w(f"\n===== 量化结果：小修改 真调工具 {stats['tool_ok']}/{stats['tool_ok']+stats['tool_none']}；"
  f"提问 正常回答 {stats['chat_ok']}/{stats['chat_ok']+stats['chat_bad']} =====")
LOG.write_text(log.getvalue(), encoding="utf-8")
w("[done]")
