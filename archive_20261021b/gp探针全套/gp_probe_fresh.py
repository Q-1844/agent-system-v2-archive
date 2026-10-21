# gp_probe_fresh.py — SCRATCH（不提交）。
# 决定性实验：P2/P3/P4「零工具假成功」到底是 (a)模型真没发 tool_call，还是 (b)流式解析丢了 tool_call？
#   实验1：全新会话【第1条消息】= 小修改，走【流式】 /turn/stream
#   实验2：全新会话【第1条消息】= 小修改，走【非流式】 /turn
#   实验3：全新会话流式，第1轮先做一个真实成功的小编辑，第2轮再发小修改（复现探针的中毒顺序）
import json, shutil, sys, time, io
from pathlib import Path
import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent
BASE = "http://localhost:8000"
SRC = ROOT / "projects" / "__sw_streamtest"
LOG = ROOT / "gp_probe_fresh.txt"
log = io.StringIO()
def w(*a):
    line = " ".join(str(x) for x in a)
    print(line); log.write(line + "\n")

P2 = "请把第 4 个故事段的时段（time_of_day）改成「清晨」，只改这一段，其它不要动。"
P3 = "请给 s01 和 s05 两个故事段的出场角色都加上「奶奶」，两个段一起改完，其它段不要动。"
T1 = "请把 s02 这个故事段的 summary 改写得更生动、更有画面感一些，只改 s02 这一段，其它段不要动。"

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
                   json={"agent_id": "script_writer", "scope_type": "project", "scope_id": name},
                   timeout=30)
    r.raise_for_status()
    return name, r.json()["session_id"]

def stream_turn(proj, sid, content, tag):
    tools = []; result = None; err = None
    try:
        with httpx.stream("POST", f"{BASE}/api/project/{proj}/agents/sessions/{sid}/turn/stream",
                          json={"content": content, "thinking": False},
                          timeout=httpx.Timeout(connect=30, read=600, write=60, pool=30)) as resp:
            if resp.status_code != 200:
                err = f"HTTP {resp.status_code}: {resp.read().decode('utf-8','replace')[:200]}"
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
                    if t == "tool.started":
                        tools.append(("started", ev.get("name")))
                    elif t == "tool.completed":
                        tools.append(("ok", ev.get("name")))
                    elif t == "tool.failed":
                        tools.append(("FAIL", ev.get("name"), (ev.get("error") or "")[:60]))
                    elif t == "tool.pending":
                        tools.append(("pending", ev.get("name")))
                    elif t == "turn.completed":
                        result = ev.get("result")
                    elif t == "turn.failed":
                        err = ev.get("error")
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
    return tools, result, err

def nonstream_turn(proj, sid, content):
    r = httpx.post(f"{BASE}/api/project/{proj}/agents/sessions/{sid}/turn",
                   json={"content": content}, timeout=httpx.Timeout(connect=30, read=600, write=60, pool=30))
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}: {r.text[:200]}"
    return r.json(), None

def disk_state(proj):
    d = json.loads((ROOT / "projects" / proj / "output" / "project.json").read_text(encoding="utf-8"))
    sc = {s["scene_id"]: s for s in d["scenes"]}
    return {"s04_tod": sc["s04"].get("time_of_day"),
            "s01_chars": sc["s01"].get("characters"),
            "s05_chars": sc["s05"].get("characters")}

def report(tag, proj, tools, result, err):
    w(f"\n{'='*70}\n{tag}")
    if err:
        w("  ERROR:", err); return
    reply = (result or {}).get("assistant_message") or ""
    trace = [(t.get("tool"), t.get("result")) for t in ((result or {}).get("trace") or [])]
    w(f"  intent={(result or {}).get('intent')} write_attempts={(result or {}).get('receipts') and len((result or {}).get('receipts'))}")
    w(f"  SSE工具事件: {tools}")
    w(f"  result.trace: {trace}")
    w(f"  回复({len(reply)}字): {reply[:150]}")
    w(f"  磁盘: {disk_state(proj)}")

# ---- 实验1：全新会话 + 流式 + 第1条就是小修改 P2 ----
p1, s1 = make_fixture("__sw_fresh_stream")
w(f"[setup] 实验1 项目={p1} 会话={s1}（流式，首条=P2小修改）")
for attempt in range(3):
    tools, result, err = stream_turn(p1, s1, P2, "E1")
    if err and "429" in str(err):
        w("  429，等45s重试"); time.sleep(45); continue
    break
report("实验1：全新会话/流式/首条小修改(P2)", p1, tools, result, err)
time.sleep(5)

# ---- 实验2：全新会话 + 非流式 + 第1条就是小修改 P3 ----
p2, s2 = make_fixture("__sw_fresh_nonstream")
w(f"[setup] 实验2 项目={p2} 会话={s2}（非流式，首条=P3小修改）")
result2, err2 = None, None
for attempt in range(3):
    result2, err2 = nonstream_turn(p2, s2, P3)
    if err2 and "429" in str(err2):
        w("  429，等45s重试"); time.sleep(45); continue
    break
report("实验2：全新会话/非流式/首条小修改(P3)", p2, None, result2, err2)
time.sleep(5)

# ---- 实验3：全新会话 + 流式 + 先真实成功1轮，再发小修改 P2 ----
p3, s3 = make_fixture("__sw_poisoned")
w(f"[setup] 实验3 项目={p3} 会话={s3}（流式，第1轮真实编辑→第2轮小修改）")
for attempt in range(3):
    tools_a, res_a, err_a = stream_turn(p3, s3, T1, "E3a")
    if err_a and "429" in str(err_a):
        w("  429，等45s重试"); time.sleep(45); continue
    break
report("实验3a：第1轮 真实编辑(s02改写)", p3, tools_a, res_a, err_a)
time.sleep(5)
for attempt in range(3):
    tools_b, res_b, err_b = stream_turn(p3, s3, P2, "E3b")
    if err_b and "429" in str(err_b):
        w("  429，等45s重试"); time.sleep(45); continue
    break
report("实验3b：第2轮 小修改(P2 改s04时段) ← 关键", p3, tools_b, res_b, err_b)

LOG.write_text(log.getvalue(), encoding="utf-8")
w(f"\n[done] {LOG}")
