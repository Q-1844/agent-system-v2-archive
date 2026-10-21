# scratch 探针：对活后端 :8000 跑一次真实 /turn/stream，打印事件类型序列，
# 确认 turn.started / tool.pending / tool.started / tool.completed / turn.completed
# 的先后与完整性（定位"完成后折叠按钮消失"= processItems 是否在完成时为空）。
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8000"
PROJECT = "__sw_timeout_test"


def post(path, payload):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


# 1) 建/取会话
sess = post(f"/api/project/{PROJECT}/agents/sessions",
            {"agent_id": "script_writer", "scope_type": "project", "scope_id": PROJECT})
sid = sess["session_id"]
print("session:", sid)

# 2) 发流式 turn（SSE）
body = json.dumps({"content": "创建2个故事段，每段两句话即可。", "thinking": False}).encode("utf-8")
req = urllib.request.Request(
    f"{BASE}/api/project/{PROJECT}/agents/sessions/{sid}/turn/stream",
    data=body, headers={"Content-Type": "application/json"}, method="POST")

seq = []
final = None
with urllib.request.urlopen(req, timeout=300) as r:
    buf = b""
    for chunk in iter(lambda: r.read(1024), b""):
        buf += chunk
        while b"\n\n" in buf:
            frame, buf = buf.split(b"\n\n", 1)
            txt = frame.decode("utf-8", "replace")
            for line in txt.split("\n"):
                if line.startswith("data:"):
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        continue
                    try:
                        ev = json.loads(payload)
                    except Exception:
                        continue
                    t = ev.get("type")
                    seq.append(t)
                    if t == "turn.completed":
                        final = ev.get("result")
                    if t in ("tool.pending", "tool.started", "tool.completed", "tool.failed"):
                        print(f"  EVT {t}: name={ev.get('name')} label={ev.get('label')} ok={ev.get('ok')}")

print("\n事件序列:", " -> ".join(seq))
if final:
    msg = final.get("message", {})
    print("final message role:", msg.get("role"), "| status:", msg.get("status"))
    print("receipts:", [(r.get('operation'), r.get('ok')) for r in final.get("receipts", [])])
    print("trace steps:", len(final.get("trace", [])))
else:
    print("!! 没有 turn.completed")
