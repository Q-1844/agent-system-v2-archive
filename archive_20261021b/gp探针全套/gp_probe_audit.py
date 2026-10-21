# gp_probe_audit.py — SCRATCH（不提交）。
# 干净新项目 sw_behavior_audit，10 轮代表性对话覆盖三块行为：
#  聊天探讨路由 / 故事段局部读取 / zero-write recovery（若模型偷懒不写）。
#  用户可同时打开前端 Agent Center 看实时 SSE（执行过程折叠条动画），
#  事后打开可看：对话历史 + 每轮【实际执行记录】事实块 + 最终剧本状态。
import json, shutil, sys, time, io
from pathlib import Path
import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.agents.script_writer import _is_explicit_write_request

ROOT = Path(__file__).resolve().parent
BASE = "http://localhost:8000"
SRC = ROOT / "projects" / "__sw_streamtest"
PROJ = "sw_behavior_audit"
LOG = ROOT / "gp_probe_audit.txt"
log = io.StringIO()
def w(*a):
    line = " ".join(str(x) for x in a)
    print(line); log.write(line + "\n")

dst = ROOT / "projects" / PROJ
if dst.exists():
    shutil.rmtree(dst)
shutil.copytree(SRC, dst)
ad = dst / "output" / "agents"
if ad.exists():
    shutil.rmtree(ad)
pj = dst / "output" / "project.json"
data = json.loads(pj.read_text(encoding="utf-8"))
data["name"] = PROJ
pj.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
r = httpx.post(f"{BASE}/api/project/{PROJ}/agents/sessions",
               json={"agent_id": "script_writer", "scope_type": "project", "scope_id": PROJ}, timeout=30)
r.raise_for_status()
sid = r.json()["session_id"]
w(f"[setup] 项目={PROJ}（前端项目列表可见），session={sid}，初始 {len(data['scenes'])} 段")
w(f"[setup] 后端日志恢复标记：grep 'zero-write recovery 触发' backend_runtime.log")

TURNS = [
    ("chat", "你觉得这个故事整体怎么样？简单说说你的感觉，不用改。"),
    ("edit", "把第 3 段的时段（time_of_day）改成「黄昏」，只改这一段。"),
    ("chat", "你刚才改了什么？一两句话告诉我就行。"),
    ("edit", "给 s02 加一个出场角色「邻居」，只改 s02。"),
    ("chat", "不用改，你觉得结尾的节奏怎么样？说说看法。"),
    ("edit", "在故事最后加一个收尾的故事段。"),
    ("chat", "为什么把收尾段放在最后？解释一下你的思路，不用再改。"),
    ("edit", "重写第 5 段，让它和前后剧情衔接更自然。"),
    ("chat", "现在一共有几段故事段？每段用一句话概括，不用改东西。"),
    ("edit", "把第 1 段的标题（title）设为「相遇」。"),
]

def stream_turn(content):
    tools = []; result = None; err = None
    for _ in range(3):
        tools = []; result = None; err = None
        try:
            with httpx.stream("POST", f"{BASE}/api/project/{PROJ}/agents/sessions/{sid}/turn/stream",
                              json={"content": content, "thinking": False},
                              timeout=httpx.Timeout(connect=30, read=600, write=60, pool=30)) as resp:
                if resp.status_code != 200:
                    err = f"HTTP {resp.status_code}: {resp.read().decode('utf-8','replace')[:120]}"
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
                        elif ev.get("type") == "tool.failed":
                            tools.append(ev.get("name") + "✗")
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

def disk_fp():
    d = json.loads(pj.read_text(encoding="utf-8"))
    import hashlib
    payload = json.dumps(
        [{"id": s["scene_id"], **{k: s.get(k) for k in ("title","location","time_of_day","summary","characters")}}
         for s in d["scenes"]], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]

WRITE_TOOLS = {"script.update","story.create","story.move","story.update","story.delete",
               "story.create_many","story.update_many","story.delete_many","story.insert_many"}
FALLBACK = ("没有真正执行修改", "请再说一次你的需求", "没有真正生效")

stats = {"edit": 0, "edit_ok": 0, "edit_zero": 0, "chat": 0, "chat_bad": 0, "full_read_edit": 0}
prev = disk_fp()
for i, (kind, content) in enumerate(TURNS, 1):
    w("\n" + "=" * 78)
    w(f"[轮{i:02d}|{kind}] explicit_write_intent={_is_explicit_write_request(content)}  U: {content}")
    t0 = time.time()
    tools, res, err = stream_turn(content)
    dt = time.time() - t0
    reply = ((res or {}).get("assistant_message") or "")
    reads = [t for t in tools if t in ("script.read", "story.list", "story.read")]
    writes = [t for t in tools if t.replace("✗","") in WRITE_TOOLS]
    fp = disk_fp()
    changed = (fp != prev)
    fallback = any(m in reply for m in FALLBACK)
    full_read = "script.read" in reads
    verdict = ""
    if kind == "edit":
        stats["edit"] += 1
        if writes and changed:
            stats["edit_ok"] += 1; verdict = "✅真改落盘"
        elif not writes:
            stats["edit_zero"] += 1; verdict = "❌零写工具结束（recovery 应已兜/兜不住）"
        else:
            verdict = "⚠️有写工具但磁盘无变化"
        if full_read: stats["full_read_edit"] += 1
    else:
        stats["chat"] += 1
        bad = fallback or any(t.replace("✗","") in WRITE_TOOLS for t in tools)
        verdict = "❌聊天轮异常" if bad else "✅自然回答"
        if bad: stats["chat_bad"] += 1
    w(f"  [{dt:.0f}s] intent={(res or {}).get('intent')} err={err} {verdict}")
    w(f"  工具: {tools}")
    w(f"  磁盘: {'变化' if changed else '未变'}；全文read: {'是' if full_read else '否'}；固定文案: {'是【异常】' if fallback else '否'}")
    w(f"  回复({len(reply)}字): {reply[:160]}")
    prev = fp
    time.sleep(3)

w("\n" + "#" * 78)
w(f"汇总：编辑轮 {stats['edit_ok']}/{stats['edit']} 真改落盘；零写失败 {stats['edit_zero']}；"
  f"聊天异常 {stats['chat_bad']}/{stats['chat']}；编辑轮读全文 {stats['full_read_edit']} 次")
w(f"后端 recovery 触发次数（grep）：见 backend_runtime.log 'zero-write recovery 触发'")
LOG.write_text(log.getvalue(), encoding="utf-8")
w("[done] 项目可在前端 Agent Center 选 sw_behavior_audit → script_writer 会话查看")
