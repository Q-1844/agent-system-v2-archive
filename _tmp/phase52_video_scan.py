# -*- coding: utf-8 -*-
"""Phase52 视频复测第二批：漂移率扫描（用户授权额度放开）。
A 组 5s vs 10s 同镜对照（s01_c01 空旷镜）；B 组 10s 跨镜头类型扫描；C 组接力链闭环。
串行执行（1 RPM 不扩并发），每条独立 try/except，失败不阻断后续。
用法：python phase52_video_scan.py A1,A2,A3,A4   （逗号分隔用例）
"""
import asyncio, base64, json, os, pathlib, subprocess, sys, time
from datetime import datetime, timezone

REPO = pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard")
OUTDIR = pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流\PHASE52_VIDEO_OUTPUT")
OUTDIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO))
FR = REPO / "projects/P50_B/output/frames"
VO = OUTDIR  # T2 尾帧所在

FF = {
    "s01_c01": FR / "s01_c01_first_v1.png",
    "s01_c02": FR / "s01_c02_first_v1.png",
    "s02_c01": FR / "s01_c05_video_end_vv_2c1efb9f.jpg",   # 接力镜：上游 s01_c05 末帧
    "s03_c03": FR / "s03_c03_first_v1.png",
    "s03_c04": FR / "s03_c04_first_v1.png",
    "s05_c02": FR / "s05_c02_first_v1.png",
    "T2end":   VO / "T2_s03_c02_end.png",                   # C 组：T2 真实生成末帧
}

PROMPTS = {
    "s01_c01": "黄昏平静的开阔海面。太阳低垂，海面泛着金紫光泽。一艘小型机动渔船缓慢向画面右侧航行，船体在画面中很小，拖出细白尾迹；远处海平线平直安静，没有其他船只。镜头固定，仅船体缓慢移动与海面微光波动。写实电影质感。",
    "s01_c02": "黄昏船尾甲板，中年船长穿油布外套双手扶住舵盘，年轻大副穿水手服弯腰收拢渔网，动作熟练。船缓慢航行，两人各司其职无对话。镜头固定中景。写实电影质感。",
    "s02_c01": "船全速逃逸，侧面跟拍，排气口喷出浓重黑烟，船体前倾加速，尾迹白浪翻滚，海面风浪增大。写实电影质感。",
    "s03_c03": "前甲板上，大副被巨浪冲击甩倒在甲板上，右手单手撑住桅杆，左手撑地，身体在倾斜的甲板上滑动，渔网散开；他脸上是震惊与恐惧。手持微晃与船体摇晃同步。写实电影质感。",
    "s03_c04": "船尾操控区，船长死死握住舵盘，身体前倾对抗船体左倾，双眼紧盯前方，牙关紧咬，额头汗珠在暮色反光；船体剧烈震动，舵盘晃动。手持微晃。写实电影质感。",
    "s05_c02": "黄昏海面，渔船缓慢平稳航行，船体带着战斗后的痕迹，浪已平息，夕阳低垂。镜头固定。写实电影质感。",
    "T2end":   "船体保持明显左倾，在巨浪中剧烈摇晃，甲板持续上浪，水面漂浮碎壳残片，黄昏光线。固定机位，画面随涌浪起伏。写实电影质感。",
}

CASES = {
    "A1": {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 5},
    "A2": {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 5},
    "A3": {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 5},
    "A4": {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 10},
    "B1": {"shot_id": "s01_c02", "ff": FF["s01_c02"], "seconds": 10},
    "B2": {"shot_id": "s02_c01", "ff": FF["s02_c01"], "seconds": 10},
    "B3": {"shot_id": "s03_c04", "ff": FF["s03_c04"], "seconds": 10},
    "B4": {"shot_id": "s05_c02", "ff": FF["s05_c02"], "seconds": 10},
    "T3": {"shot_id": "s03_c03(接力链T2end)", "ff": FF["T2end"], "seconds": 10},
    # ---- 第 2 批：样本扩充 + 8s 拐点探测 + 5s 人物镜对照 ----
    "C10a": {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 10},
    "C10b": {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 10},
    "C5a":  {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 5},
    "C5b":  {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 5},
    "C8a":  {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 8},
    "C8b":  {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 8},
    "P5a":  {"shot_id": "s01_c02", "ff": FF["s01_c02"], "seconds": 5},
    "P5b":  {"shot_id": "s01_c02", "ff": FF["s01_c02"], "seconds": 5},
    # ---- 第 3 批：扩大样本至统计可用 ----
    "D10a": {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 10},
    "D10b": {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 10},
    "D10c": {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 10},
    "D10d": {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 10},
    "D8a":  {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 8},
    "D8b":  {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 8},
    "D8c":  {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 8},
    "D10p1": {"shot_id": "s05_c02", "ff": FF["s05_c02"], "seconds": 10},
    "D10p2": {"shot_id": "s05_c02", "ff": FF["s05_c02"], "seconds": 10},
    # ---- 第 4 批：收尾大样本（配额打到 ~370s）----
    "E10a": {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 10},
    "E10b": {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 10},
    "E10c": {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 10},
    "E10d": {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 10},
    "E10e": {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 10},
    "E10p1": {"shot_id": "s05_c02", "ff": FF["s05_c02"], "seconds": 10},
    "E10p2": {"shot_id": "s05_c02", "ff": FF["s05_c02"], "seconds": 10},
    "E10p3": {"shot_id": "s05_c02", "ff": FF["s05_c02"], "seconds": 10},
    "E5a":  {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 5},
    "E5b":  {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 5},
    "E5c":  {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 5},
    "E5d":  {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 5},
    "E8a":  {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 8},
    "E8b":  {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 8},
    "E8c":  {"shot_id": "s01_c01", "ff": FF["s01_c01"], "seconds": 8},
}

def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

async def run_one(case_id, client, video_model):
    case = CASES[case_id]
    rec = {"case": case_id, "shot_id": case["shot_id"], "model": video_model,
           "mode": "i2v", "seconds_requested": case["seconds"],
           "first_frame": str(case["ff"])}
    print(f"\n===== [{case_id}] {case['shot_id']} {case['seconds']}s =====", flush=True)

    from src.core.image_host import build_image_host
    import yaml
    cfg = yaml.safe_load((REPO / "config" / "config.yaml").read_text(encoding="utf-8"))
    ih_cfg = dict(cfg.get("image_host") or {})
    for sect in ("github_pages", "imgbb"):
        sub = ih_cfg.get(sect) or {}
        for k, v in list(sub.items()):
            if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                sub[k] = os.environ.get(v[2:-1], "")
    host = build_image_host(ih_cfg, cache_path=str(REPO / "cache" / "imgbb_cache.json"))
    t0 = time.time()
    ff_url = await host.upload(case["ff"])
    rec["host_duration_s"] = round(time.time() - t0, 1)
    print(f"[{case_id}] 托管 {rec['host_duration_s']}s: {ff_url[:80]}", flush=True)

    from src.core.timing_ledger import record as _tl
    def tl(ev, **kw):
        kw.setdefault("phase52_retest", True); kw.setdefault("utc", now())
        return _tl(ev, **kw)

    tl("video_ready", project="P50_B", shot_id=case["shot_id"], model=video_model,
       mode="i2v", seconds_requested=case["seconds"])
    t1 = time.time()
    res = await client.create_video(PROMPTS[case["shot_id"].split("(")[0]] if case["shot_id"] in PROMPTS else PROMPTS["T2end"],
                                    mode="i2v", image_url=ff_url, duration_s=case["seconds"])
    vid = res.get("video_id") or res.get("task_id")
    rec["video_id"] = vid
    tl("video_submitted", project="P50_B", shot_id=case["shot_id"], job_id=case_id,
       video_id=vid, model=video_model, mode="i2v", seconds_requested=case["seconds"])
    print(f"[{case_id}] 提交 video_id={vid}", flush=True)

    def on_prog(pct, st, waited):
        if st != "pending" or waited % 60 == 0:
            print(f"[{case_id}] poll {st} {pct}% waited={int(waited)}s", flush=True)
    t2 = time.time()
    pres = await client.poll_video(vid, interval=5, on_progress=on_prog, model_name=video_model)
    rec["submit_to_complete_s"] = round(time.time() - t1, 1)
    tl("video_completed", project="P50_B", shot_id=case["shot_id"], job_id=case_id,
       video_id=vid, model=video_model, seconds_returned=pres.get("seconds"))
    print(f"[{case_id}] 完成（提交→完成 {rec['submit_to_complete_s']}s）", flush=True)

    import shutil, hashlib
    dest = OUTDIR / f"{case_id}.mp4"
    await client.download(pres["url"], dest)
    rec["local"] = str(dest)
    rec["total_s"] = round(time.time() - t1, 1)
    rec["local_sha256"] = hashlib.sha256(dest.read_bytes()).hexdigest()
    tl("video_downloaded", project="P50_B", shot_id=case["shot_id"], job_id=case_id,
       video_id=vid, local=str(dest), seconds_returned=pres.get("seconds"))

    ffbin = shutil.which("ffmpeg") or "ffmpeg"
    rec["frames"] = {}
    for tag, args in {"first": ["-i", str(dest), "-frames:v", "1"],
                      "mid": ["-ss", str(case["seconds"] / 2), "-i", str(dest), "-frames:v", "1"],
                      "end": ["-sseof", "-0.1", "-i", str(dest), "-frames:v", "1"]}.items():
        outp = OUTDIR / f"{case_id}_{tag}.png"
        subprocess.run([ffbin, "-y", *args, str(outp)], capture_output=True, text=True)
        rec["frames"][tag] = outp.exists()
    print(f"[{case_id}] 抽帧: {rec['frames']}", flush=True)
    return rec

async def main(case_list):
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
    all_recs = []
    for cid in case_list:
        try:
            all_recs.append(await run_one(cid, client, video_model))
        except Exception as e:
            print(f"[{cid}] FAILED: {type(e).__name__}: {str(e)[:250]}", flush=True)
            all_recs.append({"case": cid, "status": "failed",
                             "error": f"{type(e).__name__}: {str(e)[:250]}"})
    with open(r"C:\Users\曹文淇\Desktop\ai工作流\PHASE52_VIDEO_LEDGER.jsonl", "a", encoding="utf-8") as f:
        for r in all_recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("\n===== BATCH SUMMARY =====")
    for r in all_recs:
        print(r.get("case"), "|", r.get("shot_id"), "|", r.get("seconds_requested"),
              "s |", r.get("submit_to_complete_s", r.get("status")), "s")

if __name__ == "__main__":
    ids = sys.argv[1].split(",") if len(sys.argv) > 1 else list(CASES)
    asyncio.run(main(ids))
