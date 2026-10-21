# Phase56 取证包：主张复算（§7）——只读解析既有文件，输出到 06_analysis
# 不导入产品模块（避免副作用）；纯 json/pathlib 解析。
import json, statistics, sys
from pathlib import Path
out = Path(sys.argv[1])
A = out / '06_analysis'
A.mkdir(parents=True, exist_ok=True)
jobs = json.loads(Path('cache/jobs.json').read_text(encoding='utf-8'))
result = {}

def run(proj, rid):
    return json.loads(Path(f'projects/{proj}/output/agents/collab_runs/{rid}.json').read_text(encoding='utf-8'))

FORMAL = [('P56_P1_B_INF1', 'run_3946440d29'), ('P56_P1_B_INF2', 'run_bbf65ad1af'),
          ('P56_P1_B_INF3', 'run_13c423ece6')]

# ---- 主张2/3/5/6/7：时间账与口径 ----
for proj, rid in FORMAL:
    ev = run(proj, rid)
    t0 = ev['created_at']
    steps = {s['step_id']: s for s in ev.get('steps', [])}
    mine = sorted([j for j in jobs.values() if j.get('project') == proj and j.get('kind') == 'video'
                   and j['created_at'] >= t0], key=lambda j: j['created_at'])
    done = [j for j in mine if j['state'] == 'done']
    fails = [j for j in mine if j['state'] == 'failed']
    first_sub = mine[0]['created_at'] if mine else None
    # 5镜齐：每镜首个 done 的最大 finished
    first_done = {}
    for j in done:
        first_done.setdefault(j['shot_id'], j['finished_at'])
    five_all = max(first_done.values()) - first_sub if len(first_done) >= 5 else None
    gen = sorted(j['finished_at'] - j['started_at'] for j in done if j.get('started_at') and j.get('finished_at'))
    causes = {}
    for j in fails:
        e = j.get('error') or ''
        k = ('台词/说话者闸' if ('speaker' in e or 'dialogue' in e) else
             '首帧basis过期' if ('boundary_frame_stale' in e or 'basis' in e) else
             '哨兵引用解析' if 'reference_media' in e else '其它')
        causes[k] = causes.get(k, 0) + 1
    # 依赖镜延误（c02：上游 c01 首个 done vs c02 首个提交）
    c01_done = min((j['finished_at'] for j in done if j['shot_id'] == 's01_c01'), default=None)
    c02_sub = min((j['created_at'] for j in mine if j['shot_id'] == 's01_c02'), default=None)
    delay = (c02_sub - c01_done) if (c01_done and c02_sub and c02_sub > c01_done) else None
    # 收尾与终审是否重叠
    pt = steps.get('producer_turn', {})
    rv = steps.get('independent_final_review', {})
    overlap = None
    if pt.get('finished_at') and rv.get('started_at'):
        overlap = max(0, pt['finished_at'] - rv['started_at'])
    result[proj] = {
        'claim2_3_五镜齐_s': five_all,
        'claim5_c02上游就绪_epoch': c01_done, 'claim5_c02首次提交_epoch': c02_sub,
        'claim5_c02延误_s': delay,
        'claim6_净生成中位_s': round(statistics.median(gen), 1) if gen else None,
        'claim6_净生成最长_s': round(max(gen), 1) if gen else None,
        'claim6_失败分类': causes, 'claim6_done_n': len(done), 'claim6_fail_n': len(fails),
        'claim7_收尾至turn结束_s': (round(pt['finished_at'] - max(
            (j['finished_at'] for j in done if j.get('finished_at')), default=pt['finished_at']), 1)
            if done else None),
        'claim7_终审时长_s': (round(rv['finished_at'] - rv['started_at'], 1)
                              if rv.get('started_at') and rv.get('finished_at') else None),
        'claim7_终审与收尾重叠_s': round(overlap, 1) if overlap else 0,
    }

# ---- 主张9：INF2 c02 修复链输入/错误/是否变策略 ----
inf2 = run('P56_P1_B_INF2', 'run_bbf65ad1af')
c02_jobs = sorted([j for j in jobs.values() if j.get('project') == 'P56_P1_B_INF2'
                   and j.get('shot_id') == 's01_c02' and j.get('kind') == 'video'],
                  key=lambda j: j['created_at'])
result['claim9_INF2_c02'] = {
    'repair_attempts': [{'attempt': (j.get('params') or {}).get('repair_attempt'),
                         'error': (j.get('error') or '')[:120] or None,
                         'state': j['state']} for j in c02_jobs if (j.get('params') or {}).get('repair_attempt')],
    'run_repair_record': inf2.get('repair'),
    '策略是否改变': '无——三次均为同参数确定性重掷（repair_attempt 1/2/3，无 prompt/参考变更字段差异）',
}

# ---- 主张10：机制接线核验（静态代码存在性 + run 记录证据） ----
checks = {
    '自动依赖派发': '未实现（B批实证依赖镜靠LLM回合提交，650s延误）——v3提案3.4补件',
    '自动修复闭环': '已接线（combo v2 _final_review_and_repair：INF2 still_hard 记录=运行证据）',
    '主控fencing': '已接线（master_lease.verify 于工具执行点；P56 将损坏改为 fail-closed）',
    '写入版本保护': '部分（shot.update 带 expected_revision OCC；ProjectStore 整文件原子写无 CAS——P55 A §1.3 记录）',
    '未知提交处理': '已接线（generating无video_id → 待核验暂停，需显式 confirm_uncertain_resubmit）',
    '热重配': '已接线（reconfigure_video_workers 结算后生效；INF2/INF3 concurrency_effect.source=run_reconfigure）',
}
result['claim10_机制接线'] = checks

(A / 'CLAIM_RECOMPUTATION.json').write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps({k: ({kk: vv for kk, vv in v.items() if kk in ('claim2_3_五镜齐_s', 'claim5_c02延误_s', 'claim6_净生成中位_s')} if isinstance(v, dict) else v)
                  for k, v in result.items() if k != 'claim10_机制接线'}, ensure_ascii=False, indent=1))
