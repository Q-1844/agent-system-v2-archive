import json
from collections import Counter
for f in ('cache/jobs.json.bak-7ch', 'cache/jobs.json'):
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception as e:
        print(f, 'ERR', e)
        continue
    jobs = d if isinstance(d, list) else d.get('jobs', [])
    print(f, 'total', len(jobs), Counter(j.get('type') for j in jobs))
    # image/video job durations
    for j in jobs:
        st = j.get('started_at'); ct = j.get('completed_at')
        if st and ct and j.get('type') in ('image', 'video', 'first_frame', 'character_views', 'character_views_seg'):
            print('  {} dur={:.1f}s'.format(j.get('type'), ct - st))
