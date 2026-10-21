# gp_probe_reasoning.py — SCRATCH。验证 reasoning 持久化：跑一个 thinking 开的流式 turn，
# 查 meta.reasonings 是否非空、与 meta.trace 交错、刷新后前端能重建。
import json, shutil, sys, time, io
from pathlib import Path
import httpx
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent
BASE = "http://localhost:8000"
SRC = ROOT / "projects" / "__sw_streamtest"
PROJ = "sw_reasoning_probe"
LOG = ROOT / "gp_probe_reasoning.txt"
log = io.StringIO()
def w(*a): line=" ".join(str(x) for x in a); print(line); log.write(line+"\n")
dst = ROOT/"projects"/PROJ
if dst.exists(): shutil.rmtree(dst)
shutil.copytree(SRC, dst)
ad = dst/"output"/"agents"
if ad.exists(): shutil.rmtree(ad)
pj = dst/"output"/"project.json"
data = json.loads(pj.read_text(encoding="utf-8")); data["name"]=PROJ
pj.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
r = httpx.post(f"{BASE}/api/project/{PROJ}/agents/sessions",
               json={"agent_id":"script_writer","scope_type":"project","scope_id":PROJ}, timeout=30)
r.raise_for_status(); sid=r.json()["session_id"]
content = "把第 4 段的时段改成「清晨」，只改这一段。"
w(f"[setup] {PROJ} sid={sid} thinking=TRUE")
t0=time.time(); result=None; err=None
reasoning_deltas = 0
try:
  with httpx.stream("POST",f"{BASE}/api/project/{PROJ}/agents/sessions/{sid}/turn/stream",
                    json={"content":content,"thinking":True},
                    timeout=httpx.Timeout(connect=30,read=600,write=60,pool=30)) as resp:
    if resp.status_code!=200: err=f"HTTP{resp.status_code}: {resp.read().decode('utf-8','replace')[:200]}"
    else:
      for line in resp.iter_lines():
        if not line or not line.startswith("data:"): continue
        p=line[5:].strip()
        if p=="[DONE]": break
        try: ev=json.loads(p)
        except: continue
        if ev.get("type")=="reasoning.delta": reasoning_deltas += 1
        elif ev.get("type")=="turn.completed": result=ev.get("result")
        elif ev.get("type")=="turn.failed": err=ev.get("error")
except Exception as e: err=f"{type(e).__name__}:{e}"
dt=time.time()-t0
w(f"[{dt:.0f}s] err={err} reasoning.delta 流事件数={reasoning_deltas}")
if result:
  # result.meta.reasonings（turn.completed.result.message.meta 或 result 顶层）
  msg = result.get("message") or {}
  meta = msg.get("meta") or {}
  reasonings = meta.get("reasonings") or result.get("reasonings") or []
  trace = meta.get("trace") or result.get("trace") or []
  w(f"result.trace 条数={len(trace)}：{[ (t.get('tool'),t.get('result')) for t in trace]}")
  w(f"meta.reasonings 条数={len(reasonings)}")
  for r0 in reasonings:
    w(f"  step {r0.get('step')} duration={r0.get('duration_ms')}ms text({len(r0.get('text') or '')}字): "
      f"{(r0.get('text') or '')[:120]}")
  # 从持久化 session 文件再读一次（模拟刷新）
  fs = list((dst/"output/agents/sessions").glob("*.json"))
  sd = json.loads(fs[0].read_text(encoding="utf-8"))
  last_asst = [m for m in sd.get("messages",[]) if m.get("role")=="assistant"][-1]
  rmeta = last_asst.get("meta") or {}
  w(f"\n[持久化文件] meta.reasonings={len(rmeta.get('reasonings') or [])} 条, meta.trace={len(rmeta.get('trace') or [])} 条")
  w(f"刷新后前端可重建折叠项：reasoning {len(rmeta.get('reasonings') or [])} + tool {len(rmeta.get('trace') or [])}")
else:
  w("无 result（错误）")
LOG.write_text(log.getvalue(),encoding="utf-8")
w("[done]")
