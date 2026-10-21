# gp_probe_title.py — SCRATCH。单点验证"设标题"是否正常用 story.update(title) 而非误改正文。
import json, shutil, sys, time, io
from pathlib import Path
import httpx
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent
BASE = "http://localhost:8000"
SRC = ROOT / "projects" / "__sw_streamtest"
PROJ = "sw_title_probe"
LOG = ROOT / "gp_probe_title.txt"
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
w(f"[setup] {PROJ} {len(data['scenes'])}段")
content = "把最后一段的标题（title）设为「暖阳」。"
w(f"U: {content}")
t0=time.time()
tools=[];res=None;err=None
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
  if err and ("429" in str(err) or "500" in str(err)): w(f"  {err} 等45s重试"); time.sleep(45); continue
  break
dt=time.time()-t0
reply=((res or {}).get("assistant_message") or "")
w(f"[{dt:.0f}s] intent={(res or {}).get('intent')} err={err}")
w(f"tools={tools}")
w(f"回复({len(reply)}字): {reply[:300]}")
# 磁盘
d=json.loads(pj.read_text(encoding="utf-8"))
last=d["scenes"][-1]
story_len=len(d.get("story_text") or "")
w(f"磁盘：末段={last['scene_id']} title={last.get('title')!r} story_text长度={story_len}（应为2329未变）")
w(f"判定：{'✅正确 story.update 改 title、正文未动' if last.get('title')=='暖阳' and story_len==2329 else '❌异常（改正文或未设标题）'}")
LOG.write_text(log.getvalue(),encoding="utf-8")
w("[done]")
