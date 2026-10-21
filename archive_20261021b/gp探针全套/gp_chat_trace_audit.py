# gp_chat_trace_audit.py — SCRATCH（不提交）。
# 全量挖掘 projects/*/output/agents/sessions/*.json 中 script_writer 会话：
# 问题1：纯聊天 turn 是否调工具 / 是否在回复里输出全文；
# 问题2：局部修改 turn 是否调了 script.read 全文读取 / 读了哪些工具 / 读取量估算。
import json, glob, io, sys, re
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "gp_chat_trace_audit.txt"
out = io.StringIO()
def w(*a):
    print(*a, file=out)

EDIT_VERBS = re.compile(r"(修改|改一下|改下|改成|改写|删掉|删除|删了|创建|新建|新增|插入|加一?段|"
                        r"移动|移到|互换|换一下|拆分|拆成|续写|扩写|重写|压缩|调整.*顺序|排一下|"
                        r"第.{1,3}[段条].*(改|删|挪|移)|把.{1,10}[段条])")
QUESTION_MARK = re.compile(r"[?？]|为什么|怎么看|看法|是什么|有什么|吗[？?]?\s*$|呢[？?]?\s*$|聊聊|建议|如何|哪些")

def load_proj(proj_dir):
    pj = proj_dir / "project.json"
    if not pj.exists():
        return None
    try:
        return json.loads(pj.read_text(encoding="utf-8"))
    except Exception:
        return None

def story_overlap_ratio(reply, story_text):
    """story_text 中有多少比例的句子出现在 reply 里（粗粒度全文输出检测）。"""
    if not story_text or not reply:
        return 0.0, 0
    sents = [s for s in re.split(r"[。！？\n]", story_text) if len(s.strip()) >= 8]
    if not sents:
        return 0.0, 0
    hit = sum(1 for s in sents if s.strip() in reply)
    return hit / len(sents), len(sents)

def scene_quote_ratio(reply, scenes):
    """scene summary 被大段引用的段数（>60% 字符出现）。"""
    if not scenes or not reply:
        return 0, 0
    n = 0
    for sc in scenes:
        sm = (sc.get("summary") or "").strip()
        if len(sm) < 20:
            continue
        # 粗判：summary 前 60% 的字串是否在回复中
        head = sm[:int(len(sm)*0.6)]
        if head and head in reply:
            n += 1
    return n, len(scenes)

turns = []
sess_files = sorted(glob.glob(str(ROOT / "projects" / "*" / "output" / "agents" / "sessions" / "*.json")))
sw_sessions = 0
for f in sess_files:
    try:
        d = json.loads(Path(f).read_text(encoding="utf-8"))
    except Exception:
        continue
    if d.get("agent_id") != "script_writer":
        continue
    sw_sessions += 1
    proj_dir = Path(f).parents[3]   # projects/<name>/output/agents/sessions/x.json → projects/<name>
    proj_name = proj_dir.name
    proj = load_proj(proj_dir)
    story_text = (proj or {}).get("story_text") or ""
    scenes = (proj or {}).get("scenes") or []
    msgs = d.get("messages") or []
    # pair: user → next assistant
    pending_user = None
    for m in msgs:
        role = m.get("role")
        if role == "user":
            pending_user = m
        elif role == "assistant" and pending_user is not None:
            turns.append({
                "proj": proj_name,
                "sess": Path(f).stem[:18],
                "user": (pending_user.get("content") or "")[:200],
                "user_len": len(pending_user.get("content") or ""),
                "asst": m.get("content") or "",
                "asst_len": len(m.get("content") or ""),
                "status": m.get("status"),
                "meta": m.get("meta") or {},
                "story_len_now": len(story_text),
                "n_scenes_now": len(scenes),
                "story_text": story_text,
                "scenes": scenes,
            })
            pending_user = None

w(f"script_writer 会话数: {sw_sessions}，turn 数: {len(turns)}\n")

# ---------- 分类 ----------
chat_turns = []
edit_turns = []
for t in turns:
    u = t["user"]
    has_edit_verb = bool(EDIT_VERBS.search(u))
    is_question = bool(QUESTION_MARK.search(u))
    meta = t["meta"]
    trace = meta.get("trace") or []
    tools = [tr.get("tool") for tr in trace]
    reads = [x for x in tools if x in ("script.read", "story.list", "story.read")]
    writes = [x for x in tools if x in ("script.update","story.create","story.move","story.update",
                                        "story.delete","story.create_many","story.update_many",
                                        "story.delete_many","story.insert_many")]
    t["tools"] = tools; t["reads"] = reads; t["writes"] = writes
    t["has_edit_verb"] = has_edit_verb; t["is_question"] = is_question
    # 纯聊天判定：无写成功 + （疑问句式 或 无编辑动词）
    if meta.get("intent") == "conversation" and not writes:
        cat = "chat"
    elif writes:
        cat = "edit"
    else:
        cat = "other"
    t["cat"] = cat
    if cat == "chat":
        chat_turns.append(t)
    elif cat == "edit":
        edit_turns.append(t)

w(f"================ 问题1：纯聊天 turn（intent=conversation 且无写工具）共 {len(chat_turns)} ================")
chat_with_tools = 0
chat_fulltext = []
for t in chat_turns:
    tools = t["tools"]
    reads = t["reads"]
    ratio, nsents = story_overlap_ratio(t["asst"], t["story_text"])
    qn, nsc = scene_quote_ratio(t["asst"], t["scenes"])
    flag = ""
    if reads:
        chat_with_tools += 1
        flag += f" [调了读工具: {reads}]"
    if t["asst_len"] >= 600:
        flag += f" [长回复 {t['asst_len']}字]"
    if ratio >= 0.3 and nsents >= 3:
        flag += f" [正文复现率 {ratio:.0%} {nsents}句]"
        chat_fulltext.append(t)
    if qn >= 2:
        flag += f" [引用{qn}/{nsc}段摘要]"
        chat_fulltext.append(t)
    if flag or t["is_question"]:
        w(f"\n● [{t['proj'][:40]}] status={t['status']}")
        w(f"  U: {t['user'][:120]}")
        w(f"  A({t['asst_len']}字): {t['asst'][:180].replace(chr(10),' ')}")
        w(f"  tools={tools}{flag}")

w(f"\n--- 小结：{len(chat_turns)} 个纯聊天 turn 中，{chat_with_tools} 个调用了读工具；"
  f"{len(set(id(x) for x in chat_fulltext))} 个疑似全文/大段输出 ---")

w(f"\n\n================ 问题2：编辑 turn 共 {len(edit_turns)}（按读工具模式统计）================")
from collections import Counter
pat = Counter()
script_read_on_scene_task = []
for t in edit_turns:
    reads = tuple(dict.fromkeys(t["reads"]))  # 去重保序
    pat[reads] += 1
    wset = set(t["writes"])
    # 局部段任务（不涉及正文 script.update）却全文 read
    if "script.read" in reads and "script.update" not in wset:
        script_read_on_scene_task.append(t)
w("读工具组合分布（去重后）：")
for k, v in pat.most_common():
    w(f"  {v:3d}  {k}")

w(f"\n--- 段级任务却调用 script.read 全文的 turn：{len(script_read_on_scene_task)} ---")
for t in script_read_on_scene_task:
    w(f"\n● [{t['proj'][:40]}] story_len={t['story_len_now']}字 scenes={t['n_scenes_now']}")
    w(f"  U: {t['user'][:120]}")
    w(f"  tools={t['tools']}")
    w(f"  writes={t['writes']}")

# story.read 使用情况：段级更新任务里有没有用 story.read 精确读
w(f"\n--- 段级写任务（story.update/update_many）的读取方式 ---")
for t in edit_turns:
    if any(x in ("story.update","story.update_many") for x in t["writes"]):
        w(f"  [{t['proj'][:36]}] reads={dict.fromkeys(t['reads'])} writes={set(t['writes'])} U={t['user'][:60]}")

w(f"\n\n================ 所有 turn 的 tools 序列（全量，便于人工复查）================")
for t in turns:
    w(f"[{t['cat']:5s}] [{t['proj'][:34]}] U={t['user'][:70].replace(chr(10),' ')!r}")
    w(f"        tools={t['tools']} asst_len={t['asst_len']} status={t['status']}")

OUT.write_text(out.getvalue(), encoding="utf-8")
print("written", OUT, "turns:", len(turns), "chat:", len(chat_turns), "edit:", len(edit_turns))
