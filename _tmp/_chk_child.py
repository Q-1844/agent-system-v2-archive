import json
from pathlib import Path
BASE = Path('projects/__cancel_gp_a/output')
# child scene run
for cand in (BASE / 'scene_runs').glob('**/run_d5343c0221*.json'):
    print('found', cand)
# autopilot runs root guesses
for pat in ('scene_runs', 'autopilot_runs', 'runs'):
    d = BASE / pat
    if d.exists():
        for f in d.rglob('*.json'):
            try:
                j = json.loads(f.read_text(encoding='utf-8'))
            except Exception:
                continue
            if j.get('run_id') == 'run_d5343c0221':
                print(f, '->', j.get('status'), j.get('stage'))
                for sh in (j.get('shots') or []):
                    print('   shot', sh.get('shot_id'), 'status=', sh.get('status'),
                          'first_frame=', (sh.get('first_frame') or {}).get('status'),
                          'video=', (sh.get('video') or {}).get('status'))
# shot project.json 现状
proj = json.loads((BASE / 'project.json').read_text(encoding='utf-8'))
for sc in proj.get('scenes', []):
    for sh in sc.get('shots', []):
        print('canonical shot', sh.get('shot_id'),
              'ff=', (sh.get('first_frame') or {}).get('status'),
              'video=', (sh.get('video') or {}).get('status'))
