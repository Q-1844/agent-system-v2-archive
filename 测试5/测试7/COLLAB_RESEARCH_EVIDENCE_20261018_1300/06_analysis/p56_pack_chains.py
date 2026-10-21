# Phase56 取证包：规范化时间线 + 最小请求链（只读，输出到证据目录）
import json, sys
from pathlib import Path
out = Path(sys.argv[1])
DEST = out / '04_runtime_evidence'
jobs = json.loads(Path('cache/jobs.json').read_text(encoding='utf-8'))

FORMAL = [('P56_P1_B_INF1', 'run_3946440d29'), ('P56_P1_B_INF2', 'run_bbf65ad1af'),
          ('P56_P1_B_INF3', 'run_13c423ece6'), ('P56_P2_C_COMBO', 'run_b405aea5db')]

# ---------- 6.2 规范化时间线 ----------
for proj, rid in FORMAL:
    run = json.loads(Path(f'projects/{proj}/output/agents/collab_runs/{rid}.json').read_text(encoding='utf-8'))
    t0 = run['created_at']
    lines = []
    for s in (run.get('steps') or []):
        lines.append({'event': 'run_step', 'run_id': rid, 'project': proj,
                      'step_id': s['step_id'], 'status': s['status'],
                      't_start_epoch': s.get('started_at'), 't_end_epoch': s.get('finished_at'),
                      'derived_dur_s': (round(s['finished_at'] - s['started_at'], 3)
                                        if s.get('started_at') and s.get('finished_at') else None),
                      'detail_keys': sorted((s.get('detail') or {}).keys())})
    for j in jobs.values():
        if j.get('project') == proj and j['created_at'] >= t0 and j.get('kind') == 'video':
            lines.append({'event': 'video_job', 'run_id': rid, 'project': proj,
                          'job_id': j['job_id'], 'shot_id': j.get('shot_id'), 'state': j['state'],
                          't_created_epoch': j['created_at'], 't_started_epoch': j.get('started_at'),
                          't_finished_epoch': j.get('finished_at'),
                          'provider_task_id': (j.get('params') or {}).get('provider_task_id'),
                          'repair_of_review': (j.get('params') or {}).get('repair_of_review'),
                          'repair_attempt': (j.get('params') or {}).get('repair_attempt'),
                          'origin_run_id': (j.get('params') or {}).get('origin_run_id'),
                          'error_class_stage': [j.get('error_class'), j.get('error_stage')],
                          'error': (j.get('error') or '')[:200] or None})
    lines.sort(key=lambda x: min(v for v in x.values() if isinstance(v, (int, float))) if any(
        isinstance(v, (int, float)) for v in x.values()) else 0)
    (DEST / f'timeline_{proj}_{rid}.jsonl').write_text(
        '\n'.join(json.dumps(l, ensure_ascii=False) for l in lines), encoding='utf-8')

# ---------- 6.1 run 索引 ----------
index = []
for proj, rid in FORMAL + [('P56_P1_B_INF1', 'run_fba9de2066__v1discovery'),
                            ('P56_P2_C_COMBO', 'run_11330c0c3f__interrupted')]:
    real_rid = rid.replace('__v1discovery', '').replace('__interrupted', '')
    fn = Path(f'projects/{proj}/output/agents/collab_runs/{real_rid}.json')
    src = fn if fn.exists() else DEST / f'run_record_{proj}_{rid}.json'
    d = json.loads(src.read_text(encoding='utf-8'))
    index.append({'project': proj, 'run_id': d['run_id'],
                  'mode': str(d.get('mode_id')) + ' v' + str(d.get('mode_version')),
                  'capacity_effect': d.get('concurrency_effect'), 'status': d.get('status'),
                  'version_label': ('v1政策发现样本' if 'v1discovery' in rid else
                                    '中断后由后端继续完成' if 'interrupted' in rid else
                                    'v2.1正式对照' if 'INF' in proj else 'P2组合臂'),
                  'created': d.get('created_at'), 'finished': d.get('finished_at'),
                  'review_hard': (d.get('review') or {}).get('hard_error_shots'),
                  'repair_still_hard': (d.get('repair') or {}).get('still_hard'),
                  'user_feedback': '未反馈（B/C批成片待用户看片）'})
(out / '04_runtime_evidence' / 'RUN_INDEX.json').write_text(
    json.dumps(index, ensure_ascii=False, indent=1), encoding='utf-8')

# ---------- 6.3 最小请求链 ----------
chains_dir = DEST / 'chains'
chains_dir.mkdir(exist_ok=True)

def shot_jobs(proj, sid, since):
    return sorted([j for j in jobs.values() if j.get('project') == proj and j.get('shot_id') == sid
                   and j.get('kind') == 'video' and j['created_at'] >= since],
                  key=lambda j: j['created_at'])

def review_entry(proj, batch, sid):
    p = Path(f'projects/{proj}/output/agents/review_pipeline/{batch}.json')
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding='utf-8'))
    return next((r for r in d.get('results', []) if r.get('shot_id') == sid), None)

def build_chain(name, proj, rid, sid, narrative, opening_note=None):
    run = json.loads(Path(f'projects/{proj}/output/agents/collab_runs/{rid}.json').read_text(encoding='utf-8'))
    t0 = run['created_at']
    js = []
    for j in shot_jobs(proj, sid, t0):
        js.append({'job_id': j['job_id'], 'state': j['state'],
                   'params_keys': sorted((j.get('params') or {}).keys()),
                   'input_manifest': (j.get('params') or {}).get('input_manifest'),
                   'provider_task_id': (j.get('params') or {}).get('provider_task_id'),
                   'error': (j.get('error') or '')[:300] or None,
                   'message_tail': (j.get('message') or '')[:120],
                   't_created': j['created_at'], 't_started': j.get('started_at'),
                   't_finished': j.get('finished_at'),
                   'note_provider_url': '私有媒体URL不打包——版本与哈希见 project.json 对应 shot.video_versions（version_id 索引）'})
    rv = run.get('review') or {}
    rev = review_entry(proj, rv.get('batch_id'), sid) if rv.get('batch_id') else None
    chain = {'chain': name, 'project': proj, 'run_id': rid, 'shot_id': sid,
             'narrative': narrative, 'opening_note': opening_note,
             'video_jobs': js, 'final_review_entry': rev,
             'version_receipt_location': ('projects/' + proj + '/output/project.json -> scenes[].shots[shot_id='
                                          + sid + '].video_versions / final_video（正册未内嵌，按此索引）'),
             'input_manifest_note': 'job.params 内嵌若存在；版本级 manifest 见 project.json video_versions[].generation_basis.input_manifest'}
    (chains_dir / (name + '.json')).write_text(json.dumps(chain, ensure_ascii=False, indent=1), encoding='utf-8')
    return len(js)

n1 = build_chain('chain_A_成功独立镜头_INF3_s01_c05', 'P56_P1_B_INF3', 'run_13c423ece6', 's01_c05',
                 '独立镜（无上游媒体依赖）；含一次提交前闸门拒绝后修正的完整路径')
n2 = build_chain('chain_B_依赖镜延误_INF3_s01_c02', 'P56_P1_B_INF3', 'run_13c423ece6', 's01_c02',
                 'multi+prev_tail_look_scene 三参考真实媒体硬依赖；B批报告§1的650s延误案例——上游c01于+224s收货，本镜+875s才提交（LLM忙于重试波次）',
                 opening_note='multi + video_reference_asset_id=prev_tail_look_scene（三参考接力——真实媒体硬依赖）')
n3 = build_chain('chain_C_预检拒绝后修正_INF3_s01_c03', 'P56_P1_B_INF3', 'run_13c423ece6', 's01_c03',
                 '提交前闸门拒绝（台词/说话者类）→原始错误码在 video_jobs[].error →修正后成功提交')
n4 = build_chain('chain_D_身份硬错修复耗尽_INF2_s01_c02', 'P56_P1_B_INF2', 'run_bbf65ad1af', 's01_c02',
                 '确定性修复3次全败（identity类硬错）→still_hard如实保留；run内repair.attempts含每attempt复审结论')
print('chains built:', n1, n2, n3, n4)
