# gp_probe_session.py — SCRATCH（不提交）。
# 15 轮连续会话验收：单一新会话，混合琐碎小修改 + 探讨/回顾。逐轮核对：
#  ①编辑轮是否真调写工具且磁盘落盘（零工具+声称成功=假成功，即之前的情况）
#  ②聊天/回顾轮是否自然回答（无写工具、无「没有真正执行修改」固定文案）
#  ③段任务是否还默认 script.read 全文
import json, shutil, sys, time, io
from pathlib import Path
import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent
BASE = "http://localhost:8000"
SRC = ROOT / "projects" / "__sw_streamtest"
PROJ = "__sw_session_audit"
LOG = ROOT / "gp_probe_session.txt"
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
w(f"[setup] {PROJ} session={sid}，初始 {len(data['scenes'])} 段")

TURNS = [
    ("chat", "你觉得这个故事目前整体怎么样？简单说说你的感觉就行，不用改。"),
    ("edit", "把第 4 个故事段的时段（time_of_day）改成「清晨」，只改这一个字段。"),
    ("chat", "你刚才改了什么？用一两句话告诉我就行。"),
    ("edit", "给 s01 这个故事段的出场角色加上「奶奶」，只改 s01。"),
    ("edit", "把第 7 段的 summary 开头加一句雨夜环境描写，让氛围更足，只改第 7 段。"),
    ("chat", "不用修改，你觉得现在结尾的节奏快不快？说说看法。"),
    ("edit", "把 s03 的地点（location）改成「老旧公寓楼下」，只改这个字段。"),
    ("chat", "我觉得第 9 段和第 10 段之间有点跳，你觉得要不要加个过渡段？先说说想法，先别改。"),
    ("edit", "行，那就按你说的，在第 9 段后面加一个过渡故事段。"),
    ("chat", "刚才为什么把过渡段放在那个位置？解释一下你的思路，不用再改。"),
    ("edit", "把最后一个故事段的标题（title）设为「暖阳」。"),
    ("edit", "给 s05 的出场角色也加上「奶奶」，只改 s05。"),
    ("chat", "现在一共有几段故事段？每段用一句话概括就行，不用改东西。"),
    ("edit", "把第 2 段 summary 里你觉得最平淡的那句润色一下，让它更有画面感，只改第 2 段。"),
    ("chat", "总结一下这次对话里你都帮我做了哪些修改？简短一点。"),
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

def disk_fingerprint():
    d = json.loads(pj.read_text(encoding="utf-8"))
    sc = {s["scene_id"]: s for s in d["scenes"]}
    # 内容指纹：每段可变字段 + 段 id 列表
    import hashlib
    payload = json.dumps(
        [{"id": s["scene_id"], **{k: s.get(k) for k in ("title","location","time_of_day","summary","characters")}}
         for s in d["scenes"]], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8], sc

FALLBACK_MARK = ("没有真正执行修改", "请再说一次你的需求")
SUCCESS_MARK = ("已", "完成", "改好", "加好", "改成", "改为", "加入", "添加", "插入", "创建", "重写")

stats = {"edit": 0, "edit_ok": 0, "edit_fake": 0, "chat": 0, "chat_bad": 0, "full_read_edit": 0}
prev_fp, _ = disk_fingerprint()
for i, (kind, content) in enumerate(TURNS, 1):
    w("\n" + "=" * 78)
    w(f"[轮{i:02d}|{kind}] U: {content}")
    t0 = time.time()
    tools, res, err = stream_turn(content)
    dt = time.time() - t0
    reply = ((res or {}).get("assistant_message") or "")
    reads = [t for t in tools if t in ("script.read", "story.list", "story.read")]
    writes = [t for t in tools if not t.endswith("✗") and t not in ("script.read", "story.list", "story.read")]
    writes += [t for t in tools if t.endswith("✗")]
    fp, sc = disk_fingerprint()
    disk_changed = (fp != prev_fp)
    fallback = any(m in reply for m in FALLBACK_MARK)
    full_read = "script.read" in reads
    claims = any(m in reply[:80] for m in SUCCESS_MARK)
    verdict = ""
    if kind == "edit":
        stats["edit"] += 1
        if writes and disk_changed:
            stats["edit_ok"] += 1; verdict = "✅真改且落盘"
        elif not writes and claims:
            stats["edit_fake"] += 1; verdict = "❌假成功（零写工具却声称完成，磁盘未变）"
        elif writes and not disk_changed:
            verdict = "⚠️调了写工具但磁盘无变化"
        else:
            verdict = "? 未声称完成也无写工具"
        if full_read:
            stats["full_read_edit"] += 1
    else:
        stats["chat"] += 1
        if fallback or any(not t.endswith("✗") and t not in ("script.read","story.list","story.read") for t in tools):
            stats["chat_bad"] += 1
            verdict = "❌聊天轮异常（固定文案或写工具）"
        else:
            verdict = "✅自然回答"
    w(f"  [{dt:.0f}s] intent={(res or {}).get('intent')} err={err} {verdict}")
    w(f"  工具: {tools}")
    w(f"  磁盘指纹: {prev_fp}→{fp} {'(变化)' if disk_changed else '(未变)'}；script.read全文: {'是' if full_read else '否'}；固定文案: {'是【异常】' if fallback else '否'}")
    w(f"  回复({len(reply)}字): {reply[:160]}")
    prev_fp = fp
    time.sleep(4)

w("\n" + "#" * 78)
w(f"汇总：编辑轮 {stats['edit_ok']}/{stats['edit']} 真改落盘；假成功 {stats['edit_fake']}；"
  f"聊天轮异常 {stats['chat_bad']}/{stats['chat']}；编辑轮读全文 {stats['full_read_edit']} 次")
LOG.write_text(log.getvalue(), encoding="utf-8")
w("[done]")
