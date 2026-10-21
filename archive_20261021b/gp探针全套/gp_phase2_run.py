"""Phase 2 真机验收 — 驱动 Producer 三案例并收集证据。

用法：python gp_phase2_run.py "<case prompt>" [case_label]
- 创建/复用 Producer session
- POST /turn/stream，消费 SSE 直到 turn.completed
- 打印 final assistant_message + receipts + trace 工具序列
- 读盘 bridge_messages.jsonl / specialist sessions / tasks 汇总

判定从证据，不从最终文本（§6）。
"""
import sys, json, time, os, httpx
sys.path.insert(0, ".")

BASE = "http://localhost:8000"
import os as _os
PROJ = _os.environ.get("PROD_PROJ", "__producer_phase2_smoke")
PDIR = f"projects/{PROJ}"
SESSIONS = {}  # agent_id -> sid（复用）


def create_session(agent_id="producer"):
    if agent_id in SESSIONS:
        return SESSIONS[agent_id]
    r = httpx.post(f"{BASE}/api/project/{PROJ}/agents/sessions",
                   json={"agent_id": agent_id, "scope_type": "project",
                         "scope_id": ""}, timeout=30)
    r.raise_for_status()
    sid = r.json()["session_id"]
    SESSIONS[agent_id] = sid
    return sid


def run_case(prompt, label="case"):
    sid = create_session("producer")
    print(f"\n{'='*70}\n[{label}] Producer turn\n  prompt: {prompt[:120]}\n  sid: {sid}\n{'='*70}")
    t0 = time.time()
    events = []
    final = None
    err = None
    # 流式消费 SSE（长超时：多 Agent 委派分钟级）
    with httpx.Client(timeout=httpx.Timeout(900.0, connect=30.0)) as c:
        with c.stream("POST",
                      f"{BASE}/api/project/{PROJ}/agents/sessions/{sid}/turn/stream",
                      json={"content": prompt, "thinking": False}) as resp:
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
                    else:
                        events.append(ev)
                        # 实时打印关键里程碑
                        if et in ("tool.started", "tool.completed") and ev.get("name", "").endswith(".delegate"):
                            ph = ev.get("phase") or ev.get("status") or ""
                            print(f"  [{time.time()-t0:6.1f}s] {et} {ev.get('name')} {ph} {ev.get('summary','')[:60]}")
                        elif et == "tool.completed" and ev.get("name") == "project.inspect":
                            print(f"  [{time.time()-t0:6.1f}s] inspect: {ev.get('summary','')[:60]}")
    dt = time.time() - t0
    if err:
        print(f"  !! turn.failed: {err}")
    if final is None:
        print(f"  !! no turn.completed result (events={len(events)})")
        return None
    print(f"\n  wall_clock={dt:.1f}s  window_renewals={final.get('window_renewals',0)}")
    print(f"  intent={final.get('intent')}  linked_task_ids={final.get('linked_task_ids')}")
    print(f"  receipts ({len(final.get('receipts',[]))}):")
    for r_ in final.get("receipts", []):
        print(f"    - {r_.get('agent')}: status={r_.get('status')} verified={r_.get('verified')} "
              f"n_tool_calls={r_.get('n_tool_calls')} changed={r_.get('changed_refs')} "
              f"warnings={r_.get('warnings',[])[:2]}")
        print(f"        summary: {(r_.get('summary') or '')[:140]}")
    print(f"  trace tool sequence:")
    for t in final.get("trace", []):
        print(f"    - step{t.get('step')} {t.get('tool')} ok={t.get('ok')} {(t.get('summary') or '')[:70]}")
    print(f"  final assistant_message:\n    {final.get('assistant_message','')[:600]}")
    _dump_disk_evidence(label)
    return final


def _dump_disk_evidence(label):
    """读盘：bridge_messages / specialist sessions / tasks。"""
    print(f"\n  --- disk evidence ({label}) ---")
    bm = f"{PDIR}/output/agents/producer/bridge_messages.jsonl"
    if os.path.exists(bm):
        rows = [json.loads(l) for l in open(bm, encoding="utf-8") if l.strip()]
        # 只看本 turn 新增（最后 N 条）。简化：打印全部 sender→receiver 序列
        print(f"  bridge_messages total={len(rows)}")
        for r in rows[-12:]:
            print(f"    {r.get('sender')}→{r.get('receiver')} status={r.get('status')} "
                  f"obj={(r.get('objective') or '')[:50]}")
    # producer workflow
    wf = f"{PDIR}/output/agents/producer/workflows.json"
    if os.path.exists(wf):
        wfd = json.loads(open(wf, encoding="utf-8").read())
        wfs = wfd.get("workflows", {})
        if wfs:
            w = list(wfs.values())[-1]
            print(f"  workflow: status={w.get('status')} tasks={len(w.get('task_ids',[]))} "
                  f"coord={(w.get('last_coordination_summary') or '')[:120]}")
    # producer session trace（最后一个 assistant 消息的 meta.trace / receipts）
    # specialist sessions
    ag_dir = f"{PDIR}/output/agents/sessions"
    if os.path.isdir(ag_dir):
        for f in sorted(os.listdir(ag_dir)):
            if not f.endswith(".json"):
                continue
            try:
                sd = json.loads(open(f"{ag_dir}/{f}", encoding="utf-8").read())
            except Exception:
                continue
            if sd.get("agent_id") in ("script_writer", "character_designer", "director"):
                msgs = sd.get("messages", [])
                umsgs = [m for m in msgs if m.get("role") == "user"]
                amsgs = [m for m in msgs if m.get("role") == "assistant"]
                print(f"  specialist session {sd.get('agent_id')}({f[:10]}): "
                      f"user_msgs={len(umsgs)} asst_msgs={len(amsgs)}")
                if amsgs:
                    last_meta = (amsgs[-1].get("meta") or {})
                    print(f"    last asst trace tools: "
                          f"{[t.get('tool') for t in (last_meta.get('trace') or [])][:12]}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    prompt = sys.argv[1]
    label = sys.argv[2] if len(sys.argv) > 2 else "case"
    run_case(prompt, label)
