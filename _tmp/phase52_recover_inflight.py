# -*- coding: utf-8 -*-
"""Phase52 在途任务恢复收货（E03 真实演练）。
对批处理中断留下的已受理任务：先 poll（服务端大概率已完成），完成即下载+抽帧+记账；
仍在生成则如实记录继续等待；绝不重提交。
"""
import asyncio, base64, hashlib, json, os, pathlib, subprocess, sys, time
from datetime import datetime, timezone

REPO = pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard")
OUTDIR = pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流\PHASE52_VIDEO_OUTPUT")
sys.path.insert(0, str(REPO))

INFLIGHT = [
    {"case": "E10e", "shot_id": "s01_c01", "seconds": 10, "video_id": "task_0UMGQA92wQEfpuxl7raoX5d3Ga4bWw8q"},
    {"case": "E10b", "shot_id": "s01_c01", "seconds": 10, "video_id": "task_mL8LXFU4AR7fD0pcCaQK24rDmZtzlW1S"},
    {"case": "E10p2", "shot_id": "s05_c02", "seconds": 10, "video_id": "task_A4CN6VVLRqUqYM1cb5XtkZJOSamP7Fqe"},
    {"case": "E5a", "shot_id": "s01_c01", "seconds": 5, "video_id": "task_wk37hvmgq8d4Q6YSkgNltOFfcGIWxYd4"},
]

def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

async def main():
    env = {}
    for line in (REPO / ".env").read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    import yaml
    cfg = yaml.safe_load((REPO / "config" / "config.yaml").read_text(encoding="utf-8"))
    agnes_cfg = dict(cfg["agnes"]); agnes_cfg["api_key"] = env["AGNES_API_KEY"]
    from src.api.agnes_client import AgnesClient
    from src.core.quota import QuotaLedger
    quota = QuotaLedger(REPO / "cache" / "quota.json",
                        limits={"video_seconds": 500, "images": 4000, "text_calls": 7200})
    client = AgnesClient(agnes_cfg, quota=quota)
    video_model = agnes_cfg["models"]["video"]
    import shutil
    ffbin = shutil.which("ffmpeg") or "ffmpeg"
    out = []
    for t in INFLIGHT:
        rec = {"case": t["case"], "shot_id": t["shot_id"], "video_id": t["video_id"],
               "recover": True, "seconds_requested": t["seconds"]}
        print(f"[{t['case']}] 恢复查询 video_id={t['video_id']}", flush=True)
        try:
            t0 = time.time()
            pres = await client.poll_video(t["video_id"], interval=5, max_wait=300,
                                           model_name=video_model)
            rec["recover_poll_s"] = round(time.time() - t0, 1)
            dest = OUTDIR / f"{t['case']}.mp4"
            await client.download(pres["url"], dest)
            rec["local"] = str(dest)
            rec["local_sha256"] = hashlib.sha256(dest.read_bytes()).hexdigest()
            rec["seconds_returned"] = pres.get("seconds")
            for tag, args in {"first": ["-i", str(dest), "-frames:v", "1"],
                              "mid": ["-ss", str(t["seconds"] / 2), "-i", str(dest), "-frames:v", "1"],
                              "end": ["-sseof", "-0.1", "-i", str(dest), "-frames:v", "1"]}.items():
                outp = OUTDIR / f"{t['case']}_{tag}.png"
                subprocess.run([ffbin, "-y", *args, str(outp)], capture_output=True, text=True)
                rec.setdefault("frames", {})[tag] = outp.exists()
            from src.core.timing_ledger import record as _tl
            _tl("video_downloaded", project="P50_B", shot_id=t["shot_id"], job_id=t["case"],
                video_id=t["video_id"], local=str(dest), seconds_returned=pres.get("seconds"),
                phase52_retest=True, utc=now(), recovered_inflight=True)
            print(f"[{t['case']}] 收货完成（恢复查询 {rec['recover_poll_s']}s）", flush=True)
        except Exception as e:
            rec["status"] = "failed"
            rec["error"] = f"{type(e).__name__}: {str(e)[:200]}"
            print(f"[{t['case']}] 恢复失败: {rec['error']}", flush=True)
        out.append(rec)
    with open(r"C:\Users\曹文淇\Desktop\ai工作流\PHASE52_VIDEO_LEDGER.jsonl", "a", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("RECOVERY DONE")

if __name__ == "__main__":
    asyncio.run(main())
