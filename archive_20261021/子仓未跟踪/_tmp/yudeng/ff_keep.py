# 雨灯归航 — s01_c04 / s02_c02 首帧：直调 handler 注入 scene_reference_mode=full + human_reference_mode=keep
# （REST 路由不透传 reference_mode；不改代码，同 handler 同参数语义）
import asyncio, sys
from pathlib import Path
sys.path.insert(0, '.')
from types import SimpleNamespace
import yaml, re, os
from dotenv import load_dotenv
load_dotenv('.env')
import deps
from src.api.agnes_client import AgnesClient
from src.core.quota import QuotaLedger
from src.utils.project_manager import ProjectManager

def load_client():
    cfg = yaml.safe_load(open('config/config.yaml', encoding='utf-8'))['agnes']
    cfg['api_key'] = re.sub(r'\$\{(\w+)\}', lambda m: os.environ.get(m.group(1), ''), cfg['api_key'])
    return AgnesClient(cfg, quota=QuotaLedger.get_default())

deps.agnes_client = load_client()
deps.project_manager = ProjectManager('./projects')

from routers.shots import _handler_first_frame

async def emit(evt, msg, pct):
    print(f'  [{evt}] {msg}')

async def run(shot_id):
    job = SimpleNamespace(project='雨灯归航', shot_id=shot_id,
                          params={'variants': 2, 'force': True,
                                  'scene_reference_mode': 'full',
                                  'human_reference_mode': 'keep'})
    print(f'== {shot_id} (full+keep)')
    await _handler_first_frame(job, emit)

async def main():
    for sid in ['s03_c01','s03_c02','s03_c03']:
        job = SimpleNamespace(project='雨灯归航', shot_id=sid,
                              params={'variants': 2, 'force': True,
                                      'scene_reference_mode': 'context_only',
                                      'human_reference_mode': 'keep'})
        print(f'== {sid} (context_only+keep)')
        await _handler_first_frame(job, emit)

asyncio.run(main())