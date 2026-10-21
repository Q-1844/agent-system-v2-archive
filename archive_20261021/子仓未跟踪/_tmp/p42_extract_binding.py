# -*- coding: utf-8 -*-
"""42.md §三 binding 审计数据提取：偏差组 vs 贴定义组五+1镜"""
import json, sys

P = json.load(open('projects/雨灯归航/output/project.json', encoding='utf-8'))
TARGETS = ['s02_c01', 's02_c02', 's02_c03', 's03_c01', 's03_c02', 's03_c03']

out = {}
for sc in P.get('scenes', []):
    for s in sc.get('shots', []):
        sid = s['shot_id']
        if sid not in TARGETS:
            continue
        entry = {
            'shot_id': sid,
            'opening_source': s.get('opening_source'),
            'source_shot_id': s.get('source_shot_id'),
            'link_mode': s.get('link_mode'),
            'video_reference_asset_id': s.get('video_reference_asset_id'),
            'video_end_source_version': s.get('video_end_source_version'),
            'final_video': s.get('final_video'),
            'first_frame': s.get('first_frame'),
            'video_model': s.get('video_model'),
            'description': s.get('description'),
            'negative_prompt': s.get('negative_prompt'),
            'scene_binding_version': s.get('scene_binding_version'),
            'scene_bindings': s.get('scene_bindings'),
            'video_versions': [],
            'image_batches_summary': [],
        }
        for vv in (s.get('video_versions') or []):
            entry['video_versions'].append({
                'version_id': vv.get('version_id'),
                'created_at': vv.get('created_at'),
                'model': vv.get('model') or (vv.get('request') or {}).get('model'),
                'status': vv.get('status'),
                'selected': vv.get('selected'),
                'input_visuals': vv.get('input_visuals'),
                'mode': vv.get('mode') or (vv.get('request') or {}).get('mode'),
                'prompt_head': (vv.get('prompt') or (vv.get('request') or {}).get('prompt') or '')[:200],
                'seed': vv.get('seed') or (vv.get('request') or {}).get('seed'),
                'seconds': vv.get('seconds') or (vv.get('request') or {}).get('seconds'),
                'generation_basis': vv.get('generation_basis'),
            })
        for b in (s.get('image_batches') or s.get('batches') or []):
            entry['image_batches_summary'].append({
                'batch_id': b.get('batch_id'),
                'created_at': b.get('created_at'),
                'kind': b.get('kind'),
                'generation_basis': b.get('generation_basis'),
                'selected_version': b.get('selected_version') or b.get('selected'),
            })
        out[sid] = entry

# 场景绑定与 Look（角色资产）
out['_scenes'] = [
    {k: sc.get(k) for k in ('scene_id', 'name', 'description') if sc.get(k) is not None}
    for sc in P.get('scenes', [])]
out['_characters'] = [
    {'character_id': c.get('character_id'), 'name': c.get('name'),
     'looks': [{'look_id': l.get('look_id'), 'status': l.get('status'),
                'label': l.get('label') or l.get('name'),
                'created_at': l.get('created_at')}
               for l in (c.get('looks') or [])]}
    for c in (P.get('characters') or [])]

with open('_tmp/p42_binding_audit.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print('written', len(json.dumps(out)), 'bytes')
