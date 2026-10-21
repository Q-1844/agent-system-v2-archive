# 矩阵实验：固定同一 FC，变化输出方式，并重复运行成功基线两次验证确定性
import sys, subprocess
from pathlib import Path
import numpy as np
BASE = Path('.').resolve()
PDIR = BASE / 'projects' / '雨灯归航'
SID = 'seq_a3d5b19b'
RATE = 16000

FC = ("[1:a]atrim=start=0.000000:end=89.902000,asetpts=PTS-STARTPTS,volume=-16.500000dB,"
      "afade=t=in:st=0:d=2.500000,afade=t=out:st=84.902000:d=5.000000,adelay=delays=0:all=1[l1];"
      "[2:a]atrim=start=0.000000:end=3.402000,asetpts=PTS-STARTPTS,volume=6.000000dB,"
      "afade=t=in:st=0:d=0.030000,afade=t=out:st=3.342000:d=0.060000,adelay=delays=1500:all=1[l2];"
      "[3:a]atrim=start=0.000000:end=3.355000,asetpts=PTS-STARTPTS,volume=6.000000dB,"
      "afade=t=in:st=0:d=0.030000,afade=t=out:st=3.295000:d=0.060000,adelay=delays=34859:all=1[l3];"
      "[4:a]atrim=start=0.000000:end=4.354000,asetpts=PTS-STARTPTS,volume=6.000000dB,"
      "afade=t=in:st=0:d=0.030000,afade=t=out:st=4.294000:d=0.060000,adelay=delays=47943:all=1[l4];"
      "[5:a]atrim=start=0.000000:end=3.030000,asetpts=PTS-STARTPTS,volume=6.000000dB,"
      "afade=t=in:st=0:d=0.030000,afade=t=out:st=2.970000:d=0.060000,adelay=delays=70722:all=1[l5];"
      "[6:a]atrim=start=0.000000:end=3.785000,asetpts=PTS-STARTPTS,volume=6.000000dB,"
      "afade=t=in:st=0:d=0.030000,afade=t=out:st=3.725000:d=0.060000,adelay=delays=83702:all=1[l6];"
      "[0:a]volume=-60.000000dB[b0];"
      "[l2]asplit=2[l2k][l2f];[l3]asplit=2[l3k][l3f];[l4]asplit=2[l4k][l4f];"
      "[l5]asplit=2[l5k][l5f];[l6]asplit=2[l6k][l6f];"
      "[l2k][l3k][l4k][l5k][l6k]amix=inputs=5:duration=longest:normalize=0[narrkey];"
      "[l1][narrkey]sidechaincompress=threshold=0.031622777:ratio=4.000000:attack=50:release=800[l1d];"
      "[b0][l1d][l2f][l3f][l4f][l5f][l6f]amix=inputs=7:duration=first:normalize=0[mixed];"
      "[mixed]loudnorm=I=-16.0:TP=-2.0:LRA=11.0,aresample=48000[final]")

base = PDIR / f'output/sequences/{SID}/srender_aca99c81.mp4'
music = PDIR / 'output/audio_imports/music/bgm_44c_v2.wav'
narr = [PDIR / f'output/audio_imports/narration/nc0{i}__nver_{h}.wav' for i, h in
        [(1,'64272666'), (2,'abc9c584'), (3,'c37a2a75'), (4,'2ce8f431'), (5,'fbfb97ee')]]
INPUTS = ["-i", str(music)] + sum([["-i", str(n)] for n in narr], [])
STARTS = [1.5, 34.859, 47.943, 70.722, 83.702]
DURS = [3.402, 3.355, 4.354, 3.030, 3.785]

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

def run(name, out_args, dst):
    cmd = (["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(base)]
           + INPUTS + ["-filter_complex", FC] + out_args + [str(dst)])
    pr = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if pr.returncode:
        print(f"{name}: rc={pr.returncode} {pr.stderr[-300:]}"); return
    print(f"{name}: {cue_check(dst)}")

# 成功基线重复两次（确定性检验）
for k in (1, 2):
    run(f"基线{k}(pcm/wav/无video)", ["-map", "[final]", "-c:a", "pcm_s16le",
        "-ar", "48000", "-ac", "2", "-map_metadata", "-1"], BASE / f'_tmp/mx_base{k}.wav')
# 基线 + aac（m4a 容器）
run("pcm→aac(m4a)", ["-map", "[final]", "-c:a", "aac", "-b:a", "192k",
    "-ar", "48000", "-ac", "2", "-map_metadata", "-1"], BASE / '_tmp/mx_aac.m4a')
# 基线 + wav 容器但 aac 编码（wav 可容纳 aac? 用 adts 换个方向：mp3）
run("pcm→libmp3lame(mp3)", ["-map", "[final]", "-c:a", "libmp3lame", "-b:a", "192k",
    "-ar", "48000", "-ac", "2", "-map_metadata", "-1"], BASE / '_tmp/mx_mp3.mp3')
# 基线但 flac（无损压缩容器）
run("flac", ["-map", "[final]", "-c:a", "flac",
    "-ar", "48000", "-ac", "2", "-map_metadata", "-1"], BASE / '_tmp/mx_flac.flac')
