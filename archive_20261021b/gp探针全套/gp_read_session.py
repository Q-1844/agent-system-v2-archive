# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

p = r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard\projects\__sw_streamtest\output\agents\sessions\sess_4c401422739a.json"
data = json.loads(io.open(p, encoding="utf-8").read())
msgs = data.get("messages", [])
print(f"total messages: {len(msgs)}")
for i, m in enumerate(msgs):
    role = m.get("role")
    content = m.get("content") or ""
    meta = m.get("meta") or {}
    evs = meta.get("events") or []
    trace = meta.get("trace") or []
    rc = meta.get("receipts") or []
    print(f"\n=== [{i}] {role} len={len(content)} events={len(evs)} trace={len(trace)} receipts={len(rc)}")
    if role == "user":
        print("USER:", content[:500])
    else:
        # assistant：打印 content 尾部（含事实摘要）+ receipts 细节
        print("ASSISTANT tail:", content[-600:])
        if rc:
            for r in rc:
                print(f"  receipt: op={r.get('operation')} status={r.get('status')} target={r.get('target')} err={(r.get('error') or '')[:80]}")
        if trace:
            # 打印 trace 序列（工具名+结果状态）
            for t in trace:
                print(f"  trace: step={t.get('step')} tool={t.get('tool')} result={str(t.get('result'))[:60]}")
