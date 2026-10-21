import httpx, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
r = httpx.post('http://localhost:8000/api/project/__sw_batch_e2e/agents/sessions',
               json={'agent_id': 'script_writer', 'scope_type': 'project', 'scope_id': '__sw_batch_e2e'}, timeout=15)
print(r.status_code, r.text[:500])
r2 = httpx.get('http://localhost:8000/openapi.json', timeout=15)
paths = [p for p in r2.json().get('paths', {}) if 'agents' in p]
print('agent paths:', len(paths))
for p in paths[:10]:
    print(' ', p)
