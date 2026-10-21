# 雨灯归航 — 铜灯视觉参考 v2：独立 AgnesClient（config.yaml 同源）→ 注册 → 挂载
import asyncio, sys
from pathlib import Path
sys.path.insert(0, '.')
import yaml
from src.api.agnes_client import AgnesClient
from src.core.quota import QuotaLedger
from src.resources.write_service import ResourceWriteService
from src.resources.store import ResourceStore
from src.resources.models import document_revision as _doc_rev_fn
PDIR_ABS = Path('projects/雨灯归航').resolve()
def doc_rev():
    return str(_doc_rev_fn(ResourceStore(PDIR_ABS, PNAME).load()))

PDIR = Path('projects/雨灯归航')
PNAME = '雨灯归航'

def load_client():
    from dotenv import load_dotenv
    load_dotenv('.env')
    import os, re
    cfg = yaml.safe_load(open('config/config.yaml', encoding='utf-8'))['agnes']
    cfg['api_key'] = re.sub(r'\$\{(\w+)\}', lambda m: os.environ.get(m.group(1), ''), cfg['api_key'])
    return AgnesClient(cfg, quota=QuotaLedger.get_default())

async def main():
    ws = ResourceWriteService(PDIR, PNAME)
    client = load_client()
    prompt = ("Object design sheet: an old brass lantern with a red-painted handle "
              "(paint chipped and worn), warm brass body with gentle patina, a glass "
              "chimney, small sturdy base; 2D hand-drawn storybook style, soft "
              "watercolor shading, clean line art, plain white background, centered, "
              "high quality, detailed")
    res = await client.generate_image(prompt=prompt, size_tier="1K", ratio="1:1")
    url = res.get("url")
    assert url, res
    dest = PDIR / 'output' / 'resources' / 'props'
    dest.mkdir(parents=True, exist_ok=True)
    local = dest / 'lantern_ref_01.png'
    await client.download(url, str(local))
    print('lamp url:', url)
    r_reg = await ws.register_reference_asset(local=str(local.relative_to(PDIR).as_posix()),
                                              view='hero', purpose='prop_reference', source='agnes',
                                              expected_document_revision=doc_rev())
    assert r_reg.get('ok'), r_reg
    asset = type('A',(),{'asset_id': r_reg.get('asset_id') or (r_reg.get('after') or {}).get('asset_id')})
    print('asset:', asset.asset_id)
    r = await ws.attach_prop_reference('prop_fb1bd0b18fb1', asset.asset_id,
                                       expected_revision=doc_rev())
    print('attach ok:', r.get('ok'), r.get('error', ''))
    print('ASSET_ID=' + asset.asset_id)

asyncio.run(main())