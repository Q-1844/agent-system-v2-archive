# -*- coding: utf-8 -*-
"""42.md §三 补充提取：first_frame_batches 与英文 prompt"""
import json

P = json.load(open('projects/雨灯归航/output/project.json', encoding='utf-8'))
TARGETS = ['s02_c01', 's02_c02', 's02_c03', 's03_c01', 's03_c02', 's03_c03']

out = {}
for sc in P.get('scenes', []):
    for s in sc.get('shots', []):
        sid = s['shot_id']
        if sid not in TARGETS:
            continue
        out[sid] = {
            'prompt_en': (s.get('prompt_en') or '')[:400],
            'video_prompt_en': (s.get('video_prompt_en') or '')[:400],
            'seed': s.get('seed'),
            'first_frame_batches': [],
        }
        for b in (s.get('first_frame_batches') or []):
            bb = {
                'batch_id': b.get('batch_id'),
                'created_at': b.get('created_at'),
                'kind': b.get('kind'),
                'mode': b.get('mode'),
                'selected_version': b.get('selected_version'),
                'generation_basis': b.get('generation_basis'),
            }
            # 批次里每个候选/版本的 reference 构成
            vers = b.get('versions') or b.get('candidates') or []
            vv = []
            for v in vers:
                vv.append({
                    'id': v.get('version_id') or v.get('candidate_id'),
                    'input_visuals': v.get('input_visuals'),
                    'prompt_head': (v.get('prompt') or '')[:160],
                })
            bb['versions'] = vv
            out[sid]['first_frame_batches'].append(bb)

with open('_tmp/p42_batches_audit.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print('written', len(json.dumps(out)))
