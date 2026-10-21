# -*- coding: utf-8 -*-
"""Phase 53 复算工具（PHASE53_04 §Python 复算要求）。
从真实数据（run store/events.jsonl/jobs.json/quota.json/project store）复算：
  - runs.csv：一 run 一行
  - events.jsonl 规范化导出（保留原始 ts/kind/name/nodeId/attemptId）
  - media_tasks.csv：每媒体提交（job_id/task/shot/kind/state/时长/秒数/版本）
  - 节点尝试区间 + 审核等待区间 + ready_to_submit（视频 job 相对其首帧/审核前置）
所有输出在 evidence/<project>/ 下。derived 字段全部显式标注。
用法：python p53_metrics.py <project> <run_id>
"""
import json, sys, time, pathlib, csv

ROOT = pathlib.Path(r"c:\Users\曹文淇\Desktop\ai工作流\animation-storyboard")
EB = pathlib.Path(r"c:\Users\曹文淇\Desktop\ai工作流\测试4\PHASE53_TEST\evidence")
PROJ, RID = sys.argv[1], sys.argv[2]
RUNS = ROOT / "projects" / PROJ / "output" / "workflows" / "runs"
OUT = EB / PROJ
OUT.mkdir(parents=True, exist_ok=True)


def iso(epoch):
    if epoch is None:
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(epoch)) + time.strftime(".%f", time.localtime(epoch))[:4]


run = json.load(open(RUNS / f"{RID}.json", encoding="utf-8"))

# ---- runs.csv ----
with open(OUT / "runs.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["run_id", "project", "workflow", "status", "created_at", "updated_at",
                "cursor", "error"])
    w.writerow([RID, PROJ, run.get("workflowId"), run.get("status"),
                run.get("createdAt"), run.get("updatedAt"), run.get("cursor"),
                (run.get("error") or "")[:200]])

# ---- events normalized ----
evs = []
evf = RUNS / RID / "events.jsonl"
if evf.exists():
    for line in open(evf, encoding="utf-8"):
        if line.strip():
            e = json.loads(line)
            evs.append({"seq": e.get("seq"), "ts": e.get("ts"), "kind": e.get("kind"),
                        "nodeId": e.get("nodeId"), "attemptId": e.get("attemptId"),
                        "name": e.get("name"), "ok": e.get("ok"),
                        "label": e.get("label"), "phase": e.get("phase"),
                        "status": e.get("status"), "clock": "system_utc_iso",
                        "derived": False})
with open(OUT / "events.jsonl", "w", encoding="utf-8") as f:
    for e in evs:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

# ---- node attempt intervals（原始区间，不裁剪不合并）----
rows = []
for nid, n in (run.get("nodes") or {}).items():
    for i, a in enumerate(n.get("attempts") or []):
        rows.append({"node": nid, "type": n.get("type"), "attempt": i,
                     "attempt_id": a.get("attemptId"), "status": a.get("status"),
                     "started_epoch": a.get("startedAt"), "ended_epoch": a.get("endedAt"),
                     "started": iso(a.get("startedAt")), "ended": iso(a.get("endedAt")),
                     "dur_s": (round(a["endedAt"] - a["startedAt"], 1)
                               if a.get("startedAt") and a.get("endedAt") else None),
                     "result_status": (a.get("result") or {}).get("status")})
with open(OUT / "node_attempts.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["node"])
    w.writeheader(); w.writerows(rows)

# ---- reviews（审核卡：创建/裁定时刻与裁定者）----
rrows = []
for rv in run.get("reviews") or []:
    rrows.append({"node": rv.get("nodeId"), "request_id": rv.get("requestId"),
                  "status": rv.get("status"),
                  "created_epoch": rv.get("createdAt"), "created": iso(rv.get("createdAt")),
                  "decided_epoch": rv.get("decidedAt"), "decided": iso(rv.get("decidedAt")),
                  "decision": rv.get("decision"),
                  "decided_by_note": (rv.get("note") or "")[:160],
                  "autoApprove": bool(((run.get("snapshot") or {}).get("definition")
                                       and next((nn.get("config", {}).get("autoApprove")
                                                 for nn in run["snapshot"]["definition"]["nodes"]
                                                 if nn.get("id") == rv.get("nodeId")), False))
                                 or None)})
with open(OUT / "reviews.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rrows[0].keys()) if rrows else ["node"])
    w.writeheader(); w.writerows(rrows)

# ---- media tasks：jobs.json 该项目本 run 窗口 + shot 版本信息 ----
jobs = json.load(open(ROOT / "cache" / "jobs.json", encoding="utf-8"))
win = [a.get("startedAt") for n in (run.get("nodes") or {}).values()
       for a in (n.get("attempts") or []) if a.get("startedAt")]
win_start = min(win) - 60 if win else 0
mrows = []
for jid, j in jobs.items():
    if j.get("project") != PROJ:
        continue
    c = j.get("created_at") or 0
    if c < win_start:
        continue
    p = j.get("params") or {}
    mrows.append({"job_id": jid, "shot_id": j.get("shot_id"), "kind": j.get("kind"),
                  "state": j.get("state"), "attempts": j.get("attempts"),
                  "created": iso(c), "started": iso(j.get("started_at")),
                  "finished": iso(j.get("finished_at")),
                  "provider_visible_s": (round(j["finished_at"] - j["started_at"], 1)
                                          if j.get("started_at") and j.get("finished_at") else None),
                  "seconds": p.get("seconds"), "mode": p.get("mode"),
                  "origin_run_id": p.get("origin_run_id"),
                  "error": (j.get("error") or "")[:120],
                  "derived": True})
mrows.sort(key=lambda r: (r["created"] or "", r["shot_id"] or ""))
with open(OUT / "media_tasks.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(mrows[0].keys()) if mrows else ["job_id"])
    w.writeheader(); w.writerows(mrows)

# ---- ready_to_submit（视频 job：ready_at=max(该镜首帧 job finished, 上游审核裁定)；derived）----
ff_done = {}   # shot -> first_frame job finished epoch
for r in mrows:
    if r["kind"] == "first_frame" and r["state"] in ("success", "done", "completed") and r["shot_id"]:
        e = r["finished_epoch"] = None
        # 从原始 jobs 找 epoch
        pass
ff_epochs = {}
for jid, j in jobs.items():
    if (j.get("project") == PROJ and j.get("kind") == "first_frame"
            and (j.get("created_at") or 0) >= win_start
            and j.get("finished_at") and j.get("shot_id")):
        ff_epochs[j["shot_id"]] = max(ff_epochs.get(j["shot_id"], 0), j["finished_at"])
rv_decided = {}
for rv in run.get("reviews") or []:
    if rv.get("decidedAt"):
        rv_decided[rv.get("nodeId")] = max(rv_decided.get(rv.get("nodeId"), 0), rv["decidedAt"])
board_t = rv_decided.get("n_rv_board")
qrows = []
for r in mrows:
    if r["kind"] != "video":
        continue
    # submit epoch
    se = next((j.get("started_at") for jid, j in jobs.items() if jid == r["job_id"]), None)
    ready_cands = [t for t in (ff_epochs.get(r["shot_id"]), board_t) if t]
    ready = max(ready_cands) if ready_cands else None
    r2s = (round(se - ready, 1) if se and ready else None)
    qrows.append({"job_id": r["job_id"], "shot_id": r["shot_id"],
                  "ready_epoch": ready, "ready": iso(ready),
                  "submit_epoch": se, "submit": iso(se),
                  "ready_to_submit_s": r2s,
                  "note": "ready_at=max(首帧job完成,n_rv_board裁定)；审核裁定若晚于ready以审核为准" if ready else "前置缺失=unknown",
                  "derived": True})
with open(OUT / "ready_to_submit.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["job_id", "shot_id", "ready_epoch", "ready",
                                      "submit_epoch", "submit", "ready_to_submit_s", "note", "derived"])
    w.writeheader(); w.writerows(qrows)

# ---- quota 快照 ----
try:
    q = json.load(open(ROOT / "cache" / "quota.json", encoding="utf-8"))
    (OUT / "quota_snapshot.json").write_text(
        json.dumps({"observed_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "ledger": q,
                    "note": "本地保守账本非服务端真值"}, ensure_ascii=False, indent=1),
        encoding="utf-8")
except Exception as e:
    (OUT / "quota_snapshot.json").write_text(json.dumps({"error": str(e)}), encoding="utf-8")

print("metrics written ->", OUT)
print("events:", len(evs), "| node attempts:", len(rows), "| media tasks:", len(mrows),
      "| ready_to_submit:", len(qrows))
