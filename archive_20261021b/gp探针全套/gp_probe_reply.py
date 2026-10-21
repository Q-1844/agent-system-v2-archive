# gp_probe_reply.py — SCRATCH。验证问题2：连续做几轮不同段修改，看每轮回复是否只说本轮改动、不复述历史。
import json, shutil, sys, time, io
from pathlib import Path
import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent
BASE = "http://localhost:8000"
SRC = ROOT / "projects" / "__sw_streamtest"
PROJ = "sw_reply_audit"
LOG = ROOT / "gp_probe_reply.txt"
log = io.StringIO()
def w(*a):
    line = " ".join(str(x) for x in a)
    print(line); log.write(line + "\n")

dst = ROOT / "projects" / PROJ
if dst.exists(): shutil.rmtree(dst)
shutil.copytree(SRC, dst)
ad = dst / "output" / "agents"
if ad.exists(): shutil.rmtree(ad)
pj = dst / "output" / "project.json"
data = json.loads(pj.read_text(encoding="utf-8")); data["name"] = PROJ
pj.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
r = httpx.post(f"{BASE}/api/project/{PROJ}/agents/sessions",
               json={"agent_id":"script_writer","scope_type":"project","scope_id":PROJ}, timeout=30)
r.raise_for_status(); sid = r.json()["session_id"]
w(f"[setup] {PROJ} session={sid} {len(data['scenes'])}段")

TURNS = [
    "把第 2 段的时段改成「黄昏」，只改这一段。",
    "给 s05 加一个角色「邻居」，只改 s05。",          # 轮1改了s02，本轮只s05——看是否复述s02
    "把最后一段的标题设为「暖阳」。",                  # 轮1/2改过，本轮只末段——看是否复述
    "重写第 4 段的 summary，让它更生动，只改第 4 段。",
    "总结一下这次对话里你都帮我做了哪些修改？简短一点。",  # 这轮允许汇总历史
]

def stream(content):
    tools=[]; res=None; err=None
    for _ in range(3):
        tools=[];res=None;err=None
        try:
            with httpx.stream("POST",f"{BASE}/api/project/{PROJ}/agents/sessions/{sid}/turn/stream",
                              json={"content":content,"thinking":False},
                              timeout=httpx.Timeout(connect=30,read=600,write=60,pool=30)) as resp:
                if resp.status_code!=200: err=f"HTTP{resp.status_code}"
                else:
                    for line in resp.iter_lines():
                        if not line or not line.startswith("data:"): continue
                        p=line[5:].strip()
                        if p=="[DONE]": break
                        try: ev=json.loads(p)
                        except: continue
                        if ev.get("type")=="tool.completed": tools.append(ev.get("name"))
                        elif ev.get("type")=="turn.completed": res=ev.get("result")
                        elif ev.get("type")=="turn.failed": err=ev.get("error")
        except Exception as e: err=f"{type(e).__name__}:{e}"
        if err and "429" in str(err): w("  429等45s"); time.sleep(45); continue
        break
    return tools,res,err

for i,c in enumerate(TURNS,1):
    w("\n"+"="*70)
    w(f"[轮{i}] U: {c}")
    t0=time.time(); tools,res,err=stream(c); dt=time.time()-t0
    reply=((res or {}).get("assistant_message") or "")
    w(f"  [{dt:.0f}s] intent={(res or {}).get('intent')} tools={tools}")
    w(f"  回复({len(reply)}字):")
    w(reply[:600])
    time.sleep(3)
LOG.write_text(log.getvalue(),encoding="utf-8")
w("[done]")
