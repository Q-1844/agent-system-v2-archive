# gp_probe_append.py — SCRATCH（不提交）。末尾加段复测 ×3（全新会话夹具），看是否还默认 script.read。
import json, shutil, sys, time, io
from pathlib import Path
import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent
BASE = "http://localhost:8000"
SRC = ROOT / "projects" / "__sw_streamtest"
LOG = ROOT / "gp_probe_append.txt"
log = io.StringIO()
def w(*a):
    line = " ".join(str(x) for x in a)
    print(line); log.write(line + "\n")

def make_fixture(name):
    dst = ROOT / "projects" / name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(SRC, dst)
    ad = dst / "output" / "agents"
    if ad.exists():
        shutil.rmtree(ad)
    pj = dst / "output" / "project.json"
    data = json.loads(pj.read_text(encoding="utf-8"))
    data["name"] = name
    pj.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    r = httpx.post(f"{BASE}/api/project/{name}/agents/sessions",
                   json={"agent_id": "script_writer", "scope_type": "project", "scope_id": name}, timeout=30)
    r.raise_for_status()
    return name, r.json()["session_id"]

def stream_turn(proj, sid, content):
    tools = []; result = None; err = None
    for _ in range(3):
        tools = []; result = None; err = None
        try:
            with httpx.stream("POST", f"{BASE}/api/project/{proj}/agents/sessions/{sid}/turn/stream",
                              json={"content": content, "thinking": False},
                              timeout=httpx.Timeout(connect=30, read=600, write=60, pool=30)) as resp:
                if resp.status_code != 200:
                    err = f"HTTP {resp.status_code}"
                else:
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
                        if ev.get("type") == "tool.completed":
                            tools.append(ev.get("name"))
                        elif ev.get("type") == "turn.completed":
                            result = ev.get("result")
                        elif ev.get("type") == "turn.failed":
                            err = ev.get("error")
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
        if err and "429" in str(err):
            w("  429，等45s"); time.sleep(45); continue
        break
    return tools, result, err

TASKS = [
    ("append-1", "在故事最后增加一个故事段。"),
    ("append-2", "请在剧本末尾再续一个故事段，讲小雨和老奶奶后来的日常。"),
    ("append-3", "最后加一段收尾的故事段，给故事一个有余韵的结尾。"),
]
for tag, content in TASKS:
    proj, sid = make_fixture(f"__sw_app_{tag}")
    t0 = time.time()
    tools, res, err = stream_turn(proj, sid, content)
    dt = time.time() - t0
    reads = [t for t in tools if t in ("script.read", "story.list", "story.read")]
    w(f"[{tag}] [{dt:.0f}s] err={err} intent={(res or {}).get('intent')}")
    w(f"  工具序列: {tools}")
    w(f"  script.read全文: {'是' if 'script.read' in reads else '否'}；story.read 次数: {tools.count('story.read')}")
    w(f"  回复({len((res or {}).get('assistant_message') or '')}字): "
      f"{((res or {}).get('assistant_message') or '')[:150]}")
    time.sleep(4)

LOG.write_text(log.getvalue(), encoding="utf-8")
w("[done]")
