# 变体测试：找出 amix+延迟层+aac 丢音的精确触发条件
import subprocess
from pathlib import Path
import numpy as np
BASE = Path('.').resolve()
PDIR = BASE / 'projects' / '雨灯归航'
SID = 'seq_a3d5b19b'
RATE = 16000

base = PDIR / f'output/sequences/{SID}/srender_aca99c81.mp4'
music = PDIR / 'output/audio_imports/music/bgm_44c_v2.wav'
n2 = PDIR / 'output/audio_imports/narration/nc02__nver_abc9c584.wav'

def decode(path, t0, dur):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                        "-ss", str(t0), "-t", str(dur), "-i", path,
                        "-vn", "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"],
                       capture_output=True, timeout=300)
    return np.frombuffer(r.stdout, dtype=np.float32)

def norm(x):
    x = x - x.mean(); s = x.std()
    return x / s if s > 1e-9 else x

def nc02_corr(path):
    a = decode(path, 34.859, 3.355); b = decode(n2, 0, 3.355)
    m = min(len(a), len(b))
    if m == 0: return 0.0
    return float(np.dot(norm(a[:m]), norm(b[:m])) / m)

def run(name, inputs, fc, dst):
    cmd = (["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
           + inputs + ["-filter_complex", fc, "-map", "[out]",
                       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                       "-map_metadata", "-1", str(dst)])
    pr = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if pr.returncode:
        print(f"{name}: rc={pr.returncode} {pr.stderr[-250:]}"); return
    c = nc02_corr(dst)
    print(f"{name}: nc02 corr={c:+.3f} → {'✓' if c > 0.3 else '✗'}")

# V1: 3 输入 amix（base + 单句旁白@34.9s），无音乐
fc_v1 = ("[1:a]atrim=0:3.355,asetpts=PTS-STARTPTS,volume=6dB,adelay=delays=34859:all=1[l2];"
         "[0:a]volume=-60dB[b0];"
         "[b0][l2]amix=inputs=2:duration=first:normalize=0[out]")
run("V1 base+单句(2输入)", ["-i", str(base), "-i", str(n2)], fc_v1, BASE / '_tmp/vv_v1.m4a')

# V2: 3 输入 amix（music + 单句），无 base
fc_v2 = ("[1:a]atrim=0:3.355,asetpts=PTS-STARTPTS,volume=6dB,adelay=delays=34859:all=1[l2];"
         "[0:a]atrim=0:89.9,volume=-16.5dB[l1];"
         "[l1][l2]amix=inputs=2:duration=first:normalize=0[out]")
run("V2 music+单句(2输入)", ["-i", str(music), "-i", str(n2)], fc_v2, BASE / '_tmp/vv_v2.m4a')

# V3: 同 V2 但用 apad+atrim 替代 adelay（先铺静音再叠加 amix duration=longest）
fc_v3 = ("[1:a]atrim=0:3.355,asetpts=PTS-STARTPTS,volume=6dB,apad=whole_dur=34.859,"
         "atrim=0:38.214,asetpts=PTS-STARTPTS[l2];"
         "[0:a]atrim=0:89.9,volume=-16.5dB[l1];"
         "[l1][l2]amix=inputs=2:duration=longest:normalize=0[out]")
run("V3 apad替代adelay", ["-i", str(music), "-i", str(n2)], fc_v3, BASE / '_tmp/vv_v3.m4a')

# V4: adelay 但 amix 前 asetnsamples=1024（模拟 aac 帧粒度）
fc_v4 = ("[1:a]atrim=0:3.355,asetpts=PTS-STARTPTS,volume=6dB,adelay=delays=34859:all=1[l2];"
         "[0:a]atrim=0:89.9,volume=-16.5dB[l1];"
         "[l1][l2]amix=inputs=2:duration=first:normalize=0,asetnsamples=1024[out]")
run("V4 amix+asetnsamples=1024", ["-i", str(music), "-i", str(n2)], fc_v4, BASE / '_tmp/vv_v4.m4a')

# V5: adelay 小延迟（1.5s，模拟 nc01 成功情形）作对照
fc_v5 = fc_v2.replace("delays=34859", "delays=1500")
run("V5 music+单句@1.5s(对照)", ["-i", str(music), "-i", str(n2)], fc_v5, BASE / '_tmp/vv_v5.m4a')
