# -*- coding: utf-8 -*-
# 《雨灯归航》修复轮——s01_c04 路径 c 样张（幂等，可重复运行）
# 用法：
#   D:\Delta Force\python.exe _tmp/yudeng/fix_round_s01_c04.py            # v2.0 i2v 样张
#   D:\Delta Force\python.exe _tmp/yudeng/fix_round_s01_c04.py --also25   # 追加 2.5 keyframe 对照
# 前提：后端已在 localhost:8000 运行（start.bat）；ffmpeg 在 PATH。
# 产物：融合首帧候选（projects/雨灯归航/output/frames/）、新 VideoVersion、
#       帧检三联 _tmp/yudeng/fix_strip_s01_c04.jpg、对照图 fix_ab.jpg
import asyncio, sys, os, re, json, time
from pathlib import Path
sys.path.insert(0, '.')
from types import SimpleNamespace
from dotenv import load_dotenv
load_dotenv('.env')
import yaml, httpx

ALSO25 = '--also25' in sys.argv
BASE = Path('.').resolve()
PDIR = BASE / 'projects' / '雨灯归航'
PNAME = '雨灯归航'
API = 'http://localhost:8000'
from urllib.parse import quote as _q
PP = _q(PNAME)   # 中文项目名 URL 编码

def http(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = httpx.request(method, API + path, content=data,
                      headers={'Content-Type': 'application/json'}, timeout=120)
    try: return r.json()
    except Exception: return r.text

def log(s):
    print(s, flush=True)
    Path('_tmp/yudeng/fixround_log.txt').open('a', encoding='utf-8').write(s + '\n')

# ---------- 依赖初始化（进程内 handler 需要）----------
import deps
from src.api.agnes_client import AgnesClient
from src.core.quota import QuotaLedger
from src.utils.project_manager import ProjectManager
def load_client():
    cfg = yaml.safe_load(open('config/config.yaml', encoding='utf-8'))['agnes']
    cfg['api_key'] = re.sub(r'\$\{(\w+)\}',
                            lambda m: os.environ.get(m.group(1), ''), cfg['api_key'])
    return AgnesClient(cfg, quota=QuotaLedger.get_default())
deps.agnes_client = load_client()
deps.project_manager = ProjectManager('./projects')
from routers.shots import _handler_first_frame

async def emit(evt, msg, pct):
    log(f'  [{evt}] {msg}')

async def gen_first_frame(shot_id, modes):
    job = SimpleNamespace(project=PNAME, shot_id=shot_id,
                          params={'variants': 2, 'force': True, **modes})
    await _handler_first_frame(job, emit)

def latest_batch(shot_id):
    doc = json.load(open(PDIR / 'output' / 'project.json', encoding='utf-8'))
    for sc in doc['scenes']:
        for s in sc['shots']:
            if s['shot_id'] == shot_id:
                b = (s.get('first_frame_batches') or [])[-1]
                return b
    raise RuntimeError(shot_id + ' not found')

def clear_vref(shot_id):
    from src.core.store import ProjectStore
    store = ProjectStore(PDIR)
    def mut(s): s.video_reference_asset_id = None
    store.update_shot(shot_id, mut)

async def wait_video(job_id, sid, max_poll=20):
    for i in range(max_poll):
        await asyncio.sleep(30)
        j = http('GET', f'/api/project/{PP}/jobs'.replace('/api/project/', '/api/project/'))
        # jobs 路由：/api/project/{p}/jobs
        for k in j.get('jobs', []):
            if k['job_id'] == job_id:
                log(f'  poll {i+1}: {k["state"]} {(k["error"] or "")[:100]}')
                if k['state'] == 'done': return True
                if k['state'] == 'failed': return False
    return False

def extract_strip(local, tag):
    import subprocess
    for t in ('0.3', '4.0', '7.6'):
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', t, '-i', local,
                        '-frames:v', '1', '-q:v', '3',
                        f'_tmp/yudeng/fix_{tag}_{t}.jpg'], check=True)
    subprocess.run(['ffmpeg', '-y', '-v', 'error',
                    '-i', f'_tmp/yudeng/fix_{tag}_0.3.jpg',
                    '-i', f'_tmp/yudeng/fix_{tag}_4.0.jpg',
                    '-i', f'_tmp/yudeng/fix_{tag}_7.6.jpg',
                    '-filter_complex', '[0][1][2]hstack=3', '-q:v', '3',
                    f'_tmp/yudeng/fix_strip_{tag}.jpg'], check=True)

async def main():
    SID = 's01_c04'
    # 1. opening_source（幂等；同场景 s01_c03 已完成视频，gate 允许）
    r = http('POST', f'/api/project/{PP}/shot/{SID}/opening-source',
             {'source': 'reference_previous'})
    log(f'1. opening-source: {json.dumps(r, ensure_ascii=False)[:160]}')

    # 2. 融合首帧（refs=SIV+Look+未点亮组合图+c03尾帧，full+keep）
    log('2. 融合首帧生成（full+keep）...')
    await gen_first_frame(SID, {'scene_reference_mode': 'full',
                                'human_reference_mode': 'keep'})
    batch = latest_batch(SID)
    log(f'   批次 {batch["batch_id"]} 候选: '
        + ', '.join(c['local'] for c in batch['candidates']))
    log('   >>> 人工目检点：候选文件如上（也可以在此改选另一候选，见 README）')

    # 3. 选第一候选（如需改选：POST /shot/s01_c04/first-frame/choose {candidate_id}）
    cid = batch['candidates'][0]['candidate_id']
    r = http('POST', f'/api/project/{PP}/shot/{SID}/first-frame/choose',
             {'candidate_id': cid})
    log(f'3. 选择 {cid}: {r.get("url", "")[:80]}')

    # 4. 切 i2v + 清 vref（路径 a；消除 i2v 上的 relay 残留）
    http('PUT', f'/api/project/{PP}/shot/{SID}', {'link_mode': 'i2v'})
    from src.core.store import ProjectStore
    ProjectStore(PDIR).update_shot(SID, lambda s: setattr(s, 'video_reference_asset_id', None))
    log('4. link_mode=i2v，vref 已清')

    # 5. v2.0 i2v 出片
    j = http('POST', f'/api/project/{PP}/shot/{SID}/video', {})
    job_id = j.get('job_id'); log(f'5. v2.0 提交 {job_id}')
    ok = await wait_video(job_id, SID)
    doc = json.load(open(PDIR / 'output' / 'project.json', encoding='utf-8'))
    vv = None
    for sc in doc['scenes']:
        for s in sc['shots']:
            if s['shot_id'] == SID:
                vv = [v for v in s['video_versions'] if v['version_id'] == s['final_video']][0]
    log(f'   v2.0 版 {vv["version_id"]} {"OK" if ok else "FAILED"} url={vv["url"][:80]}')
    extract_strip(vv['local'], 'v20')

    # 6.（可选）2.5 keyframe 对照
    if ALSO25:
        j = http('POST', f'/api/project/{PP}/shot/{SID}/video?video_model=agnes-video-2.5-flash', {})
        job_id = j.get('job_id'); log(f'6. 2.5 提交 {job_id}')
        ok = await wait_video(job_id, SID)
        doc = json.load(open(PDIR / 'output' / 'project.json', encoding='utf-8'))
        for sc in doc['scenes']:
            for s in sc['shots']:
                if s['shot_id'] == SID:
                    vv = [v for v in s['video_versions'] if v['version_id'] == s['final_video']][0]
        log(f'   2.5 版 {vv["version_id"]} {"OK" if ok else "FAILED"} url={vv["url"][:80]}')
        extract_strip(vv['local'], 'v25')
        # 对照图：旧 relay 版 vv_0c52efca vs 新融合 i2v
        doc = json.load(open(PDIR / 'output' / 'project.json', encoding='utf-8'))
        for sc in doc['scenes']:
            for s in sc['shots']:
                if s['shot_id'] == SID:
                    old = [v for v in s['video_versions'] if v['version_id'] == 'vv_0c52efca'][0]
    # 7. 与旧 relay 版并排（始终生成）
    import subprocess
    doc = json.load(open(PDIR / 'output' / 'project.json', encoding='utf-8'))
    for sc in doc['scenes']:
        for s in sc['shots']:
            if s['shot_id'] == SID:
                old = [v for v in s['video_versions'] if v['version_id'] == 'vv_0c52efca'][0]
    subprocess.run(['ffmpeg', '-y', '-v', 'error',
                    '-ss', '4.0', '-i', old['local'], '-frames:v', '1', '-q:v', '3',
                    '_tmp/yudeng/fix_old_4.0.jpg'], check=True)
    subprocess.run(['ffmpeg', '-y', '-v', 'error',
                    '-i', '_tmp/yudeng/fix_old_4.0.jpg',
                    '-i', '_tmp/yudeng/fix_v20_4.0.jpg',
                    '-filter_complex', '[0][1]hstack', '-q:v', '3',
                    '_tmp/yudeng/fix_ab.jpg'], check=True)
    log('7. 对照图 _tmp/yudeng/fix_ab.jpg（左=旧 relay 版，右=新融合 i2v）')
    log('ACCEPTANCE: 看 fix_strip_v20.jpg 三联——0.3s 应=选中融合首帧（身份接近批准 Look + 承接 c03 尾态），'
        '4s/7.6s 身份不漂；对照 fix_ab.jpg 判断是否消除变体 C。')

asyncio.run(main())