"""Controlled offline scheduling benchmark; no real Provider calls or speed estimate.
Run from the validated source root, passing the output JSON path as argv[1].
"""
import asyncio,json,statistics,sys,tempfile,time
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path.cwd()))
from src.core.models import Project,Scene,Shot,VideoAsset,VideoVersion
from src.core.store import ProjectStore
from src.agents import review_pipeline as rp

SHOTS=6;GENERATION_S=.12;VISION_FRAME_S=.06;REPEATS=3

def fake_extract(pdir,project,shot,**kw):
    version=next(v for v in shot.video_versions if v.version_id==shot.final_video)
    if not Path(version.local).is_file():raise FileNotFoundError(version.local)
    return {'local':version.local,'source':{'version_id':version.version_id}}
rp.extract_shot_frame_local=fake_extract

async def measure(mode):
    with tempfile.TemporaryDirectory() as tmp:
        pdir=Path(tmp);store=ProjectStore(pdir)
        shots=[Shot(shot_id=f's01_c{i+1:02}',scene_id='s01',index=i+1,
                    video=VideoAsset(num_frames=121,frame_rate=24)) for i in range(SHOTS)]
        store.save(Project(name='simulation',scenes=[Scene(scene_id='s01',shots=shots)]))
        jobs={s.shot_id:SimpleNamespace(project='simulation',kind='video',shot_id=s.shot_id,state='queued') for s in shots}
        queue=SimpleNamespace(jobs=jobs);calls=[]
        rt=SimpleNamespace(_resolve_client_or_none=lambda **kw:object(),_resolve_job_queue_or_none=lambda:queue)
        async def vision(*a,**kw):
            calls.append(time.perf_counter());await asyncio.sleep(VISION_FRAME_S)
            return {'review':{'dimensions':{d:{'status':'pass'} for d in rp.VIDEO_HARD_DIMS}},'derived':{'overall':'pass'}}
        rp.review_shot_core=vision
        start=time.perf_counter();live=None
        if mode=='overlap_review_2':
            live=rp.LiveReviewSession(rt,pdir,'simulation',concurrency=2,interval_s=.005);live.start()
        for i,s in enumerate(shots):
            jobs[s.shot_id].state='running';await asyncio.sleep(GENERATION_S)
            path=pdir/f'{s.shot_id}.mp4';path.write_bytes(b'simulated video')
            def complete(shot):
                version=VideoVersion(version_id=f'new_{i}',status='done',local=str(path),seconds_returned=5)
                shot.video_versions.append(version);shot.final_video=version.version_id
                shot.video.mark_done(str(path),'https://offline.invalid/video')
            store.update_shot(s.shot_id,complete);jobs[s.shot_id].state='done'
        generation_end=time.perf_counter()
        if live:await live.close()
        result=await rp.run_independent_review(rt,pdir,'simulation',max_concurrency=1 if mode=='after_review_1' else 2,
                    cached_results=live.cache if live else None)
        end=time.perf_counter()
        assert result['machine_passed'] and len(result['results'])==SHOTS and len(calls)==SHOTS*3
        return {'mode':mode,'wall_s':round(end-start,4),'generation_wall_s':round(generation_end-start,4),
                'review_tail_s':round(end-generation_end,4),'vision_calls':len(calls),
                'review_started_during_generation':bool(calls and min(calls)<generation_end),
                'cache_reused':sum(bool(x.get('cache_reused')) for x in result['results'])}

async def main():
    samples=[]
    for _ in range(REPEATS):
        for mode in ['after_review_1','after_review_2','overlap_review_2']:samples.append(await measure(mode))
    medians=[]
    for mode in ['after_review_1','after_review_2','overlap_review_2']:
        group=[s for s in samples if s['mode']==mode]
        medians.append({'mode':mode,'wall_s':round(statistics.median(s['wall_s'] for s in group),4),
                        'review_tail_s':round(statistics.median(s['review_tail_s'] for s in group),4)})
    report={'kind':'controlled_offline_simulation','shot_count':SHOTS,'generation_concurrency':1,
        'generation_delay_per_shot_s':GENERATION_S,'vision_delay_per_frame_s':VISION_FRAME_S,'frames_per_shot':3,
        'repeats':REPEATS,'medians':medians,'samples':samples,
        'limits':'Artificial delays and fake frames; excludes real model latency, rate limits, quota and visual quality. Does not estimate production speedup.'}
    Path(sys.argv[1]).write_text(json.dumps(report,indent=2));print(json.dumps(report['medians']))
if __name__=='__main__':asyncio.run(main())
