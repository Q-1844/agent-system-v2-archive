"""从工程数据程序化生成 E 部看片页条目（写入 e_review_server_E.py 的 SHOTS 数据）。"""
import json
from pathlib import Path

ROOT = Path(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard")
PROJ = "P56_E_FULL_E"

project = json.loads((ROOT / "projects" / PROJ / "output" / "project.json").read_text(encoding="utf-8"))
review = None
rvw = Path(ROOT / "projects" / PROJ / "output" / "agents" / "review_pipeline" / "rvw_210f31ea.json")
if rvw.exists():
    review = json.loads(rvw.read_text(encoding="utf-8"))
verdicts = {}
if review:
    for e in review.get("results", []):
        fired = set()
        for fr in e.get("frames") or []:
            fired |= set(fr.get("hard_dims_fired") or [])
        verdicts[e["shot_id"]] = (e.get("overall"), sorted(fired))

decisions = {}
run = json.loads((ROOT / "projects" / PROJ / "output" / "agents" / "collab_runs" / "run_e214e08766.json").read_text(encoding="utf-8"))
for d in run.get("decision_requests") or []:
    for sid in d.get("shot_ids") or []:
        decisions[sid] = d.get("hard_errors")

entries = []
for sc in project.get("scenes", []):
    for sh in sc.get("shots", []):
        sid = sh["shot_id"]
        vv = sh.get("video_versions") or []
        last = vv[-1] if vv else {}
        fname = Path(last.get("local") or "").name
        if not fname:
            continue
        overall, fired = verdicts.get(sid, ("?", []))
        dec = decisions.get(sid)
        machine = f"机器审查 {overall}"
        if fired:
            machine += f"（触发维度: {', '.join(fired)}）"
        if dec:
            machine += f" → 决策单待答复（{', '.join(dec)}）"
        elif overall == "pass":
            machine += " ✓"
        dlg = (sh.get("dialogue") or "").strip()
        desc_bits = [f"段{sh.get('scene_id','')} {sid}"]
        if dlg:
            desc_bits.append("台词: " + dlg[:40])
        if sh.get("source_shot_id"):
            desc_bits.append(f"接力←{sh['source_shot_id']}")
        entries.append({
            "shot": sid, "proj": PROJ, "file": fname,
            "desc": "；".join(desc_bits),
            "machine": machine,
            "suggest": "8-10s；" + ("整段保留候选" if overall == "pass" else "请肉眼复核"),
        })

out = Path(r"C:\Users\曹文淇\Desktop\ai工作流\测试7\film_E_shots.json")
out.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{len(entries)} entries -> {out}")
print("pass:", sum(1 for e in entries if "pass" in e["machine"]),
      "| decision:", sum(1 for e in entries if "决策单" in e["machine"]),
      "| incomplete:", sum(1 for e in entries if "incomplete" in e["machine"]))
