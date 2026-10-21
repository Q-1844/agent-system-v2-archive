"""E 批 R1.1 验证组：combo v2.1.0 + approved_package 真实 run（P2 冻结包）。
用法: python e_group_run.py start|poll|evidence
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard")
OUT = Path(r"D:\isolated\evidence\e_batch")
API = "http://127.0.0.1:8000"
PROJECT = "P56_E_R11_A"
RUN_FILE = OUT / "group_run_id.txt"


def api(method, path, payload=None, timeout=120):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(f"{API}{path}", data=body, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def start():
    r = api("POST", f"/api/project/{PROJECT}/collab-runs", {
        "mode_id": "combo_recommended",
        "params": {
            "story_goal": "《铁门后的信号》批准工作包视频生产（E 批 R1.1 真实验证组，"
                          "冻结源 P56_P2_SIGNAL/dfbfc4d00e78；链 s01_c01→c02→c03 "
                          "消费上游已接纳末帧；s01_c04/s01_c05/s02_c01 独立镜）",
            "approved_package": True,
            "duration_hint": "24 秒（6 镜 × 4 秒）",
        },
        "granted_by": "e_batch_r11_verification",
    })
    run = r["run"]
    RUN_FILE.write_text(run["run_id"], encoding="utf-8")
    print(f"run started: {run['run_id']} v{run['mode_version']}")
    return run["run_id"]


def poll(max_s=3600.0, poll_s=20.0):
    rid = RUN_FILE.read_text(encoding="utf-8").strip()
    t0 = time.time()
    last = ""
    while time.time() - t0 < max_s:
        try:
            run = api("GET", f"/api/project/{PROJECT}/collab-runs/{rid}")["run"]
        except Exception as e:
            print(f"[{int(time.time()-t0)}s] poll error: {e}")
            time.sleep(poll_s)
            continue
        steps = "; ".join(f"{s['step_id']}:{s.get('status','')}" for s in run.get("steps") or [])
        jobs = api("GET", f"/api/project/{PROJECT}/jobs")["jobs"]
        js = "; ".join(f"{j['job_id'][:6]}:{j['state']}" for j in jobs if j.get('state') != 'done') \
            or "all-done"
        cur = f"{run['status']} | {js} | {steps[:120]}"
        if cur != last:
            print(f"[{int(time.time()-t0)}s] {cur}")
            last = cur
        if run["status"] in ("completed", "completed_with_issues", "failed",
                             "cancelled", "awaiting_relay"):
            print(f"FINAL: {run['status']}")
            return run
        time.sleep(poll_s)
    raise TimeoutError("run 未按时到终态")


def evidence():
    rid = RUN_FILE.read_text(encoding="utf-8").strip()
    run = api("GET", f"/api/project/{PROJECT}/collab-runs/{rid}")["run"]
    jobs_all = json.loads((ROOT / "cache" / "jobs.json").read_text(encoding="utf-8"))
    t0 = run.get("created_at") or 0
    media = []
    for j in jobs_all.values():
        if j.get("project") == PROJECT and j.get("kind") == "video" \
                and j.get("created_at", 0) >= t0:
            media.append({k: j.get(k) for k in
                          ("job_id", "shot_id", "state", "created_at", "started_at",
                           "finished_at", "error")})
            media[-1]["provider_task_id"] = (j.get("params") or {}).get("provider_task_id")
            media[-1]["origin_run_id"] = (j.get("params") or {}).get("origin_run_id")
            media[-1]["repair_of_review"] = (j.get("params") or {}).get("repair_of_review")
    media.sort(key=lambda x: x["created_at"] or 0)
    # 版本回执
    project = json.loads((ROOT / "projects" / PROJECT / "output" / "project.json")
                         .read_text(encoding="utf-8"))
    versions = {}
    for sc in project.get("scenes", []):
        for sh in sc.get("shots", []):
            versions[sh["shot_id"]] = {
                "final_video": sh.get("final_video"),
                "video_status": (sh.get("video") or {}).get("status"),
                "n_versions": len(sh.get("video_versions") or []),
                "end_frame_status": (sh.get("video_end_frame") or {}).get("status"),
                "end_source_version": sh.get("video_end_source_version"),
            }
    out = {
        "schema": "e_group_r11_evidence_v1",
        "project": PROJECT, "run_id": rid,
        "status": run.get("status"),
        "mode": f"{run.get('mode_id')} v{run.get('mode_version')}",
        "snapshot_hash": run.get("snapshot_hash"),
        "created_at": run.get("created_at"), "finished_at": run.get("finished_at"),
        "concurrency_effect": run.get("concurrency_effect"),
        "authorization": run.get("authorization"),
        "steps": run.get("steps"),
        "review": run.get("review"), "repair": run.get("repair"),
        "relay_count": run.get("relay_count"),
        "session_ids": run.get("session_ids"),
        "relay_pending": run.get("relay_pending"),
        "result_excerpt": (run.get("result") or {}).get("assistant_excerpt", "")[:400],
        "media_jobs": media,
        "versions": versions,
        "quota_after": json.loads((ROOT / "cache" / "quota.json").read_text(encoding="utf-8")),
    }
    p = OUT / f"group_evidence_{rid}.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("evidence ->", p)
    print(f"status={out['status']} media_jobs={len(media)} "
          f"states={[m['state'] for m in media]}")
    print(f"quota_after={out['quota_after']}")
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "start"
    if cmd == "start":
        start()
    elif cmd == "poll":
        poll()
    elif cmd == "evidence":
        evidence()
