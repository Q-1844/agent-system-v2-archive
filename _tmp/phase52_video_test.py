# -*- coding: utf-8 -*-
"""Phase52 真实视频链路复测（CodeBuddy）。额度已刷新，串行 2 条（不扩并发，1 RPM）。

T1 s01_c01（效率基线镜，i2v 10s）：选中首帧 s01_c01_first_v1.png
T2 s03_c02（高难接力镜，i2v 10s）：真实接力端点 s03_c01_video_end_vv_916fba97.jpg

真实路径组件：GithubPagesHost 托管首帧（E15 真实链路）→ AgnesClient.create_video
（限流/配额预检）→ poll_video（自适应轮询）→ download → ffmpeg 抽帧（含 -sseof -0.1
系统接力端点同款取法，E16 验证）。计时调用系统 timing_ledger.record（同事件名，
phase52_retest=true 标记，与历史 n=82 基线同口径可直接对比）。
用法：python phase52_video_test.py T1   /   T2
"""
import asyncio, base64, json, os, pathlib, random, subprocess, sys, time
from datetime import datetime, timezone

REPO = pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard")
OUTDIR = pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流\PHASE52_VIDEO_OUTPUT")
OUTDIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO))

CASES = {
    "T1": {
        "shot_id": "s01_c01",
        "first_frame": REPO / "projects/P50_B/output/frames/s01_c01_first_v1.png",
        "prompt": ("黄昏平静的开阔海面。太阳低垂，海面泛着金紫光泽。一艘小型机动渔船缓慢"
                   "向画面右侧航行，船体在画面中很小，拖出细白尾迹；远处海平线平直安静，"
                   "没有其他船只。镜头固定，仅船体缓慢移动与海面微光波动。写实电影质感。"),
        "seconds": 10,
        "mode": "i2v",
    },
    "T2": {
        "shot_id": "s03_c02",
        "first_frame": REPO / "projects/P50_B/output/frames/s03_c01_video_end_vv_916fba97.jpg",
        "prompt": ("一条巨大触须从船体右舷旁的水下猛然甩出，拍击船体右舷，掀起巨浪将船体"
                   "打侧，水花与碎壳飞散，船体向左倾斜近三十度，右舷被击点水柱冲天而起。"
                   "固定机位，画面随冲击震动。写实电影质感。"),
        "seconds": 10,
        "mode": "i2v",
    },
}

def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

def tl_record(event, **fields):
    from src.core.timing_ledger import record
    fields.setdefault("phase52_retest", True)
    fields.setdefault("utc", now())
    return record(event, **fields)

async def main(case_id):
    case = CASES[case_id]
    # .env（不打印密钥）
    env = {}
    for line in (REPO / ".env").read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    os.environ.setdefault("GITHUB_TOKEN", env.get("GITHUB_TOKEN", ""))

    import yaml
    cfg = yaml.safe_load((REPO / "config" / "config.yaml").read_text(encoding="utf-8"))
    agnes_cfg = dict(cfg["agnes"]); agnes_cfg["api_key"] = env["AGNES_API_KEY"]
    from src.api.agnes_client import AgnesClient
    from src.core.quota import QuotaLedger
    quota = QuotaLedger(REPO / "cache" / "quota.json",
                        limits={"video_seconds": 500, "images": 4000, "text_calls": 7200})
    client = AgnesClient(agnes_cfg, quota=quota)
    video_model = agnes_cfg["models"]["video"]

    rec = {"case": case_id, "shot_id": case["shot_id"], "model": video_model,
           "mode": case["mode"], "seconds_requested": case["seconds"]}
    print(f"[{case_id}] shot={case['shot_id']} model={video_model} mode={case['mode']} "
          f"seconds={case['seconds']}")

    # 1) 托管首帧 → 公网 URL（系统默认 github_pages 链路）
    from src.core.image_host import build_image_host
    ih_cfg = dict(cfg.get("image_host") or {})
    for sect in ("github_pages", "imgbb"):
        sub = ih_cfg.get(sect) or {}
        for k, v in list(sub.items()):
            if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                sub[k] = os.environ.get(v[2:-1], "")
    host = build_image_host(ih_cfg, cache_path=str(REPO / "cache" / "imgbb_cache.json"))
    t0 = time.time()
    ff_url = await host.upload(case["first_frame"])
    rec["first_frame"] = str(case["first_frame"])
    rec["first_frame_host_url"] = ff_url
    rec["host_duration_s"] = round(time.time() - t0, 1)
    print(f"[{case_id}] 首帧托管 OK（{rec['host_duration_s']}s）: {ff_url[:90]}")

    # 2) 提交（quota.can 预检在 create_video 内部）
    tl_record("video_ready", project="P50_B", shot_id=case["shot_id"],
              model=video_model, mode=case["mode"],
              seconds_requested=case["seconds"])
    t1 = time.time()
    res = await client.create_video(case["prompt"], mode=case["mode"],
                                    image_url=ff_url, duration_s=case["seconds"])
    vid = res.get("video_id") or res.get("task_id")
    rec["video_id"] = vid
    rec["submitted_at"] = now()
    tl_record("video_submitted", project="P50_B", shot_id=case["shot_id"],
              job_id=case_id, video_id=vid, model=video_model, mode=case["mode"],
              seconds_requested=case["seconds"])
    print(f"[{case_id}] 已提交 video_id={vid}（{round(time.time()-t1,1)}s）")

    # 3) 轮询（系统默认节奏：5s→60s 后 20s）
    def on_prog(pct, st, waited):
        print(f"[{case_id}] poll {st} {pct}% waited={int(waited)}s", flush=True)
    t2 = time.time()
    pres = await client.poll_video(vid, interval=5, on_progress=on_prog,
                                   model_name=video_model)
    rec["poll_duration_s"] = round(time.time() - t2, 1)
    rec["completed_at"] = now()
    tl_record("video_completed", project="P50_B", shot_id=case["shot_id"],
              job_id=case_id, video_id=vid, model=video_model,
              seconds_returned=pres.get("seconds"), size=pres.get("size"))
    print(f"[{case_id}] 服务端完成（轮询 {rec['poll_duration_s']}s）url={pres['url'][:80]}")

    # 4) 下载
    dest = OUTDIR / f"{case_id}_{case['shot_id']}.mp4"
    await client.download(pres["url"], dest)
    rec["local"] = str(dest)
    rec["local_bytes"] = dest.stat().st_size
    rec["total_duration_s"] = round(time.time() - t1, 1)
    tl_record("video_downloaded", project="P50_B", shot_id=case["shot_id"],
              job_id=case_id, video_id=vid, local=str(dest),
              seconds_returned=pres.get("seconds"))
    print(f"[{case_id}] 下载完成 {rec['local_bytes']}B，端到端（提交→落盘）"
          f"{rec['total_duration_s']}s")

    # 5) ffmpeg 抽帧：首/中/尾（尾帧用系统接力同款 -sseof -0.1，E16）
    import shutil
    ffbin = shutil.which("ffmpeg") or "ffmpeg"
    frames = {}
    for tag, args in {
        "first": ["-i", str(dest), "-frames:v", "1"],
        "mid":   ["-ss", "5", "-i", str(dest), "-frames:v", "1"],
        "end":   ["-sseof", "-0.1", "-i", str(dest), "-frames:v", "1"],
    }.items():
        outp = OUTDIR / f"{case_id}_{case['shot_id']}_{tag}.png"
        r = subprocess.run([ffbin, "-y", *args, str(outp)],
                           capture_output=True, text=True)
        frames[tag] = {"path": str(outp), "ok": outp.exists(),
                       "bytes": outp.stat().st_size if outp.exists() else 0}
        print(f"[{case_id}] 抽帧 {tag}: {'OK' if frames[tag]['ok'] else 'FAIL'}")
    rec["frames"] = frames

    import hashlib
    rec["local_sha256"] = hashlib.sha256(dest.read_bytes()).hexdigest()
    with open(r"C:\Users\曹文淇\Desktop\ai工作流\PHASE52_VIDEO_LEDGER.jsonl",
              "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[{case_id}] DONE 全部计时已入 timing_ledger（phase52_retest=true）")

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "T1"))
