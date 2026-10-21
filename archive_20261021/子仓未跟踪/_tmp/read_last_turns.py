# -*- coding: utf-8 -*-
"""读取 producer 会话最近两条 assistant 消息，检查模型对扩展 schema 的输出。"""
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

PROJ = "我的动画短片"
BASE = "http://127.0.0.1:8000"
SID = "sess_a6ba0d941664"

r = urllib.request.Request(f"{BASE}/api/project/{urllib.request.quote(PROJ)}/agents/sessions/{SID}")
sess = json.loads(urllib.request.urlopen(r, timeout=60).read().decode("utf-8"))
msgs = sess.get("messages") or sess.get("session", {}).get("messages") or []
assistant_msgs = [m for m in msgs if m.get("role") == "assistant"]
print(f"total={len(msgs)} assistant={len(assistant_msgs)}")
for m in assistant_msgs[-2:]:
    c = (m.get("content") or "")[:1200]
    print("=" * 40)
    print(c)
