"""Nodeid-level comparison: local full run vs delivery events records. Read-only."""
import json
from collections import defaultdict
from pathlib import Path

LOCAL = Path(r"D:\isolated\evidence\local\a4_full60.events.jsonl")
DELIV_FINAL = Path(r"D:\isolated\COLLAB_FIX_R1_1_20261018\COLLAB_FIX_R1_1\validation\review_r11_final.events.jsonl")
DELIV_BASE = Path(r"D:\isolated\COLLAB_FIX_R1_1_20261018\COLLAB_FIX_R1_1\validation\full_baseline.events.jsonl")
OUT = Path(r"D:\isolated\evidence\local\a4_full60_nodeid_diff.json")


def load(path):
    """nodeid -> {phase: outcome}; plus worst outcome per nodeid."""
    per = defaultdict(dict)
    for line in open(path, encoding="utf-8"):
        e = json.loads(line)
        per[e["nodeid"]][e["when"]] = e["outcome"]
    return per


def worst(phases):
    for bad in ("failed", "error"):
        for ph, oc in phases.items():
            if oc == bad:
                return f"{ph}:{oc}"
    if "passed" in phases.values():
        return "passed"
    return ",".join(f"{ph}:{oc}" for ph, oc in phases.items())


loc, fin, base = load(LOCAL), load(DELIV_FINAL), load(DELIV_BASE)
loc_w = {n: worst(p) for n, p in loc.items()}
fin_w = {n: worst(p) for n, p in fin.items()}
base_w = {n: worst(p) for n, p in base.items()}

only_local = sorted(set(loc_w) - set(fin_w))
only_deliv = sorted(set(fin_w) - set(loc_w))
diff_status = sorted(n for n in set(loc_w) & set(fin_w) if loc_w[n] != fin_w[n])

report = {
    "counts": {
        "local_nodes": len(loc_w),
        "delivery_final_nodes": len(fin_w),
        "local_failed_or_error": sum(1 for v in loc_w.values() if v != "passed"),
        "delivery_failed_or_error": sum(1 for v in fin_w.values() if v != "passed"),
    },
    "nodeids_only_in_local": only_local[:40],
    "nodeids_only_in_delivery": only_deliv[:40],
    "status_diff_local_vs_delivery_final": [
        {"nodeid": n, "local": loc_w[n], "delivery_final": fin_w[n],
         "delivery_baseline": base_w.get(n, "?")} for n in diff_status],
}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report["counts"], ensure_ascii=False))
print(f"only_local={len(only_local)} only_delivery={len(only_deliv)} status_diff={len(diff_status)}")
for d in report["status_diff_local_vs_delivery_final"]:
    print(f"  {d['nodeid'][:90]}\n    local={d['local']}  deliv_final={d['delivery_final']}  deliv_base={d['delivery_baseline']}")
