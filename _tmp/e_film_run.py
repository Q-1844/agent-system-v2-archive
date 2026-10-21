"""E 批参数化组跑：python e_film_run.py <project> <start|poll|evidence> [goal] [hint]"""
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard")
OUT = Path(r"D:\isolated\evidence\e_batch")
API = "http://127.0.0.1:8000"


def api(method, path, payload=None, timeout=120):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(f"{API}{path}", data=body, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def start(project, goal, hint):
    r = api("POST", f"/api/project/{project}/collab-runs", {
        "mode_id": "combo_recommended",
        "params": {"story_goal": goal, "approved_package": True,
                   "duration_hint": hint},
        "granted_by": "e_batch_r11_coverage",
    })
    run = r["run"]
    (OUT / f"run_id_{project}.txt").write_text(run["run_id"], encoding="utf-8")
    print(f"run started: {run['run_id']} v{run['mode_version']} project={project}")
    return run["run_id"]


def poll(project, max_s=14400.0, poll_s=20.0):
    rid = (OUT / f"run_id_{project}.txt").read_text(encoding="utf-8").strip()
    t0 = time.time()
    last = ""
    while time.time() - t0 < max_s:
        try:
            run = api("GET", f"/api/project/{project}/collab-runs/{rid}")["run"]
            jobs = api("GET", f"/api/project/{project}/jobs")["jobs"]
        except Exception as e:
            print(f"[{int(time.time()-t0)}s] poll error: {e}")
            time.sleep(poll_s)
            continue
        js = "; ".join(f"{j['shot_id']}:{j['state']}" for j in jobs) or "-"
        cur = f"{run['status']} | {js}"
        if cur != last:
            print(f"[{int(time.time()-t0)}s] {cur}")
            last = cur
        if run["status"] in ("completed", "completed_with_issues", "failed",
                             "cancelled", "awaiting_relay"):
            print(f"FINAL: {run['status']}")
            return run
        time.sleep(poll_s)
    raise TimeoutError("run 未按时到终态")


def evidence(project):
    rid = (OUT / f"run_id_{project}.txt").read_text(encoding="utf-8").strip()
    run = api("GET", f"/api/project/{project}/collab-runs/{rid}")["run"]
    jobs_all = json.loads((ROOT / "cache" / "jobs.json").read_text(encoding="utf-8"))
    t0 = run.get("created_at") or 0
    media = []
    for j in jobs_all.values():
        if j.get("project") == project and j.get("kind") == "video" \
                and j.get("created_at", 0) >= t0:
            media.append({"job_id": j["job_id"], "shot_id": j.get("shot_id"),
                          "state": j["state"],
                          "dur": round((j.get("finished_at") or j.get("created_at", 0))
                                       - (j.get("created_at") or 0), 0),
                          "error": (j.get("error") or "")[:120]})
    media.sort(key=lambda x: x["job_id"])
    project_data = json.loads((ROOT / "projects" / project / "output" / "project.json")
                              .read_text(encoding="utf-8"))
    versions = {}
    for sc in project_data.get("scenes", []):
        for sh in sc.get("shots", []):
            versions[sh["shot_id"]] = {
                "final_video": sh.get("final_video"),
                "n_versions": len(sh.get("video_versions") or []),
                "video_file": ((sh.get("video_versions") or [{}])[-1].get("local") or ""),
            }
    out = {"schema": "e_film_evidence_v1", "project": project, "run_id": rid,
           "status": run.get("status"),
           "mode": f"{run.get('mode_id')} v{run.get('mode_version')}",
           "created_at": run.get("created_at"), "finished_at": run.get("finished_at"),
           "wall_s": round((run.get("finished_at") or 0) - (run.get("created_at") or 0), 0),
           "steps": run.get("steps"), "review": run.get("review"),
           "repair": run.get("repair"), "relay_count": run.get("relay_count"),
           "decision_requests": run.get("decision_requests"),
           "media_jobs": media, "versions": versions,
           "quota_after": json.loads((ROOT / "cache" / "quota.json").read_text(encoding="utf-8"))}
    p = OUT / f"film_evidence_{project}_{rid}.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("evidence ->", p)
    print(f"status={out['status']} wall={out['wall_s']}s jobs={len(media)} "
          f"states={[m['state'] for m in media]}")
    print(f"quota={out['quota_after']}")
    return out


if __name__ == "__main__":
    project, cmd = sys.argv[1], sys.argv[2]
    if cmd == "start":
        start(project, sys.argv[3], sys.argv[4])
    elif cmd == "poll":
        poll(project)
    elif cmd == "evidence":
        evidence(project)
