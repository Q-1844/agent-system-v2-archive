# -*- coding: utf-8 -*-
"""复现用户 10 段 x300 字任务：拷贝 __sw_streamtest -> __sw_repro_fail，
保留原会话历史，重发同款指令，抓异常身份（新后端已带 traceback 日志）。"""
import json, shutil, sys, time
from pathlib import Path
import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent
BASE = "http://localhost:8000"
SRC = ROOT / "projects" / "__sw_streamtest"
DST = ROOT / "projects" / "__sw_repro_fail"

# 拷贝项目（保留当前 10 段状态与原会话）
if DST.exists():
    shutil.rmtree(DST)
shutil.copytree(SRC, DST)
# 改 project.json 的 name 字段
pj = DST / "output" / "project.json"
data = json.loads(pj.read_text(encoding="utf-8"))
data["name"] = "__sw_repro_fail"
pj.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[setup] 项目拷贝完成：10 段状态 + 会话历史（{len(data['scenes'])} 段）")

# 拷贝会话（保历史）
src_sess = SRC / "output" / "agents" / "sessions" / "sess_4c401422739a.json"
sess_data = json.loads(src_sess.read_text(encoding="utf-8"))
sess_data["session_id"] = "sess_repro_fail01"
sess_data["scope_id"] = "__sw_repro_fail"
dst_sess = DST / "output" / "agents" / "sessions" / "sess_repro_fail01.json"
dst_sess.write_text(json.dumps(sess_data, ensure_ascii=False), encoding="utf-8")
print("[setup] 会话拷贝完成：sess_repro_fail01（13 条历史）")

# 发同款任务
content = ("剧本内容还不够，请你慢慢制作：剧本至少要到2000字，"
           "每个故事段内容起码要300字左右的。把 s01 到 s10 每段都扩写。")
print(f"[send] {content!r}")
print("=" * 60)

tools, assistant, failed, completed = [], "", None, None
t0 = time.time()
with httpx.stream("POST",
                  f"{BASE}/api/project/__sw_repro_fail/agents/sessions/sess_repro_fail01/turn/stream",
                  json={"content": content, "thinking": False}, timeout=600) as resp:
    if resp.status_code != 200:
        print(f"[HTTP {resp.status_code}] {resp.read().decode('utf-8', 'replace')[:300]}")
        sys.exit(1)
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
            tools.append((ev.get("name"), ev.get("ok")))
            print(f"  [{time.time()-t0:5.0f}s] ✓ {ev.get('name')} ok={ev.get('ok')} {(ev.get('summary') or '')[:60]}")
        elif t == "tool.failed":
            tools.append((ev.get("name"), False))
            print(f"  [{time.time()-t0:5.0f}s] ! {ev.get('name')} {(ev.get('error') or '')[:80]}")
        elif t == "turn.completed":
            completed = ev.get("result")
            print(f"  [{time.time()-t0:5.0f}s] turn.completed intent={completed.get('intent') if completed else None}")
        elif t == "turn.failed":
            failed = ev.get("error")
            print(f"  [{time.time()-t0:5.0f}s] turn.failed error={failed!r}")

dt = time.time() - t0
print("=" * 60)
print(f"[{dt:.0f}s] 工具调用 {len(tools)} 次；turn.failed={failed!r}")
names = [n for n, _ in tools]
for n in sorted(set(names)):
    okc = sum(1 for x, ok in tools if x == n and ok)
    print(f"    {n:22s} {okc}/{names.count(n)} ok")
