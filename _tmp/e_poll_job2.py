"""E 批冒烟任务轮询与取证：job 终态 → 版本回执/哈希/配额快照落档。"""
import hashlib
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard")
OUT = Path(r"D:\isolated\evidence\e_batch\smoke_evidence.json")
API = "http://127.0.0.1:8000"
PROJECT = "P56_E_SMOKE"
JOB = "e321ce7adb22"


def api(path):
    with urllib.request.urlopen(f"{API}{path}", timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


t0 = time.time()
last = None
while time.time() - t0 < 900:
    try:
        jobs = api(f"/api/project/{PROJECT}/jobs")["jobs"]
        job = next((j for j in jobs if j["job_id"] == JOB), None)
    except Exception as e:
        print(f"[{int(time.time()-t0)}s] poll error: {e}")
        time.sleep(10)
        continue
    if job is None:
        print("job missing!")
        break
    cur = f"{job['state']} | {job.get('message','')[:60]} | prog={job.get('progress')}"
    if cur != last:
        print(f"[{int(time.time()-t0)}s] {cur}")
        last = cur
    if job["state"] in ("done", "failed", "cancelled"):
        break
    time.sleep(10)

# 终态取证：job 详情 + shot 版本回执 + 配额
time.sleep(2)
project = json.loads((ROOT / "projects" / PROJECT / "output" / "project.json")
                     .read_text(encoding="utf-8"))
shot = next(s for sc in project["scenes"] for s in sc["shots"]
            if s["shot_id"] == "s01_c01")
versions = shot.get("video_versions") or []
evidence = {
    "schema": "e_smoke_evidence_v1",
    "job_id": JOB, "job_state": job["state"], "job_error": job.get("error"),
    "job_params": {k: v for k, v in (job.get("params") or {}).items()
                   if k != "input_manifest"},
    "input_manifest_keys": list((job.get("params") or {}).get("input_manifest", {}).keys()),
    "video_status": shot.get("video", {}).get("status"),
    "video_id": shot.get("video", {}).get("video_id"),
    "task_id": shot.get("video", {}).get("task_id"),
    "final_video": shot.get("final_video"),
    "versions": [{"version_id": v.get("version_id"), "status": v.get("status"),
                  "local": v.get("local"), "video_id": v.get("video_id"),
                  "origin_run_id": v.get("origin_run_id"),
                  "num_frames": v.get("num_frames"),
                  "seconds_returned": v.get("seconds_returned"),
                  "generation_basis": v.get("generation_basis")}
                 for v in versions],
    "local_file": None, "local_sha256": None,
}
if versions and versions[-1].get("local"):
    lp = ROOT / versions[-1]["local"] if not Path(versions[-1]["local"]).is_absolute() \
        else Path(versions[-1]["local"])
    lp = lp if lp.is_file() else ROOT / "projects" / PROJECT / "output" / versions[-1]["local"]
    if Path(str(lp)).is_file():
        evidence["local_file"] = str(lp)
        evidence["local_sha256"] = sha(str(lp))
        evidence["local_bytes"] = Path(str(lp)).stat().st_size
quota = json.loads((ROOT / "cache" / "quota.json").read_text(encoding="utf-8"))
evidence["quota_after"] = quota
OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
print("evidence ->", OUT)
print(f"job={job['state']} versions={len(versions)} final={shot.get('final_video')} "
      f"quota={quota}")
