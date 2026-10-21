# 雨灯归航 — SIV/组合参考资产 rehost：本地图 → GitHub Pages 公网 URL → 回填 ReferenceAsset
import asyncio, sys, os, re
from pathlib import Path
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('.env')
import yaml

BASE = Path('.').resolve()
cfg = yaml.safe_load(open('config/config.yaml', encoding='utf-8'))
ih = dict(cfg.get('image_host') or {})
for sect in ('github_pages', 'imgbb'):
    sub = ih.get(sect) or {}
    for k, v in list(sub.items()):
        if isinstance(v, str) and v.startswith('${') and v.endswith('}'):
            sub[k] = os.environ.get(v[2:-1], '')
from src.core.image_host import build_image_host
host = build_image_host(ih, cache_path=str(BASE / 'cache' / 'imgbb_cache.json'))

from src.resources.write_service import ResourceWriteService
from src.resources.store import ResourceStore
from src.resources.models import document_revision as doc_rev_fn, reference_asset_revision

PDIR = BASE / 'projects' / '雨灯归航'

ASSETS = [
    'ref_d5881214348a',  # s01 SIV
    'ref_f0a099a2e973',  # s02 SIV
    'ref_826b39576f62',  # s03 SIV
    'ref_3d372c85a955',  # composition lit (otter+lamp)
    'ref_e4e31677e7ab',  # composition unlit
]

async def main():
    ws = ResourceWriteService(PDIR, '雨灯归航')
    doc = ResourceStore(PDIR, '雨灯归航').load()
    for aid in ASSETS:
        a = doc.reference_assets.get(aid)
        if a is None:
            print(aid, 'MISSING'); continue
        if a.url:
            print(aid, 'already has url'); continue
        local = PDIR / a.local
        url = await host.upload(str(local))
        r = await ws.update_reference_asset(aid, lambda m, u=url: setattr(m, 'url', u),
                                            expected_revision=reference_asset_revision(
                                                ResourceStore(PDIR, '雨灯归航').load().reference_assets[aid]))
        print(aid, '->', url, 'ok=', r.get('ok'), r.get('error', ''))

asyncio.run(main())