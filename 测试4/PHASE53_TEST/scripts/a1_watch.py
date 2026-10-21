# -*- coding: utf-8 -*-
"""Phase 53 A1 后台观察器：每 30s 快照 run 状态到 evidence，记录状态迁移。
只读生产数据；观察事件独立标 observed_at/derived=true。
用法：python a1_watch.py <project> <run_id> [max_hours]
"""
import json, sys, time, pathlib

ROOT = pathlib.Path(r"c:\Users\曹文淇\Desktop\ai工作流\animation-storyboard")
EB = pathlib.Path(r"c:\Users\曹文淇\Desktop\ai工作流\测试4\PHASE53_TEST\evidence")
PROJ, RID = sys.argv[1], sys.argv[2]
MAX_H = float(sys.argv[3]) if len(sys.argv) > 3 else 12.0
RUNS = ROOT / "projects" / PROJ / "output" / "workflows" / "runs"
OUT = EB / f"a1_{PROJ}_watch.jsonl"

sig_prev = None
t0 = time.time()
while time.time() - t0 < MAX_H * 3600:
    try:
        d = json.load(open(RUNS / f"{RID}.json", encoding="utf-8"))
        nodes = {nid: n.get("status") for nid, n in (d.get("nodes") or {}).items()}
        pend = [rv.get("nodeId") for rv in (d.get("reviews") or []) if rv.get("status") == "pending"]
        evf = RUNS / RID / "events.jsonl"
        nev = sum(1 for _ in open(evf, encoding="utf-8")) if evf.exists() else 0
        sig = (d.get("status"), json.dumps(nodes, sort_keys=True), tuple(pend), nev)
        rec = {"observed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "derived": True, "run_status": d.get("status"),
               "nodes": nodes, "pending_reviews": pend, "events_n": nev}
        if sig != sig_prev:
            rec["transition"] = True
            sig_prev = sig
            with open(OUT, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except FileNotFoundError:
        pass
    except Exception as e:
        with open(OUT, "a", encoding="utf-8") as f:
            f.write(json.dumps({"observed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                "derived": True, "error": str(e)[:200]}, ensure_ascii=False) + "\n")
    time.sleep(30)
