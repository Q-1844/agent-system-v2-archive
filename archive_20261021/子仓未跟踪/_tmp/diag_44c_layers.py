# 诊断：打印 be64b193 plan 编译出的完整 ducking 图，并检查每层文件
import sys, subprocess
from pathlib import Path
BASE = Path('.').resolve()
sys.path.insert(0, str(BASE))
PDIR = BASE / 'projects' / '雨灯归航'

from src.sequence.service import SequenceService
from src.sequence.audio_mix import MixLayer, build_audio_mix_plan, compile_audio_filter_graph
from src.sequence.audio_basis import resolve_audio_source

svc = SequenceService(PDIR, '雨灯归航')
SID = 'seq_a3d5b19b'
plan = svc.get_audio_plan(SID)
print(f"plan revision={plan.revision} base_gain={plan.base_gain_db} layers={len(plan.layers)}")
for l in plan.layers:
    print(f"  {l.layer_id:12s} role={l.role:10s} start={l.start_ms:6d} dur={l.duration_ms:5d} "
          f"gain={l.gain_db:+.1f}dB src_in={l.source_in_ms}")

mix_layers = []
for l in plan.layers:
    r = resolve_audio_source(PDIR, l.layer_id, l.source)
    ok = Path(str(r.file)).exists() and Path(str(r.file)).stat().st_size > 0
    print(f"  layer {l.layer_id} -> {r.file} exists={ok}")
    mix_layers.append(MixLayer(layer_id=l.layer_id, role=l.role, source_file=str(r.file),
                               source_in_ms=l.source_in_ms, duration_ms=l.duration_ms,
                               start_ms=l.start_ms, gain_db=l.gain_db,
                               fade_in_ms=l.fade_in_ms, fade_out_ms=l.fade_out_ms))

base_file = PDIR / 'output' / 'sequences' / SID / 'srender_aca99c81.mp4'
mix = build_audio_mix_plan(str(base_file), 'srender_aca99c81', mix_layers,
                            base_gain_db=plan.base_gain_db,
                            ducking=plan.ducking.semantic_snapshot() if plan.ducking else None,
                            loudness=plan.loudness.semantic_snapshot() if plan.loudness else None)
g = compile_audio_filter_graph(mix)
print("\n=== 完整 filter_complex ===")
for seg in g['filter_complex'].split(';'):
    print(" ", seg)
print("\ninput_args:", g['input_args'])
