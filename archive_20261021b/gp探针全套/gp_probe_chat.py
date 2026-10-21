# gp_probe_chat.py — SCRATCH（不提交）。
# 实时探针：真后端(localhost:8000) + 真 Agnes，跑【局部修改矩阵】+【纯聊天/回顾矩阵】，
# 每 turn 记录：SSE 工具事件、最终回复、session meta.trace、读工具读取量估算、全文复现率。
import json, shutil, sys, time, re, io
from pathlib import Path
import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent
BASE = "http://localhost:8000"
SRC = ROOT / "projects" / "__sw_streamtest"
DST_NAME = "__sw_probe_ctx"
DST = ROOT / "projects" / DST_NAME
LOG = ROOT / "gp_probe_chat.txt"
log = io.StringIO()
def w(*a):
    line = " ".join(str(x) for x in a)
    print(line); log.write(line + "\n")

# ---------- 夹具：拷贝 streamtest（2329字正文 + 10段），清空 agents 历史 ----------
if DST.exists():
    shutil.rmtree(DST)
shutil.copytree(SRC, DST)
agents_dir = DST / "output" / "agents"
if agents_dir.exists():
    shutil.rmtree(agents_dir)
pj = DST / "output" / "project.json"
data = json.loads(pj.read_text(encoding="utf-8"))
data["name"] = DST_NAME
pj.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
w(f"[setup] 夹具就绪：{DST_NAME}，story_len={len(data.get('story_text') or '')}，scenes={len(data.get('scenes') or [])}")

# ---------- 建 script_writer project 会话 ----------
r = httpx.post(f"{BASE}/api/project/{DST_NAME}/agents/sessions",
               json={"agent_id": "script_writer", "scope_type": "project", "scope_id": DST_NAME},
               timeout=30)
r.raise_for_status()
sid = r.json()["session_id"]
w(f"[setup] session={sid}")

def snapshot():
    d = json.loads(pj.read_text(encoding="utf-8"))
    scenes = {s["scene_id"]: s for s in (d.get("scenes") or [])}
    return {"story_len": len(d.get("story_text") or ""),
            "scenes": scenes, "order": [s["scene_id"] for s in d.get("scenes") or []]}

def read_volume(trace, snap):
    """估算读工具返回给模型的字符量。"""
    vol = {}
    for t in trace:
        tool = t.get("tool")
        if tool == "script.read":
            vol["script.read"] = vol.get("script.read", 0) + snap["story_len"]
        elif tool == "story.list":
            size = sum(120 + len("".join(s.get("characters") or [])) for s in snap["scenes"].values())
            vol["story.list"] = vol.get("story.list", 0) + size
        elif tool == "story.read":
            sc = snap["scenes"].get(t.get("target"))
            size = len((sc or {}).get("summary") or "") + 80
            vol["story.read"] = vol.get("story.read", 0) + size
    return vol

def story_overlap(reply, snap):
    st = json.loads(pj.read_text(encoding="utf-8")).get("story_text") or ""
    sents = [s for s in re.split(r"[。！？\n]", st) if len(s.strip()) >= 8]
    hit = sum(1 for s in sents if s.strip() in reply) if sents else 0
    scene_heads = 0
    for sid, sc in snap["scenes"].items():
        sm = (sc.get("summary") or "").strip()
        if len(sm) >= 20 and sm[:int(len(sm)*0.6)] in reply:
            scene_heads += 1
    return (hit, len(sents), scene_heads, len(snap["scenes"]))

TURNS = [
    ("P1-单段指定id改写", "请把 s02 这个故事段的 summary 改写得更生动、更有画面感一些，只改 s02 这一段，其它段不要动。"),
    ("P2-第N段小字段", "请把第 4 个故事段的时段（time_of_day）改成「清晨」，只改这一段，其它不要动。"),
    ("P3-两段独立改", "请给 s01 和 s05 两个故事段的出场角色都加上「奶奶」，两个段一起改完，其它段不要动。"),
    ("P4-衔接段重写", "请重写第 3 段的 summary，让它和前后两段的衔接更自然（承上启下），只改第 3 段。"),
    ("P5-全局一致性", "请整体通读一遍所有故事段，如果发现明显的时间线或一致性问题就修正（保持原意、段数不变）；如果没有问题就直接告诉我没有。"),
    ("Q1-回顾做了什么", "你刚才都做了什么？用两三句话简单说一下就行，不用改任何东西。"),
    ("Q2-只要看法", "不用修改任何内容，只告诉我你的看法：你觉得这个故事目前有什么问题？"),
    ("Q3-几段讲什么", "现在一共有几段故事段？每段大概讲了什么？一句话一段就行，不用改东西。"),
    ("F1-制造失败", "请把故事段 s99 移动到末尾。"),
    ("Q4-为什么失败", "刚才为什么失败？上一次工具调用出了什么问题？解释一下原因就行，不用改任何东西。"),
    ("Q5-能看到正文吗", "不用改，我只是确认一下：你现在能看到完整的剧本正文吗？你是通过什么方式看到的？"),
]

results = []
for tag, content in TURNS:
    w("\n" + "=" * 78)
    w(f"[{tag}] U: {content}")
    t0 = time.time()
    tool_events = []
    completed = None
    failed = None
    for attempt in range(3):
        tool_events = []; completed = None; failed = None
        try:
            with httpx.stream("POST",
                              f"{BASE}/api/project/{DST_NAME}/agents/sessions/{sid}/turn/stream",
                              json={"content": content, "thinking": False},
                              timeout=httpx.Timeout(connect=30, read=600, write=60, pool=30)) as resp:
                if resp.status_code != 200:
                    body = resp.read().decode("utf-8", "replace")[:300]
                    w(f"  [HTTP {resp.status_code}] {body}")
                    failed = body
                    break
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
                        tool_events.append((ev.get("name"), True, (ev.get("summary") or "")[:50]))
                    elif t == "tool.failed":
                        tool_events.append((ev.get("name"), False, (ev.get("error") or "")[:50]))
                    elif t == "turn.completed":
                        completed = ev.get("result")
                    elif t == "turn.failed":
                        failed = ev.get("error")
        except Exception as e:
            failed = f"{type(e).__name__}: {e}"
        if failed and ("429" in str(failed) or "rate" in str(failed).lower()):
            w(f"  [429 rate limit，等 45s 重试 {attempt+1}/3] {failed}")
            time.sleep(45)
            continue
        break
    dt = time.time() - t0
    if completed:
        reply = completed.get("assistant_message") or ""
        intent = completed.get("intent")
        trace = completed.get("trace") or []
    else:
        reply = ""; intent = f"FAILED: {failed}"; trace = []
    snap = snapshot()
    vol = read_volume(trace, snap)
    ov = story_overlap(reply, snap)
    tool_seq = [f"{n}{'✓' if ok else '✗'}" for n, ok, _ in tool_events]
    w(f"  [{dt:.0f}s] intent={intent}")
    w(f"  tools({len(tool_seq)}): {tool_seq}")
    w(f"  读取量估算(字符): {vol}  合计≈{sum(vol.values())}")
    w(f"  回复长度: {len(reply)} 字；正文句子复现 {ov[0]}/{ov[1]}；整段摘要引用 {ov[2]}/{ov[3]} 段")
    w(f"  回复全文:\n{reply}")
    results.append({"tag": tag, "intent": intent, "tools": tool_seq, "vol": vol,
                    "reply_len": len(reply), "overlap": ov, "dt": dt})
    time.sleep(3)

w("\n" + "#" * 78)
w("汇总表：")
for r_ in results:
    w(f"  {r_['tag']:14s} intent={str(r_['intent']):28s} reads={r_['vol']} "
      f"reply={r_['reply_len']}字 overlap={r_['overlap'][0]}/{r_['overlap'][1]}句,{r_['overlap'][2]}/{r_['overlap'][3]}段 "
      f"tools={r_['tools']}")
LOG.write_text(log.getvalue(), encoding="utf-8")
w(f"\n[done] 日志已写 {LOG}")
