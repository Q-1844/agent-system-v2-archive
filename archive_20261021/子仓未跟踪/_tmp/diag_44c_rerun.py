# 决定性实验：直接执行编译图 → 逐句相关验证
import sys, subprocess
from pathlib import Path
import numpy as np
BASE = Path('.').resolve()
sys.path.insert(0, str(BASE))
PDIR = BASE / 'projects' / '雨灯归航'
RATE = 16000

from src.sequence.service import SequenceService
from src.sequence.audio_mix import MixLayer, build_audio_mix_plan, compile_audio_filter_graph
from src.sequence.audio_basis import resolve_audio_source

svc = SequenceService(PDIR, '雨灯归航')
plan = svc.get_audio_plan('seq_a3d5b19b')
mix_layers = [MixLayer(layer_id=l.layer_id, role=l.role,
                       source_file=str(resolve_audio_source(PDIR, l.layer_id, l.source).file),
                       source_in_ms=l.source_in_ms, duration_ms=l.duration_ms,
                       start_ms=l.start_ms, gain_db=l.gain_db,
                       fade_in_ms=l.fade_in_ms, fade_out_ms=l.fade_out_ms)
              for l in plan.layers]
base_file = PDIR / 'output/sequences/seq_a3d5b19b/srender_aca99c81.mp4'
mix = build_audio_mix_plan(str(base_file), 'srender_aca99c81', mix_layers,
                            base_gain_db=plan.base_gain_db,
                            ducking=plan.ducking.semantic_snapshot() if plan.ducking else None,
                            loudness=plan.loudness.semantic_snapshot() if plan.loudness else None)
g = compile_audio_filter_graph(mix)

out = BASE / '_tmp' / '_44c_graph_direct.wav'
cmd = (["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(base_file)]
       + g["input_args"] + ["-filter_complex", g["filter_complex"],
        "-map", "[final]", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2",
        "-map_metadata", "-1", str(out)])
pr = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
print("ffmpeg rc:", pr.returncode, pr.stderr[-400:] if pr.returncode else "OK")

def decode(path, t0, dur):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                        "-ss", str(t0), "-t", str(dur), "-i", path,
                        "-vn", "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"],
                       capture_output=True, timeout=300)
    return np.frombuffer(r.stdout, dtype=np.float32)

def norm(x):
    x = x - x.mean(); s = x.std()
    return x / s if s > 1e-9 else x

def corr(a, b):
    n = min(len(a), len(b))
    return float(np.dot(norm(a[:n]), norm(b[:n])) / n)

print("\n=== 直出图逐句旁白相关 ===")
for l in sorted([l for l in plan.layers if l.role == 'narration'], key=lambda x: x.start_ms):
    src = resolve_audio_source(PDIR, l.layer_id, l.source)
    start = l.start_ms / 1000.0
    dur = l.duration_ms / 1000.0
    c = corr(decode(out, start, dur), decode(src.file, 0, dur))
    print(f"{l.layer_id}: corr={c:+.3f} → {'✓ 在场' if c > 0.3 else '✗ 缺失'}")

# 对照：正式成片同窗口
film = PDIR / 'output/sequences/seq_a3d5b19b/srender_9978e82a.mp4'
print("\n=== 正式成片 srender_9978e82a 同窗口（对照） ===")
for l in sorted([l for l in plan.layers if l.role == 'narration'], key=lambda x: x.start_ms):
    src = resolve_audio_source(PDIR, l.layer_id, l.source)
    start = l.start_ms / 1000.0
    dur = l.duration_ms / 1000.0
    c = corr(decode(film, start, dur), decode(src.file, 0, dur))
    print(f"{l.layer_id}: corr={c:+.3f} → {'✓ 在场' if c > 0.3 else '✗ 缺失'}")
