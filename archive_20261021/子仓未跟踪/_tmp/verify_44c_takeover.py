# 接管复验：新成片 srender_9978e82a 中旁白是否真实在场（与分轨逐句做相关）
# 客观判据：在每句 cue 起始时间窗内，成片音频与该句旁白 stem 的 Pearson 相关
# 应显著高于与错位窗口（时间平移后）的相关 —— 即旁白真实混入而非巧合。
import subprocess, json
from pathlib import Path
import numpy as np

BASE = Path('.').resolve()
PDIR = BASE / 'projects' / '雨灯归航'
FILM = PDIR / 'output/sequences/seq_a3d5b19b/srender_9978e82a.mp4'
NARR_DIR = PDIR / 'output/audio_imports/narration'
AMB = PDIR / 'output/sequences/seq_a3d5b19b/srender_aca99c81.mp4'  # 原生环境声 base
RATE = 16000

def decode(path, t0, dur):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                        "-ss", str(t0), "-t", str(dur), "-i", path,
                        "-vn", "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"],
                       capture_output=True, timeout=300)
    return np.frombuffer(r.stdout, dtype=np.float32)

def norm(x):
    x = x - x.mean()
    s = x.std()
    return x / s if s > 1e-9 else x

def corr(a, b):
    n = min(len(a), len(b))
    return float(np.dot(norm(a[:n]), norm(b[:n])) / n)

# 从 plan 拿逐句 cue 与时长
import sys
sys.path.insert(0, str(BASE))
from src.sequence.service import SequenceService
svc = SequenceService(PDIR, '雨灯归航')
plan = svc.get_audio_plan('seq_a3d5b19b')
cues = sorted([l for l in plan.layers if l.role == 'narration'], key=lambda l: l.start_ms)

print(f"旁白 cue 数: {len(cues)}")
all_ok = True
for l in cues:
    # 找该 layer 的实际音频文件
    from src.sequence.audio_basis import resolve_audio_source
    src = resolve_audio_source(PDIR, l.layer_id, l.source)
    start = l.start_ms / 1000.0
    dur = (l.duration_ms or 4000) / 1000.0
    film_win = decode(FILM, start, dur)
    stem = decode(src.file, 0, dur)
    # 对齐窗相关（真实在场） vs 错位 3s 的相关（基线）
    shifted = decode(FILM, max(0, start - 3.0), dur)
    amb_win = decode(AMB, start, dur)
    c_true = corr(film_win, stem)
    c_shift = corr(shifted, stem)
    c_amb = corr(amb_win, stem)
    ok = c_true > 0.3 and c_true > max(c_shift, c_amb) * 2
    all_ok &= ok
    print(f"{l.layer_id}: 起始{start:6.1f}s 时长{dur:4.1f}s | 对齐相关={c_true:+.3f} "
          f"错位相关={c_shift:+.3f} 环境声相关={c_amb:+.3f} → {'✓ 旁白在场' if ok else '✗ 可疑'}")

# 音乐窗环境声残留（复核上一轮结论）
def band_hl(x):
    nfft = 8192; hop = nfft // 2
    frames = (len(x) - nfft) // hop
    if frames < 1: return 0.0
    spec = np.zeros(nfft // 2 + 1); win = np.hanning(nfft)
    for i in range(frames):
        spec += np.abs(np.fft.rfft(x[i*hop:i*hop+nfft] * win))**2
    freqs = np.fft.rfftfreq(nfft, 1/RATE)
    lo = (freqs>=100)&(freqs<2000); hi = (freqs>=4000)&(freqs<RATE/2)
    return float(np.sqrt(spec[hi].sum()/(spec[lo].sum()+1e-12)))

film_hl = band_hl(decode(FILM, 10, 5))
amb_hl = band_hl(decode(AMB, 10, 5))
print(f"\n音乐窗(10-15s) 高/低频能量比: 成片={film_hl:.4f} 环境声base={amb_hl:.4f} "
      f"→ {'✓ 无环境声泄漏' if film_hl < amb_hl*0.3 else '✗ 仍有残留'}")
print("\n总结:", "✅ 复验通过：旁白逐句在场、环境声无泄漏" if all_ok and film_hl < amb_hl*0.3 else "❌ 存在问题")
