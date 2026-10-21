# scratch 探针（不入库）：验证 /events SSE 订阅者在一次带写操作的 turn 中
# 是否真的收到 resource.locked 和 resource.unlocked（模拟 MainLayout 的 EventSource）。
import json
import threading
import time
from types import SimpleNamespace

import sys
sys.path.insert(0, ".")

from fastapi.testclient import TestClient

import api_server
from src.agents.runtime import get_agent_runtime, reset_agent_runtime
from src.agents.project_events import reset_project_bus
import routers.agents as agents_router
from src.agents.script_writer import _scenes_token
from src.core.models import Project, Scene, Character, StyleAnchor
from src.core.store import ProjectStore
import tempfile, os

tmp = tempfile.mkdtemp()
ProjectStore(tmp).save(Project(
    name="demo", style=StyleAnchor(), story_text="剧本。",
    characters=[Character(name="LinXia", description_en="x")],
    scenes=[Scene(scene_id=f"s0{i}", summary=f"第{i}段", characters=["LinXia"], shots=[])
            for i in range(1, 5)], next_scene_seq=5))

reset_project_bus()
agents_router._ACTIVE_TURN_EVENTS.clear()
reset_agent_runtime()
rt = get_agent_runtime()
rt._project_dir_resolver = lambda name: tmp

rev = _scenes_token([SimpleNamespace(scene_id=f"s0{i}") for i in range(1, 5)])

def tc(name, args, cid="c1"):
    return {"id": cid, "type": "function",
            "function": {"name": name, "arguments": json.dumps(args, ensure_ascii=False)}}

class Scripted:
    def __init__(self, script): self.script = list(script)
    async def chat_completion_stream(self, messages, **kw):
        step = self.script.pop(0) if self.script else {"content": "完成。"}
        if step.get("tool_calls"):
            yield {"kind": "finish", "reason": "tool_calls", "content": None,
                   "tool_calls": step["tool_calls"], "usage": None}
        else:
            yield {"kind": "finish", "reason": "stop", "content": step.get("content", "完成。"),
                   "tool_calls": None, "usage": None}
    async def chat_completion(self, messages, **kw):
        return {"content": "完成。", "tool_calls": None}

rt._client = Scripted([
    {"tool_calls": [tc("story.create",
                       {"summary": "探针新段", "characters": ["LinXia"],
                        "expected_scenes_revision": rev}, "c1")]},
    {"content": "已新增一段。"},
])

client = TestClient(api_server.app)

# 建会话
r = client.post("/api/project/demo/agents/sessions",
                json={"agent_id": "script_writer", "scope_type": "project", "scope_id": "demo"})
sid = r.json()["session_id"]

# 后台线程：挂 /events SSE，持续读帧直到 stop
frames = []
stop = threading.Event()
def sse_reader():
    with client.stream("GET", "/api/project/demo/events") as resp:
        buf = b""
        it = resp.iter_bytes()
        for ch in it:
            if stop.is_set():
                break
            buf += ch
            while b"\n\n" in buf:
                frame, buf = buf.split(b"\n\n", 1)
                txt = frame.decode("utf-8", "replace")
                for line in txt.split("\n"):
                    if line.startswith("data:"):
                        try:
                            frames.append(json.loads(line[5:].strip()))
                        except Exception:
                            pass

t = threading.Thread(target=sse_reader, daemon=True)
t.start()
time.sleep(0.5)  # 让 SSE 先连上拿 snapshot

# 主线程：跑流式 turn
with client.stream("POST", f"/api/project/demo/agents/sessions/{sid}/turn/stream",
                   json={"content": "加一段", "thinking": False}) as resp:
    body = b"".join(resp.iter_bytes())

time.sleep(1.0)
stop.set()
t.join(timeout=3)

types = [f.get("type") for f in frames]
print("=== /events frames ===")
for f in frames:
    print(" ", f.get("type"), f.get("resource") or f.get("operation") or "", f.get("locks") if f.get("type")=="snapshot" else "")
print("turn.completed in body:", b"turn.completed" in body)
print("LOCKED seen:", "resource.locked" in types)
print("UNLOCKED seen:", "resource.unlocked" in types)
lock_idx = types.index("resource.locked") if "resource.locked" in types else -1
unlock_idx = types.index("resource.unlocked") if "resource.unlocked" in types else -1
print("order ok:", 0 <= lock_idx < unlock_idx)
