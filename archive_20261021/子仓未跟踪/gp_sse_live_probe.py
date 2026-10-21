# scratch 活体探针（不入库）：打真实 uvicorn(:8000)。
# 复制一个带段项目 -> 开 /events SSE 长连接(daemon 线程) -> 跑真实 /turn/stream 写一段 ->
# 观察 SSE 是否收到 snapshot/locked/story.changed/unlocked。
import json, os, shutil, sys, threading, time
sys.stdout.reconfigure(encoding="utf-8")
import httpx

BASE = "http://127.0.0.1:8000"
PROJ = "__sw_sse_probe"

# 1. 找一个 6 段的源项目，复制成探针项目
src = None
for name in os.listdir("projects"):
    pj = os.path.join("projects", name, "output", "project.json")
    if os.path.exists(pj):
        try:
            d = json.load(open(pj, encoding="utf-8"))
            if len(d.get("scenes", [])) == 6 and name.startswith("__sw_ab"):
                src = name
                break
        except Exception:
            pass
assert src, "no source project"
dst_dir = os.path.join("projects", PROJ)
if os.path.exists(dst_dir):
    shutil.rmtree(dst_dir)
shutil.copytree(os.path.join("projects", src), dst_dir)
pj_path = os.path.join(dst_dir, "output", "project.json")
d = json.load(open(pj_path, encoding="utf-8"))
d["name"] = PROJ
json.dump(d, open(pj_path, "w", encoding="utf-8"), ensure_ascii=False)
print(f"[probe] copied {src!r} -> {PROJ}, scenes=", len(d["scenes"]))

frames = []
stop = threading.Event()

def sse_loop():
    try:
        with httpx.stream("GET", f"{BASE}/api/project/{PROJ}/events", timeout=httpx.Timeout(60.0)) as r:
            buf = ""
            for line in r.iter_lines():
                if stop.is_set():
                    break
                if line.startswith("data:"):
                    try:
                        frames.append(json.loads(line[5:].strip()))
                    except Exception as e:
                        frames.append({"_parse_error": str(e), "raw": line[:80]})
    except Exception as e:
        frames.append({"_sse_error": repr(e)})

t = threading.Thread(target=sse_loop, daemon=True)
t.start()
time.sleep(1.0)

# 2. 建 script_writer 会话
sess = httpx.post(f"{BASE}/api/project/{PROJ}/agents/sessions",
                  json={"agent_id": "script_writer", "scope_type": "project", "scope_id": PROJ},
                  timeout=30)
sid = sess.json()["session_id"]
print("[probe] session", sid)

# 3. 跑流式 turn（要求确定写一段）
print("[probe] starting turn...")
t0 = time.time()
final = ""
tool_events = []
final_result = None
with httpx.stream("POST",
                  f"{BASE}/api/project/{PROJ}/agents/sessions/{sid}/turn/stream",
                  json={"content": "现在就在第二个故事段后面【新建】一个故事段，用 story.create 工具真正创建，"
                                   "不要只说话。新段内容：一个沉默的旅人在雨夜推开了驿站的木门。",
                        "thinking": False},
                  timeout=httpx.Timeout(300.0)) as r:
    for line in r.iter_lines():
        if line.startswith("data:"):
            try:
                ev = json.loads(line[5:].strip())
                if ev.get("type") == "tool.started":
                    tool_events.append(f"start:{ev.get('name')}")
                elif ev.get("type") == "tool.completed":
                    tool_events.append(f"done:{ev.get('name')}:ok={ev.get('ok')}")
                elif ev.get("type") in ("turn.completed", "turn.failed"):
                    final = ev.get("type")
                    final_result = ev.get("result")
            except Exception:
                pass
print(f"[probe] turn done in {time.time()-t0:.1f}s -> {final}")
print("[probe] tool events:", tool_events)
if final_result:
    print("[probe] intent:", final_result.get("intent"),
          "| created:", final_result.get("created"),
          "| receipts:", [(x.get("operation"), x.get("ok"), x.get("verified")) for x in final_result.get("receipts", [])])
import json as _j
n_scenes = len(_j.load(open(os.path.join(dst_dir, "output", "project.json"), encoding="utf-8"))["scenes"])
print("[probe] scenes on disk:", n_scenes)

# 等 SSE 把解锁事件送到
time.sleep(3.0)
stop.set()
t.join(timeout=5)

print("\n=== SSE /events frames ===")
for f in frames:
    t_ = f.get("type", "?")
    if t_ == "snapshot":
        print(f"  snapshot locks={[l.get('resource') for l in f.get('locks', [])]}")
    elif t_ in ("resource.locked", "resource.unlocked", "story.changed"):
        print(f"  {t_} resource={f.get('resource')} op={f.get('operation','')}")
    else:
        print("  ", t_, list(f.keys()))

types = [f.get("type") for f in frames]
print("\nLOCKED:", "resource.locked" in types)
print("UNLOCKED:", "resource.unlocked" in types)
li = types.index("resource.locked") if "resource.locked" in types else -1
ui = types.index("resource.unlocked") if "resource.unlocked" in types else -1
print("order locked<unlock:", 0 <= li < ui)
