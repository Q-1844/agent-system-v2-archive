# -*- coding: utf-8 -*-
"""Phase 53 A1 run 状态巡检（读盘版，避免 API 投影形状差异）。
用法：python a1_status.py <project> [run_id]
"""
import json, sys, time, pathlib

ROOT = pathlib.Path(r"c:\Users\曹文淇\Desktop\ai工作流\animation-storyboard")
PROJ = sys.argv[1]
RID = sys.argv[2] if len(sys.argv) > 2 else None
RUNS = ROOT / "projects" / PROJ / "output" / "workflows" / "runs"


def latest_run():
    idx = json.load(open(RUNS / "runs_index.json", encoding="utf-8"))
    lst = idx if isinstance(idx, list) else idx.get("runs", [])
    lst = sorted(lst, key=lambda x: x.get("createdAt") or x.get("startedAt") or "")
    return lst[-1].get("runId")


if not RID:
    RID = latest_run()

d = json.load(open(RUNS / f"{RID}.json", encoding="utf-8"))
now = time.strftime("%H:%M:%S")
print(f"[{now}] {PROJ}/{RID} status={d.get('status')} cursor={d.get('cursor')}")
for nid, n in (d.get("nodes") or {}).items():
    if n.get("type") in ("agent", "human_review"):
        atts = n.get("attempts") or []
        last = atts[-1] if atts else {}
        s = last.get("startedAt"); e = last.get("endedAt")
        fmt = lambda t: time.strftime("%H:%M:%S", time.localtime(t)) if t else "-"
        print(f"  {nid:<12} {n.get('status','?'):<10} attempts={len(atts)} "
              f"last={fmt(s)}->{fmt(e)}")
pend = [rv for rv in (d.get("reviews") or []) if rv.get("status") == "pending"]
for rv in pend:
    print(f"PENDING: {rv.get('nodeId')} {rv.get('requestId')} fp={rv.get('fingerprint')}")
    print("  ", str(rv.get("summary") or "")[:260].replace("\n", " "))

evf = RUNS / RID / "events.jsonl"
if evf.exists():
    lines = [json.loads(x) for x in open(evf, encoding="utf-8") if x.strip()]
    print(f"events={len(lines)} recent:")
    for e in lines[-8:]:
        ts = e.get("ts")
        t = time.strftime("%H:%M:%S", time.localtime(ts)) if isinstance(ts, (int, float)) else ts
        print(f"  {t} {e.get('type',''):<22} {e.get('nodeId','') or ''} "
              f"{str(e.get('summary') or e.get('message') or '')[:100]}".replace("\n", " "))
