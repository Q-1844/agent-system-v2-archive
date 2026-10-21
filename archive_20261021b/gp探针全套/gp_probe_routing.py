# gp_probe_routing.py — SCRATCH（不提交）。
# 验证两块行为：①聊天/探讨不被强制工具/兜底文案；②故事段任务局部读取、不默认 script.read。
# 6 个指定场景，全新会话夹具（避开不在本次范围的长会话假成功问题）。
import json, shutil, sys, time, io
from pathlib import Path
import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent
BASE = "http://localhost:8000"
SRC = ROOT / "projects" / "__sw_streamtest"
LOG = ROOT / "gp_probe_routing.txt"
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
                        if t == "tool.completed":
                            tools.append((ev.get("name"), "ok" if ev.get("ok") else "fail"))
                        elif t == "tool.failed":
                            tools.append((ev.get("name"), "FAIL"))
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

def run(proj, sid, tag, content):
    w("\n" + "=" * 78)
    w(f"[{tag}] U: {content}")
    t0 = time.time()
    tools, res, err = stream_turn(proj, sid, content)
    dt = time.time() - t0
    reply = ((res or {}).get("assistant_message") or "")
    seq = [f"{n}{'✗' if s != 'ok' else ''}" for n, s in tools]
    reads = [n for n, _ in tools if n in ("script.read", "story.list", "story.read")]
    writes = [n for n, _ in tools if n not in ("script.read", "story.list", "story.read")]
    fallback = ("没有真正执行修改" in reply) or ("请再说一次你的需求" in reply)
    w(f"  [{dt:.0f}s] intent={(res or {}).get('intent')} err={err}")
    w(f"  工具序列: {seq}")
    w(f"  读工具: {reads}  | 写工具: {writes}")
    w(f"  script.read全文: {'是' if 'script.read' in reads else '否'}；兜底固定文案: {'是【异常】' if fallback else '否'}")
    w(f"  回复({len(reply)}字): {reply[:400]}")
    time.sleep(4)
    return {"tag": tag, "seq": seq, "reads": reads, "writes": writes,
            "full_read": "script.read" in reads, "fallback": fallback, "reply_len": len(reply)}

results = []

# A 会话：probe3（末尾加段）→ probe2（为什么刚才这么改）
pA, sA = make_fixture("__sw_route_A")
results.append(run(pA, sA, "probe3-末尾加段", "在故事最后增加一个故事段。"))
results.append(run(pA, sA, "probe2-解释为什么", "为什么你刚才这么改？解释一下你的思路就行，不用再改东西。"))

# B 会话：probe1（聊天问看法）
pB, sB = make_fixture("__sw_route_B")
results.append(run(pB, sB, "probe1-问结尾看法", "不用修改，你觉得目前结尾有什么问题？"))

# C 会话：probe4（第8段后插转折）
pC, sC = make_fixture("__sw_route_C")
results.append(run(pC, sC, "probe4-第8段后插转折", "在第 8 段后增加一段转折。"))

# D 会话：probe5（重写第8段）
pD, sD = make_fixture("__sw_route_D")
results.append(run(pD, sD, "probe5-重写第8段", "重写第 8 段，让它和前后剧情更连贯。"))

# E 会话：probe6（全篇节奏检查）
pE, sE = make_fixture("__sw_route_E")
results.append(run(pE, sE, "probe6-全篇节奏检查", "检查整篇故事的节奏和逻辑，告诉我你的发现。"))

w("\n" + "#" * 78)
w("汇总：")
for r in results:
    w(f"  {r['tag']:16s} 全文read={'是' if r['full_read'] else '否'} 兜底文案={'是【异常】' if r['fallback'] else '否'} "
      f"读={r['reads']} 写={r['writes']} 回复{r['reply_len']}字")
LOG.write_text(log.getvalue(), encoding="utf-8")
w("[done]")
