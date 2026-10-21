# -*- coding: utf-8 -*-
"""42.md §三 全 13 镜锚定矩阵：最终视频的参考来源 + 被消费首帧批次的参考模式"""
import json

P = json.load(open('projects/雨灯归航/output/project.json', encoding='utf-8'))
rows = []
for sc in P.get('scenes', []):
    for s in sc.get('shots', []):
        sid = s['shot_id']
        fv = s.get('final_video')
        row = {'shot': sid, 'final': fv}
        # 最终版本的输入
        for vv in (s.get('video_versions') or []):
            if vv.get('version_id') == fv:
                iv = vv.get('input_visuals') or []
                row['video_inputs'] = [
                    (i.get('semantic_role'), i.get('source_type') or i.get('candidate_id', ''),
                     i.get('source_shot_id') or '') for i in iv]
                row['model'] = vv.get('model')
                row['pmode'] = (vv.get('generation_basis') or {}).get('provider_mode')
        # 被该版本消费的首帧（candidate batch -> 批次模式）
        consumed_batch = None
        for i in (row.get('video_inputs') or []):
            if i[1] and str(i[1]).startswith('ff_'):
                consumed_batch = str(i[1]).split('_')[1] if False else None
        # 直接找 batch_id
        for vv in (s.get('video_versions') or []):
            if vv.get('version_id') == fv:
                for i in (vv.get('input_visuals') or []):
                    bid = i.get('batch_id')
                    if bid:
                        for b in (s.get('first_frame_batches') or []):
                            if b.get('batch_id') == bid:
                                gb = b.get('generation_basis') or {}
                                row['ff_batch'] = bid
                                row['ff_scene_mode'] = gb.get('scene_reference_mode')
                                row['ff_human_mode'] = gb.get('human_reference_mode')
                                row['ff_sent'] = gb.get('sent_ref_sequence')
        rows.append(row)

with open('_tmp/p42_matrix.json', 'w', encoding='utf-8') as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)
for r in rows:
    print(r['shot'], '| model=', (r.get('model') or '')[:22], '| pmode=', r.get('pmode'),
          '| ff_batch=', r.get('ff_batch'), 'scene=', r.get('ff_scene_mode'), 'human=', r.get('ff_human_mode'),
          '| sent=', r.get('ff_sent'),
          '| vin=', [(i[1], i[2]) for i in (r.get('video_inputs') or [])])
