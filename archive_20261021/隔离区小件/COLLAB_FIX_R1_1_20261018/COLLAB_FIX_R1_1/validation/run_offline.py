import sys,os,socket,json
from pathlib import Path

def main():
    root=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    os.chdir(root);sys.path.insert(0,str(root));os.environ['WF_STARTUP_RECOVERY_DISABLE']='1'
    original_dns=socket.getaddrinfo;original_connect=socket.socket.connect
    
    def dns(host,*a,**kw):
        if host not in (None,'localhost','127.0.0.1','::1',b'localhost',b'127.0.0.1',b'::1'):
            raise OSError('offline test: external DNS blocked')
        return original_dns(host,*a,**kw)
    def connect(self,address):
        if self.family in (socket.AF_INET,socket.AF_INET6) and address[0] not in ('127.0.0.1','::1'):
            raise OSError('offline test: external connection blocked')
        return original_connect(self,address)
    socket.getaddrinfo=dns;socket.socket.connect=connect
    import pytest
    class Evidence:
        def pytest_runtest_logreport(self,report):
            with out.with_suffix('.events.jsonl').open('a') as f:
                f.write(json.dumps({'nodeid':report.nodeid,'when':report.when,'outcome':report.outcome,
                                    'duration':report.duration,'failure':str(report.longrepr)[:12000] if report.failed else None})+'\n')
        def pytest_collectreport(self,report):
            if report.failed:
                with out.with_suffix('.events.jsonl').open('a') as f:
                    f.write(json.dumps({'nodeid':report.nodeid,'when':'collect','outcome':'failed','failure':str(report.longrepr)[:12000]})+'\n')
    args=sys.argv[3:] or ['tests/','-q','--tb=short','--disable-warnings','--timeout=10']
    code=pytest.main(args+['--junitxml='+str(out.with_suffix('.xml'))],plugins=[Evidence()])
    out.with_suffix('.exit.json').write_text(json.dumps({'exit_code':int(code),'network':'external DNS and TCP blocked','root':str(root)}))
    raise SystemExit(int(code))

if __name__ == "__main__":
    main()
