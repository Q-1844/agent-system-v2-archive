import json, sys
from pathlib import Path
BASE = Path('.')
rd = BASE / 'projects/__cancel_gp_a/output/production_runs/prun_4163f189bc/run.json'
run = json.loads(rd.read_text(encoding='utf-8'))
print('run status=', run.get('status'), 'stage=', run.get('stage'),
      'cancel_requested=', run.get('cancel_requested'))
for s in run.get('scenes', []):
    print('  scene', s.get('scene_id'), 'status=', s.get('status'),
          'child=', s.get('child_run_id'))
d = json.loads((BASE / 'cache/jobs.json').read_text(encoding='utf-8'))
jobs = d if isinstance(d, list) else d.get('jobs', [])
print('--- jobs ---')
for j in jobs:
    if j.get('project') in ('__cancel_gp_a', '__cancel_gp_b') or j.get('type') in ('character_views',):
        print(j.get('type'), j.get('state'), j.get('params', {}).get('shot_id') or
              j.get('params', {}).get('character_name'), j.get('updated_at'))
