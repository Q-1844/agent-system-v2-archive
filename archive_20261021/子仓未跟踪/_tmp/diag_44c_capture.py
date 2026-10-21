# 插桩：捕获 execute_render 实际执行的 ffmpeg 命令，与复现图 diff
import sys, json
from pathlib import Path
BASE = Path('.').resolve()
sys.path.insert(0, str(BASE))
PDIR = BASE / 'projects' / '雨灯归航'
SID = 'seq_a3d5b19b'

import deps, yaml
import routers.sequences
from src.core.rate_limiter import RateLimiter
from src.core.quota import QuotaLedger
cfg = yaml.safe_load((BASE / 'config' / 'config.yaml').read_text(encoding='utf-8')) or {}
RateLimiter.get((cfg.get('agnes') or {}).get('rpm'))
QuotaLedger.get_default(BASE / 'cache' / 'quota.json', limits=cfg.get('quota'))
if deps.project_manager is None:
    from src.pipeline.controller import PipelineController
    deps.pipeline_controller = PipelineController(str(BASE / 'config' / 'config.yaml'))
    deps.agnes_client = deps.pipeline_controller.agnes_client
    deps.project_manager = deps.pipeline_controller.project_manager

# 插桩捕获
import src.sequence.media_ops as mo
captured = []
_orig_run = mo._run
def spy_run(cmd, timeout=None):
    captured.append(list(cmd))
    return _orig_run(cmd, timeout=timeout)
mo._run = spy_run
import src.sequence.service as svc_mod
svc_mod._run_ffmpeg = spy_run  # execute_render 里 from .media_ops import _run as _run_ffmpeg

from src.sequence.service import SequenceService
svc = SequenceService(PDIR, '雨灯归航')

rv = svc.create_render(SID)
print(f"[render] {rv.version_id}")
prep = svc.prepare_render(SID, rv.version_id)
print(f"[prep] has_layers={prep.has_layers} n_audio={len(prep.resolved_audio)}")
print(f"[prep] plan layers: {[(l.layer_id, l.role, l.start_ms) for l in prep.audio_plan.layers]}")
print(f"[prep] ducking={prep.audio_plan.ducking.semantic_snapshot() if prep.audio_plan.ducking else None}")

svc.execute_render(SID, rv.version_id, prep)
svc.commit_render(SID, rv.version_id)

print(f"\n[captured] {len(captured)} 条 ffmpeg 命令")
for i, cmd in enumerate(captured):
    if "-filter_complex" in cmd:
        fc = cmd[cmd.index("-filter_complex") + 1]
        print(f"\n=== cmd[{i}] filter_complex ===")
        for seg in fc.split(';'):
            print("  ", seg)
        print("inputs:", [cmd[j+1] for j, a in enumerate(cmd) if a == "-i"])
        print("full out args tail:", cmd[cmd.index("-filter_complex")+2:])

# 与 get_audio_plan 的层对比（排查 plan_for vs get_audio_plan 差异）
plan2 = svc.get_audio_plan(SID)
print(f"\n[cmp] get_audio_plan layers: {[(l.layer_id, l.role, l.start_ms) for l in plan2.layers]}")
print(f"[cmp] plan_for revision={svc.audio_store.plan_for(SID).revision} "
      f"get_audio_plan revision={plan2.revision}")
p1 = svc.audio_store.plan_for(SID)
print(f"[cmp] layer 相等: {[ (a.layer_id, a.start_ms, a.duration_ms, a.gain_db) for a in p1.layers ] == [ (b.layer_id, b.start_ms, b.duration_ms, b.gain_db) for b in plan2.layers ]}")
print(f"[cmp] ducking 相等: {p1.ducking.semantic_snapshot() == plan2.ducking.semantic_snapshot()}")
