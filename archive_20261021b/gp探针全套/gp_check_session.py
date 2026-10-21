import json, sys, httpx
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard")

BASE = "http://localhost:8000"
P = "__sw_batch_e2e"

# 列出该项目全部会话，取刚测的
import pathlib
sdir = pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard\projects") / P
# 直接扫 session store 文件位置
found = list(sdir.rglob("*sess_9b4cb04b9752*"))
print("session files:", [str(f.relative_to(sdir)) for f in found])
for f in found:
    if f.suffix == ".json":
        data = json.loads(f.read_text(encoding="utf-8"))
        msgs = data.get("messages", [])
        print(f"messages={len(msgs)}")
        for m in msgs:
            meta = m.get("meta") or {}
            evs = meta.get("events") or []
            kinds = [e.get("kind") for e in evs]
            print(f"  {m.get('role'):9s} len={len(m.get('content') or '')} "
                  f"meta.events={len(evs)} kinds={kinds[:6]}")
