"""Producer V1 Phase 3 真机验收驱动（不提交，本地 scratch 惯例 gp_*）。

子命令：
  seed                    创建两个全新安全项目 __producer_phase3_room / __producer_phase3_stop
  casea                   项目1跑 Case A（SW→Director 跨域），全程抓 SSE 帧 +
                          执行中途模拟刷新（独立 HTTP 连接 GET room snapshot），
                          结束后核对 UI 事实 vs 磁盘事实（§四十七）
  stop                    项目2跑 Stop 案例：委派进行中 POST cancel，核对 stopped 状态持久化
  room [n]                GET room snapshot n 次（默认 20），验证顺序/ID 稳定并打印最新快照

判定从证据，不从文本。
"""
import sys, json, time, os, httpx
sys.path.insert(0, ".")

BASE = "http://localhost:8000"
EV_DIR = "_phase3_evidence"
os.makedirs(EV_DIR, exist_ok=True)

ROOM_A = "__producer_phase3_room"
ROOM_S = "__producer_phase3_stop"


# ============ seed ============
def seed():
    from src.core.models import Project, Scene, Shot, Character, StyleAnchor
    from src.core.store import ProjectStore

    def _shots(scene_id, n, base_desc):
        return [Shot(shot_id=f"{scene_id}_c{i:02d}", scene_id=scene_id, index=i,
                     description=f"{base_desc}（第{i}镜）",
                     characters=["林小雨"],
                     shot_size="medium shot", target_duration_s=4)
                for i in range(1, n + 1)]

    def build(name):
        s01 = Scene(scene_id="s01", summary="林小雨在雨夜推开咖啡馆的门，心情低落。",
                    characters=["林小雨"], shots=_shots("s01", 2, "林小雨走进咖啡馆"))
        s02 = Scene(scene_id="s02", summary="她靠窗坐下，陈默沉默地坐在对面。",
                    characters=["林小雨", "陈默"],
                    shots=_shots("s02", 2, "两人对坐"))
        s03 = Scene(scene_id="s03", summary="窗外雨声渐大，两人回忆起往事，她想起未说出口的话。",
                    characters=["林小雨", "陈默"],
                    shots=_shots("s03", 2, "回忆闪回"))
        s04 = Scene(scene_id="s04", summary="雨停了，林小雨起身离开，故事在沉默中结束。",
                    characters=["林小雨"], shots=[])
        return Project(
            name=name, style=StyleAnchor(),
            story_text=(
                "短片《雨夜咖啡馆》。\n\n"
                "第一幕：雨夜，林小雨推开咖啡馆的门，心情低落，靠窗坐下。陈默沉默地坐在对面。"
                "窗外雨声渐大，两人回忆起往事。\n\n"
                "第二幕：雨停了，林小雨起身离开，故事在沉默中结束。目前结尾略仓促，"
                "人物动机不够清晰——林小雨为什么离开？陈默的沉默意味着什么？后半段节奏偏快。"
            ),
            characters=[
                Character(name="林小雨",
                          description_en="a young woman in a red coat, tired eyes"),
                Character(name="陈默",
                          description_en="a tall man with glasses, quiet demeanor"),
            ],
            scenes=[s01, s02, s03, s04], next_scene_seq=5)

    for name in (ROOM_A, ROOM_S):
        base = f"projects/{name}"
        os.makedirs(f"{base}/output", exist_ok=True)
        ProjectStore(base).save(build(name))
        p = ProjectStore(base).load()
        print(f"seeded {name}: scenes={len(p.scenes)} "
              f"shots={sum(len(s.shots or []) for s in p.scenes)} chars={len(p.characters)}")


# ============ helpers ============
def _room(project):
    r = httpx.get(f"{BASE}/api/project/{project}/agents/producer/room", timeout=30)
    r.raise_for_status()
    return r.json()


def _dump_room(project, label):
    snap = _room(project)
    path = f"{EV_DIR}/{label}.room.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=1)
    print(f"  room snapshot -> {path}  (messages={len(snap['messages'])} "
          f"turn_active={snap['turn_active']} wf={snap['workflow'] and snap['workflow']['status']})")
    for m in snap["messages"]:
        line = f"    {m['kind']:17s} {m['sender']:16s}"
        if m.get("recipient"):
            line += f" -> {m['recipient']:16s}"
        line += f" [{m.get('status') or '-'}]"
        if m["kind"] == "specialist_result":
            line += f" verified={m.get('verified')} refs={_refs_short(m.get('changed_refs'))}"
        print(line + f"  {(m.get('content') or '')[:36].replace(chr(10), ' ')}")
    print("  participants:", {p["agent_id"]: p["status"] for p in snap["participants"]})
    return snap


def _refs_short(refs):
    if not isinstance(refs, dict):
        return "-"
    parts = []
    for k, v in refs.items():
        if v:
            parts.append(f"{k[:1]}:{len(v)}")
    return ",".join(parts) or "empty"


def _create_session(project, agent_id="producer"):
    r = httpx.post(f"{BASE}/api/project/{project}/agents/sessions",
                   json={"agent_id": agent_id, "scope_type": "project",
                         "scope_id": ""}, timeout=30)
    r.raise_for_status()
    return r.json()["session_id"]


def _cancel(project, sid):
    r = httpx.post(f"{BASE}/api/project/{project}/agents/sessions/{sid}/turn/cancel",
                   timeout=30)
    return r.json()


# ============ case A：SW→Director + 中途刷新模拟 ============
CASE_A_PROMPT = ("请检查后半段剧情节奏，把真正有问题的地方处理好，并同步受到影响的分镜。"
                 "角色外貌不要改。")


def casea():
    project = ROOM_A
    sid = _create_session(project)
    print(f"[caseA] project={project} sid={sid}")
    mid_snap = {}          # 中途刷新捕获
    captured = 0
    events_path = f"{EV_DIR}/caseA.events.jsonl"
    ef = open(events_path, "w", encoding="utf-8")
    t0 = time.time()
    final = None
    err = None
    active_task = None     # 当前委派 task_id（delegation.started 后）
    with httpx.Client(timeout=httpx.Timeout(900.0, connect=30.0)) as c:
        with c.stream("POST",
                      f"{BASE}/api/project/{project}/agents/sessions/{sid}/turn/stream",
                      json={"content": CASE_A_PROMPT, "thinking": False}) as resp:
            buf = b""
            for chunk in resp.iter_bytes():
                buf += chunk
                while b"\n\n" in buf:
                    raw, buf = buf.split(b"\n\n", 1)
                    line = raw.decode("utf-8", errors="replace").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data:
                        continue
                    try:
                        ev = json.loads(data)
                    except Exception:
                        continue
                    ef.write(json.dumps({"t": round(time.time() - t0, 2), **ev},
                                        ensure_ascii=False) + "\n")
                    ef.flush()
                    et = ev.get("type")
                    if et == "turn.completed":
                        final = ev.get("result")
                    elif et == "turn.failed":
                        err = ev.get("error")
                    elif et == "tool.progress" and ev.get("phase") == "delegation.started":
                        active_task = ev.get("call_id")
                        print(f"  [{time.time()-t0:6.1f}s] ▶ delegation.started "
                              f"{ev.get('agent')} task={active_task} obj={ev.get('objective','')[:50]}")
                    elif et == "tool.progress" and ev.get("phase") == "delegation.completed":
                        print(f"  [{time.time()-t0:6.1f}s] ■ delegation.completed "
                              f"{ev.get('agent')} status={ev.get('status')}")
                        active_task = None
                    elif et == "tool.started" and ev.get("agent"):
                        # Specialist 执行中 → 模拟用户刷新（独立连接拉快照，一次即可作为证据）
                        if captured == 0 and active_task:
                            captured += 1
                            print(f"  [{time.time()-t0:6.1f}s] ⤺ 模拟刷新：独立连接 GET room（Specialist 执行中）")
                            mid_snap = _room(project)
                            with open(f"{EV_DIR}/caseA.midrefresh.room.json", "w",
                                      encoding="utf-8") as f:
                                json.dump(mid_snap, f, ensure_ascii=False, indent=1)
                            kinds = [(m["kind"], m.get("status")) for m in mid_snap["messages"]]
                            print(f"      mid-refresh messages: {kinds}")
                            print(f"      mid-refresh participants: "
                                  f"{ {p['agent_id']: p['status'] for p in mid_snap['participants']} }")
    ef.close()
    print(f"  events -> {events_path} ({captured} mid-refresh snapshot)")
    if err:
        print(f"  !! turn.failed: {err}")
    if final is None:
        print("  !! no turn.completed")
        return 1
    print(f"\n  wall={time.time()-t0:.0f}s intent={final.get('intent')} "
          f"linked_tasks={final.get('linked_task_ids')}")
    for r in final.get("receipts", []):
        print(f"    receipt {r.get('agent')}: status={r.get('status')} verified={r.get('verified')} "
              f"tools={r.get('n_tool_calls')} refs={_refs_short(r.get('changed_refs'))}")
    print(f"  final message:\n    {(final.get('assistant_message') or '')[:400]}")

    # ---- 结束后：最终快照 + 20 次顺序稳定性 + 磁盘一致性 ----
    print("\n[caseA] final room snapshot:")
    snap = _dump_room(project, "caseA.final")

    ids_seqs = []
    for i in range(20):
        s = _room(project)
        ids_seqs.append([m["id"] for m in s["messages"]])
    stable = all(x == ids_seqs[0] for x in ids_seqs)
    print(f"\n[caseA] 20x reload ordering stable: {stable}")

    ok = verify_against_disk(project, snap)
    mid_ok = bool(mid_snap) and any(
        m["kind"] == "delegation" and m.get("status") == "running"
        for m in mid_snap["messages"])
    print(f"[caseA] mid-refresh captured running delegation: {mid_ok}")
    print(f"[caseA] disk-vs-room consistency: {ok}")
    print(f"[caseA] ordering stable: {stable}")
    return 0 if (ok and stable) else 1


# ============ stop 案例 ============
def stop_case():
    project = ROOM_S
    sid = _create_session(project)
    print(f"[stop] project={project} sid={sid}")
    cancelled = False
    t0 = time.time()
    final = None
    err = None
    with httpx.Client(timeout=httpx.Timeout(900.0, connect=30.0)) as c:
        with c.stream("POST",
                      f"{BASE}/api/project/{project}/agents/sessions/{sid}/turn/stream",
                      json={"content": CASE_A_PROMPT, "thinking": False}) as resp:
            buf = b""
            for chunk in resp.iter_bytes():
                buf += chunk
                while b"\n\n" in buf:
                    raw, buf = buf.split(b"\n\n", 1)
                    line = raw.decode("utf-8", errors="replace").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data:
                        continue
                    try:
                        ev = json.loads(data)
                    except Exception:
                        continue
                    et = ev.get("type")
                    if et == "turn.completed":
                        final = ev.get("result")
                    elif et == "turn.failed":
                        err = ev.get("error")
                    # Specialist 已开工（>=2 个工具事件）→ 用户按停止
                    elif (et == "tool.started" and ev.get("agent") and not cancelled
                          and time.time() - t0 > 3):
                        cancelled = True
                        print(f"  [{time.time()-t0:6.1f}s] ⏹ POST cancel（Specialist 执行中）"
                              f" -> {_cancel(project, sid)}")
                    if et in ("tool.progress",):
                        ph = ev.get("phase") or ""
                        print(f"  [{time.time()-t0:6.1f}s] progress {ev.get('name')} {ph}")
    print(f"  turn ended: final={'yes' if final else 'no'} err={err} status="
          f"{final and final.get('message', {}).get('status')}")
    time.sleep(1.0)
    print("\n[stop] room snapshot after stop:")
    snap = _dump_room(project, "stop.final")
    # 断言：无 running；结果/producer 状态 stopped；无 completed 假象
    has_running = any(m.get("status") == "running" or m.get("live")
                      for m in snap["messages"])
    statuses = [m.get("status") for m in snap["messages"]]
    producer_stopped = any(m["kind"] == "producer" and m.get("status") == "stopped"
                           for m in snap["messages"])
    roster = {p["agent_id"]: p["status"] for p in snap["participants"]}
    print(f"\n[stop] has_running={has_running} producer_stopped={producer_stopped} roster={roster}")
    return 0 if (not has_running and producer_stopped) else 1


# ============ 磁盘 vs Room 一致性（§四十七）============
def verify_against_disk(project, snap):
    pdir = f"projects/{project}/output/agents"
    ok = True
    # bridge_messages 行 <-> room delegation/result
    bm = f"{pdir}/producer/bridge_messages.jsonl"
    rows = []
    if os.path.exists(bm):
        rows = [json.loads(l) for l in open(bm, encoding="utf-8") if l.strip()]
    dispatch_rows = {r["task_id"]: r for r in rows if r.get("sender") == "producer"}
    result_rows = {r["task_id"]: r for r in rows if r.get("sender") != "producer"}
    room_dispatch = {m["task_id"]: m for m in snap["messages"] if m["kind"] == "delegation"}
    room_results = {m["task_id"]: m for m in snap["messages"] if m["kind"] == "specialist_result"}
    for tid, r in dispatch_rows.items():
        m = room_dispatch.get(tid)
        if not m or m["content"] != r.get("objective"):
            print(f"  !! dispatch mismatch {tid}")
            ok = False
    for tid, r in result_rows.items():
        m = room_results.get(tid)
        if not m or m.get("status") != r.get("status"):
            print(f"  !! result status mismatch {tid}")
            ok = False
    # AgentTask structured_result <-> room result verified/changed_refs
    tdir = f"{pdir}/tasks"
    if os.path.isdir(tdir):
        for f in os.listdir(tdir):
            if not f.endswith(".json"):
                continue
            t = json.loads(open(f"{tdir}/{f}", encoding="utf-8").read())
            sr = t.get("structured_result") or {}
            if t.get("capability_id", "").endswith(".delegate") and sr:
                m = room_results.get(t["task_id"])
                if m and m.get("verified") != sr.get("verified"):
                    print(f"  !! verified mismatch {t['task_id']}: room={m.get('verified')} task={sr.get('verified')}")
                    ok = False
    # workflow <-> room
    wf_path = f"{pdir}/producer/workflows.json"
    if os.path.exists(wf_path):
        wfs = json.loads(open(wf_path, encoding="utf-8").read()).get("workflows", {})
        if wfs:
            latest = max(wfs.values(), key=lambda w: w.get("created_at", 0))
            if (snap.get("workflow") or {}).get("workflow_id") != latest["workflow_id"]:
                print("  !! workflow mismatch")
                ok = False
    # 唯一 ID
    ids = [m["id"] for m in snap["messages"]]
    if len(ids) != len(set(ids)):
        print("  !! duplicate message ids")
        ok = False
    return ok


# ============ room 稳定性 ============
def room_stability(n=20):
    snap = _room(ROOM_A)
    seqs = []
    for _ in range(n):
        s = _room(ROOM_A)
        seqs.append([m["id"] for m in s["messages"]])
    stable = all(x == seqs[0] for x in seqs)
    print(f"{n}x reload stable: {stable}")
    _dump_room(ROOM_A, "room.manual")
    return 0 if stable else 1


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "seed":
        seed()
    elif cmd == "casea":
        sys.exit(casea())
    elif cmd == "stop":
        sys.exit(stop_case())
    elif cmd == "room":
        sys.exit(room_stability(int(sys.argv[2]) if len(sys.argv) > 2 else 20))
    else:
        print(__doc__)
        sys.exit(1)
