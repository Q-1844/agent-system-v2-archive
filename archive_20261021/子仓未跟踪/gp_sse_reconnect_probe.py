# scratch 活体探针（不入库）：模拟浏览器 EventSource 在锁定期断线/重连。
# 场景A：SSE 收到 locked 后断开 -> turn 结束后再重连 -> 新 snapshot 应为 locks=[]（清锁）。
# 场景B：SSE locked 后断开 -> 立即重连（turn 仍在跑）-> 新 snapshot 应有 lock，且之后收到 unlocked。
import json, os, shutil, sys, threading, time
sys.stdout.reconfigure(encoding="utf-8")
import httpx

BASE = "http://127.0.0.1:8000"
PROJ = "__sw_sse_reconn"

src = None
for name in os.listdir("projects"):
    pj = os.path.join("projects", name, "output", "project.json")
    if os.path.exists(pj):
        try:
            d = json.load(open(pj, encoding="utf-8"))
            if len(d.get("scenes", [])) == 6 and name.startswith("__sw_ab"):
                src = name; break
        except Exception: pass
dst = os.path.join("projects", PROJ)
if os.path.exists(dst): shutil.rmtree(dst)
shutil.copytree(os.path.join("projects", src), dst)
pjp = os.path.join(dst, "output", "project.json")
d = json.load(open(pjp, encoding="utf-8")); d["name"] = PROJ
json.dump(d, open(pjp, "w", encoding="utf-8"), ensure_ascii=False)

def turn_async(sid, boxes):
    try:
        with httpx.stream("POST", f"{BASE}/api/project/{PROJ}/agents/sessions/{sid}/turn/stream",
                          json={"content": "现在就在最后一个故事段后面【新建】一个故事段，用 story.create 真正创建，"
                                           "内容：山风穿过松林，吹散了夜行人斗篷上的尘土。", "thinking": False},
                          timeout=httpx.Timeout(300.0)) as r:
            for line in r.iter_lines():
                if line.startswith("data:"):
                    try:
                        ev = json.loads(line[5:].strip())
                        if ev.get("type") in ("turn.completed", "turn.failed"):
                            boxes["final"] = ev.get("type")
                    except Exception: pass
    except Exception as e:
        boxes["final"] = f"ERR {e!r}"

def first_snapshot(client):
    with client.stream("GET", f"{BASE}/api/project/{PROJ}/events", timeout=httpx.Timeout(30.0)) as r:
        for line in r.iter_lines():
            if line.startswith("data:"):
                try:
                    return json.loads(line[5:].strip())
                except Exception: pass

def collect_sse(stop_evt, saw, wait_type=None):
    """持续收 SSE 帧；wait_type 命中时把整个 saw 回填并返回。"""
    try:
        with httpx.stream("GET", f"{BASE}/api/project/{PROJ}/events", timeout=httpx.Timeout(60.0)) as r:
            for line in r.iter_lines():
                if stop_evt.is_set(): break
                if line.startswith("data:"):
                    try:
                        ev = json.loads(line[5:].strip())
                        saw.append(ev)
                        if wait_type and ev.get("type") == wait_type:
                            return
                    except Exception: pass
    except Exception as e:
        saw.append({"type": "_error", "e": repr(e)})

sess = httpx.post(f"{BASE}/api/project/{PROJ}/agents/sessions",
                  json={"agent_id": "script_writer", "scope_type": "project", "scope_id": PROJ}, timeout=30)
sid = sess.json()["session_id"]

print("=== 场景 B：locked 后断开，立即重连，观察新连接是否收到 unlock ===")
saw1 = []
stop1 = threading.Event()
got_lock = threading.Event()
def reader1():
    with httpx.stream("GET", f"{BASE}/api/project/{PROJ}/events", timeout=httpx.Timeout(60.0)) as r:
        for line in r.iter_lines():
            if stop1.is_set(): break
            if line.startswith("data:"):
                try:
                    ev = json.loads(line[5:].strip()); saw1.append(ev)
                    if ev.get("type") == "resource.locked": got_lock.set()
                except Exception: pass
t1 = threading.Thread(target=reader1, daemon=True); t1.start()
time.sleep(0.5)
boxes = {}
tt = threading.Thread(target=turn_async, args=(sid, boxes), daemon=True); tt.start()
got_lock.wait(20)
print("saw1 has locked:", any(e.get("type")=="resource.locked" for e in saw1))
time.sleep(0.3)
stop1.set()  # 断开 SSE1（模拟 EventSource 掉线）
time.sleep(0.5)
# 立即重连 SSE2，收到底（含 unlock 或 snapshot）
saw2 = []
stop2 = threading.Event()
t2 = threading.Thread(target=collect_sse, args=(stop2, saw2, "resource.unlocked"), daemon=True); t2.start()
tt.join(60)
print("turn final:", boxes.get("final"))
time.sleep(2)
stop2.set(); t2.join(5)
types2 = [e.get("type") for e in saw2]
print("SSE2 first frame:", saw2[0].get("type") if saw2 else None,
      "locks=", [l.get("resource") for l in (saw2[0].get("locks",[]) if saw2 and saw2[0].get("type")=="snapshot" else [])])
print("SSE2 received resource.unlocked:", "resource.unlocked" in types2)
print("SSE2 frames:", types2)

n = len(json.load(open(pjp, encoding="utf-8"))["scenes"])
print("scenes on disk:", n)
