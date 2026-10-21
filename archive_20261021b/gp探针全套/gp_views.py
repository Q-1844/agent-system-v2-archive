# -*- coding: utf-8 -*-
"""AI-7C-H Golden Path 前置：真实生成赤焰守卫三视图并写入项目 Character.views
（§29 前置：>=1 Character with existing done front/side/back views）。
产物：views done + views_meta.json（记录旧外观 sig，供 K1 新旧对比）。"""
import base64
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import httpx

BASE = "http://127.0.0.1:8000"
PNAME = "AGNES_GoldenPath_H"
CHAR = "赤焰守卫"
DESC = "a flame guardian with red spiky hair and crimson armor, glowing ember eyes"
STYLE = "anime, cinematic"


def main():
    r = httpx.post(f"{BASE}/api/character/generate-chain", json={
        "description": DESC, "style": STYLE, "size_tier": "1K", "ratio": "2:3"},
        timeout=600)
    r.raise_for_status()
    res = r.json()
    assert res.get("success"), f"chain failed: {res.get('error')}"
    seg = res["seg_views"]   # {front, side, back} base64 png（透明底）

    from src.utils.project_manager import ProjectManager
    from src.core.store import ProjectStore
    pdir = ProjectManager(base_dir="projects").get_project_dir(PNAME)
    cdir = pdir / "output" / "characters" / CHAR
    cdir.mkdir(parents=True, exist_ok=True)

    sig = hashlib.sha256((DESC.strip() + "\x00" + STYLE.strip()).encode()).hexdigest()
    views = {}
    for v in ("front", "side", "back"):
        p = cdir / f"{v}_{sig[:8]}_seg.png"
        p.write_bytes(base64.b64decode(seg[v]))
        views[v] = {"url": f"https://seed/{v}.png", "local": str(p),
                    "status": "done"}
    store = ProjectStore(pdir)
    proj = store.load()
    ch = next(c for c in proj.characters if c.name == CHAR)
    from src.core.models import Asset
    ch.views = {k: Asset(**a) for k, a in views.items()}
    store.save(proj)
    (cdir / "views_meta.json").write_text(json.dumps({
        "appearance_sig": sig,
        "views": {k: {"local": a["local"], "url": a["url"], "status": "done"}
                  for k, a in views.items()},
        "updated_at": time.time()}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("VIEWS_SEEDED", json.dumps({"char": CHAR, "sig8": sig[:8],
          "files": sorted(x.name for x in cdir.glob('*.png'))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
