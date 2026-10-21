# 最小定位：AAC 编码下，无 ducking 的纯 amix 是否也丢延迟层
import subprocess
from pathlib import Path
import numpy as np
BASE = Path('.').resolve()
PDIR = BASE / 'projects' / '雨灯归航'
SID = 'seq_a3d5b19b'
RATE = 16000

base = PDIR / f'output/sequences/{SID}/srender_aca99c81.mp4'
music = PDIR / 'output/audio_imports/music/bgm_44c_v2.wav'
narr = [PDIR / f'output/audio_imports/narration/nc0{i}__nver_{h}.wav' for i, h in
        [(1,'64272666'), (2,'abc9c584'), (3,'c37a2a75'), (4,'2ce8f431'), (5,'fbfb97ee')]]
STARTS = [1.5, 34.859, 47.943, 70.722, 83.702]
DURS = [3.402, 3.355, 4.354, 3.030, 3.785]
INPUTS = ["-i", str(music)] + sum([["-i", str(n)] for n in narr], [])

LAYERS = ";".join(
    f"[{i+2}:a]atrim=start=0.000000:end={DURS[i]:.6f},asetpts=PTS-STARTPTS,"
    f"volume=6.000000dB,adelay=delays={int(STARTS[i]*1000)}:all=1[l{i+2}]"
    for i in range(5))

def decode(path, t0, dur):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                        "-ss", str(t0), "-t", str(dur), "-i", path,
                        "-vn", "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"],
                       capture_output=True, timeout=300)
    return np.frombuffer(r.stdout, dtype=np.float32)

def norm(x):
    x = x - x.mean(); s = x.std()
    return x / s if s > 1e-9 else x

def cue_check(path):
    res = []
    for i, n in enumerate(narr):
        a = decode(path, STARTS[i], DURS[i]); b = decode(n, 0, DURS[i])
        m = min(len(a), len(b))
        if m == 0: res.append('?'); continue
        c = float(np.dot(norm(a[:m]), norm(b[:m])) / m)
        res.append(f"{c:+.2f}")
    return ' '.join(res)

def run(name, fc, dst):
    cmd = (["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(base)]
           + INPUTS + ["-filter_complex", fc, "-map", "[out]",
                       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                       "-map_metadata", "-1", str(dst)])
    pr = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if pr.returncode:
        print(f"{name}: rc={pr.returncode} {pr.stderr[-300:]}"); return
    print(f"{name}: {cue_check(dst)}")

# M1: 无 ducking —— base(-60) + music + 5 旁白直接 amix（duration=first）
fc_m1 = (f"[1:a]atrim=start=0:end=89.902,asetpts=PTS-STARTPTS,volume=-16.5dB,"
         f"adelay=delays=0:all=1[l1];{LAYERS};"
         f"[0:a]volume=-60.000000dB[b0];"
         f"[b0][l1][l2][l3][l4][l5][l6]amix=inputs=7:duration=first:normalize=0[out]")
run("M1 无ducking→aac", fc_m1, BASE / '_tmp/mm_m1.m4a')

# M2: 有 ducking（当前生产图）→ aac（复现对照）
fc_m2 = (f"[1:a]atrim=start=0:end=89.902,asetpts=PTS-STARTPTS,volume=-16.5dB,"
         f"adelay=delays=0:all=1[l1];{LAYERS};"
         f"[0:a]volume=-60.000000dB[b0];"
         f"[l2]asplit=2[l2k][l2f];[l3]asplit=2[l3k][l3f];[l4]asplit=2[l4k][l4f];"
         f"[l5]asplit=2[l5k][l5f];[l6]asplit=2[l6k][l6f];"
         f"[l2k][l3k][l4k][l5k][l6k]amix=inputs=5:duration=longest:normalize=0[narrkey];"
         f"[l1][narrkey]sidechaincompress=threshold=0.031622777:ratio=4.000000:attack=50:release=800[l1d];"
         f"[b0][l1d][l2f][l3f][l4f][l5f][l6f]amix=inputs=7:duration=first:normalize=0[out]")
run("M2 ducking→aac", fc_m2, BASE / '_tmp/mm_m2.m4a')

# M3: 无 ducking 但 duration=longest → aac
fc_m3 = fc_m1.replace("duration=first", "duration=longest")
run("M3 无ducking/longest→aac", fc_m3, BASE / '_tmp/mm_m3.m4a')
