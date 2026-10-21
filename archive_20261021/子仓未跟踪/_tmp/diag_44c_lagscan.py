# 滞后扫描：AAC 输出中 nc02 到底在不在、在哪个时间点
import subprocess
from pathlib import Path
import numpy as np
BASE = Path('.').resolve()
PDIR = BASE / 'projects' / '雨灯归航'
RATE = 8000

def decode(path, t0, dur):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                        "-ss", str(t0), "-t", str(dur), "-i", path,
                        "-vn", "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"],
                       capture_output=True, timeout=300)
    return np.frombuffer(r.stdout, dtype=np.float32)

def norm(x):
    x = x - x.mean(); s = x.std()
    return x / s if s > 1e-9 else x

def best_lag(film, stem, span_s=60):
    """在 ±span_s 内找成片与 stem 的最大相关滞后。"""
    best = (0.0, -1)
    for lag in range(-span_s*4, span_s*4+1):  # 0.25s 步进
        t0 = lag * 0.25
        seg = film
        # film 是全长；直接用切片索引
        i0 = int((t0) * RATE)
        if i0 < 0: continue
        a = film[i0:i0+len(stem)]
        if len(a) < len(stem) // 2: continue
        m = min(len(a), len(stem))
        c = float(np.dot(norm(a[:m]), norm(stem[:m])) / m)
        if c > best[1]:
            best = (t0, c)
    return best

aac = BASE / '_tmp/mx_aac.m4a'
pcm = BASE / '_tmp/mx_base1.wav'
n2 = PDIR / 'output/audio_imports/narration/nc02__nver_abc9c584.wav'

# 流元数据
for f in (aac, pcm):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                        "-show_entries", "stream=codec_name,start_time,duration,nb_frames",
                        "-of", "json", str(f)], capture_output=True, text=True)
    print(f.name, r.stdout.strip().replace('\n', ' '))

film = decode(aac, 0, 120)
stem = decode(n2, 0, 3.355)
t, c = best_lag(film, stem)
print(f"\nnc02 在 AAC 输出中的最佳位置: t={t:+.2f}s corr={c:+.3f}（原始位置 34.86s）")

# nc01 对照
n1 = PDIR / 'output/audio_imports/narration/nc01__nver_64272666.wav'
stem1 = decode(n1, 0, 3.402)
t1, c1 = best_lag(film, stem1, span_s=10)
print(f"nc01 在 AAC 输出中的最佳位置: t={t1:+.2f}s corr={c1:+.3f}（原始位置 1.5s）")
