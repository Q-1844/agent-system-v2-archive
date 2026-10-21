# -*- coding: utf-8 -*-
"""Phase52 真实图片链路复验（CodeBuddy）。只做图片，不提交视频（视频配额 488/500 已近耗尽）。
固定条件：agnes-image-2.1-flash / 1K 档 16:9 / 思考模式不涉及（图片直出）。
测试项：
  I1 船长身份：i2i 复用已批准船长 Look（ref_e5e8b8e0a54c）
  I2 船与环境：i2i 复用已批准渔船 Look（ref_87639e9db8d5，本地缺失已从 URL 下载到冻结目录）
每个测试：记录提交/受理/完成时刻、真实模型、耗时、结果 URL/本地落盘、成功/失败。
结果追加写入 PHASE52_IMAGE_LEDGER.jsonl，输出图落盘 PHASE52_IMAGE_OUTPUT/。
"""
import asyncio, base64, json, os, pathlib, time, sys
from datetime import datetime, timezone

REPO = pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard")
OUTDIR = pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流\PHASE52_IMAGE_OUTPUT")
LEDGER = pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流\PHASE52_IMAGE_LEDGER.jsonl")
OUTDIR.mkdir(parents=True, exist_ok=True)
import sys
sys.path.insert(0, str(REPO))

# ---- 载入 .env（只取 AGNES_API_KEY，绝不打印）----
env = {}
for line in (REPO / ".env").read_text(encoding="utf-8", errors="replace").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
if not env.get("AGNES_API_KEY"):
    print("FATAL: .env 无 AGNES_API_KEY"); sys.exit(2)

import yaml
cfg = yaml.safe_load((REPO / "config" / "config.yaml").read_text(encoding="utf-8"))
agnes_cfg = dict(cfg["agnes"])
agnes_cfg["api_key"] = env["AGNES_API_KEY"]
agnes_cfg["models"] = {k: v for k, v in agnes_cfg["models"].items()}

from src.api.agnes_client import AgnesClient
from src.core.quota import QuotaLedger

def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

def append_ledger(rec):
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def ref_b64(local_path: pathlib.Path) -> str:
    mime = "image/png"
    return f"data:{mime};base64," + base64.b64encode(local_path.read_bytes()).decode()

async def main():
    quota = QuotaLedger(REPO / "cache" / "quota.json",
                        limits={"video_seconds": 500, "images": 4000, "text_calls": 7200})
    client = AgnesClient(agnes_cfg, quota=quota)
    model = agnes_cfg["models"]["image"]
    print("image model:", model, "| base_url:", agnes_cfg["base_url"], "| tier 1K 16:9")

    tests = [
        {
            "test_id": "I1_captain_identity",
            "name": "船长身份",
            "ref": REPO / "projects" / "P50_B" / "output" / "resources" / "looks"
                   / "look_f171aea96f3e" / "generations" / "gen_b0e5289f766e" / "candidate_01.png",
            "prompt": ("写实电影质感。中年渔船船长，头戴深色旧油布帽，身穿皱褶油布防水外套，"
                       "双手扶住木质舵盘，目光平静望向前方开阔海面。黄昏暖光，人物与参考图"
                       "身份、服装、脸部特征保持一致，不要出现额外人物。"),
        },
        {
            "test_id": "I2_boat_environment",
            "name": "船与环境",
            "ref": pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流\PHASE52_FROZEN_INPUTS")
                   / "03_approved_materials" / "look_96e67a3354c3__ref_87639e9db8d5.png",
            "prompt": ("写实电影质感。一艘小型机动渔船右舷侧视全貌，甲板空无一人，"
                       "黄昏开阔海面，低暖光线，船尾拖出淡淡白浪。保持参考图的船体结构、"
                       "配色与环境光线一致，不要出现人物。"),
        },
    ]

    for t in tests:
        rec = {"test_id": t["test_id"], "name": t["name"], "model": model,
               "size_tier": "1K", "ratio": "16:9", "mode": "i2i",
               "ref_exists": t["ref"].exists(), "ref_sha256": None}
        if not t["ref"].exists():
            rec["status"] = "skip"; rec["error"] = f"参考图缺失: {t['ref']}"
            append_ledger(rec); print("SKIP", t["test_id"], "ref missing"); continue
        import hashlib
        rec["ref_sha256"] = hashlib.sha256(t["ref"].read_bytes()).hexdigest()
        t0 = time.time()
        rec["submitted_at"] = now()
        try:
            res = await client.generate_image(
                t["prompt"], image_refs=[ref_b64(t["ref"])],
                size_tier="1K", ratio="16:9")
            rec["accepted_at"] = now()
            rec["duration_s"] = round(time.time() - t0, 2)
            url = res.get("url"); b64 = res.get("b64")
            if url:
                rec["url"] = url; rec["status"] = "success"
                # 下载落盘（无认证 client）
                import httpx
                async with httpx.AsyncClient(timeout=120, follow_redirects=True) as c:
                    rr = await c.get(url)
                    if rr.status_code == 200:
                        outp = OUTDIR / f"{t['test_id']}.png"
                        outp.write_bytes(rr.content)
                        rec["local"] = str(outp)
                        rec["local_sha256"] = hashlib.sha256(rr.content).hexdigest()
                        rec["downloaded_at"] = now()
                    else:
                        rec["download_http"] = rr.status_code
            elif b64:
                outp = OUTDIR / f"{t['test_id']}.png"
                outp.write_bytes(base64.b64decode(b64))
                rec["local"] = str(outp); rec["status"] = "success"
                rec["local_sha256"] = hashlib.sha256(outp.read_bytes()).hexdigest()
            else:
                rec["status"] = "failed"; rec["error"] = "无 url 也无 b64"
            print("RESULT", t["test_id"], rec["status"],
                  f"{rec.get('duration_s')}s", rec.get("url", "")[:80])
        except Exception as e:
            rec["status"] = "failed"
            rec["duration_s"] = round(time.time() - t0, 2)
            rec["error"] = f"{type(e).__name__}: {str(e)[:300]}"
            print("FAILED", t["test_id"], rec["error"])
        append_ledger(rec)

if __name__ == "__main__":
    asyncio.run(main())
    print("LEDGER:", LEDGER)
