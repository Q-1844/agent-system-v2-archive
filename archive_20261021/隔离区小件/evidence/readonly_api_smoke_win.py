"""Read-only contract smoke against real routers, fake dependencies, no lifespan.
Run with the source project's dependency environment. No real Provider requests.
This does not test production startup, a browser, or the proposed R2 APIs.
"""
import argparse,asyncio,json,socket,sys,tempfile
from pathlib import Path
from types import SimpleNamespace


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args();root=Path(args.source_root).resolve()
    if not (root/'api_server.py').is_file():raise SystemExit('source root invalid')
    sys.path.insert(0,str(root))
    attempts=[]
    # Windows 派生版唯一差异：放行 loopback（127.0.0.1/::1/localhost）。
    # 原因：Windows asyncio ProactorEventLoop 的 self-pipe 走 loopback socketpair，
    # 原版一刀切 connect 守卫会把事件循环自身的环回连接也拦下（Linux 原生
    # socketpair 不经过 connect，故交付环境未触发）。外部地址与外部 DNS 全拒。
    _LOOPBACK = {'localhost', '127.0.0.1', '::1', b'localhost', b'127.0.0.1', b'::1'}
    _real_getaddrinfo = socket.getaddrinfo
    _real_connect = socket.socket.connect
    def deny_dns(host, *a, **kw):
        if host is None or host in _LOOPBACK:
            return _real_getaddrinfo(host, *a, **kw)
        attempts.append('network')
        raise RuntimeError('offline smoke: external DNS blocked')
    def deny_connect(self, address, *a, **kw):
        host = address[0] if isinstance(address, tuple) else None
        if host is None or host in _LOOPBACK:
            return _real_connect(self, address, *a, **kw)
        attempts.append('network')
        raise RuntimeError('offline smoke: external connection blocked')
    socket.getaddrinfo = deny_dns
    socket.socket.connect = deny_connect
    socket.socket.connect_ex = deny_connect
    from fastapi import FastAPI
    import httpx
    import deps
    from src.core.models import Project,Scene,Shot
    from src.core.store import ProjectStore
    from src.core.job_queue import JobQueue
    from routers import system,agents,jobs

    async def exercise(pdir):
        project='handoff_smoke'
        ProjectStore(pdir).save(Project(name=project,scenes=[Scene(scene_id='s01',shots=[Shot(shot_id='s01_c01',scene_id='s01',index=1)])]))
        def resolve(name):
            if name!=project:raise FileNotFoundError(name)
            return pdir
        deps.project_manager=SimpleNamespace(get_project_dir=resolve)
        deps.pipeline_controller=object()
        deps.job_queue=JobQueue(pdir/'isolated_jobs.json',{})
        # Report model unavailability honestly. No fake model success is injected.
        agents.get_agent_runtime=lambda:SimpleNamespace(
            _resolve_agent=lambda *a:object(),_is_enabled=lambda *a:True,
            _resolve_client_or_none=lambda **kw:None)
        app=FastAPI();app.include_router(system.router);app.include_router(agents.router);app.include_router(jobs.router)
        checks=[]
        paths=[('/api/health',200),
            (f'/api/project/{project}/collab-modes',200),
            (f'/api/project/{project}/collab-runs',200),
            (f'/api/project/{project}/jobs',200),
            (f'/api/project/{project}/agents/producer/grant',200),
            (f'/api/project/{project}/collab-runs/missing',404)]
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://offline.invalid') as client:
            for path,status in paths:
                response=await client.get(path);assert response.status_code==status,(path,response.text)
                payload=response.json()
                if path.endswith('/collab-modes'):
                    mode=next(x for x in payload['modes'] if x['mode_id']=='combo_recommended')
                    assert mode['mode_version']=='2.1.0'
                    assert mode['review_policy']['stream_during_execution']
                    assert mode['available'] is False and mode['unavailable_reasons']
                if path.endswith('/collab-runs'):assert payload['runs']==[]
                if path.endswith('/jobs'):assert payload['jobs']==[]
                if path.endswith('/grant'):assert payload['active']==[]
                checks.append({'transport':'ASGI','method':'GET','path':path,'status':status,'result':'passed'})
        # Directly validate SSE initial snapshot and unsubscription; do not hang
        # an in-process ASGI stream waiting for browser disconnect behaviour.
        class Request:
            async def is_disconnected(self):return False
        response=await jobs.jobs_stream(Request(),project=project)
        assert response.media_type=='text/event-stream'
        iterator=response.body_iterator
        snapshot=await asyncio.wait_for(anext(iterator),timeout=2)
        assert 'event: snapshot' in snapshot
        await iterator.aclose()
        checks.append({'transport':'direct_generator','path':'/api/jobs/stream',
                       'result':'passed','scope':'SSE first snapshot and generator cleanup only'})
        assert not attempts,attempts
        return {'kind':'read_only_router_contract_smoke','checks':checks,
                'network_attempts':len(attempts),'provider_calls':0,
                'limits':['fake project manager, queue and controller readiness',
                          'real routers; no api_server lifespan/startup',
                          'no browser, production environment or R2 feature verification']}
    with tempfile.TemporaryDirectory() as temp:
        report=asyncio.run(exercise(Path(temp)))
    output=Path(args.output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'passed_checks':len(report['checks']),'provider_calls':report['provider_calls']}))
if __name__=='__main__':main()
