# -*- coding: utf-8 -*-
"""核验分离实验交付物：时长/响度/逐场景能量存活（一手结论，不转述）。"""
import subprocess
import re
from pathlib import Path
import numpy as np

FFDIR = Path(r"C:\Users\曹文淇\Downloads\ffmpeg-2026-01-07-git-af6a1dd0b2-full_build\bin")
FF = str(FFDIR / "ffmpeg.exe")
FP = str(FFDIR / "ffprobe.exe")

D = r"c:\Users\曹文淇\Downloads\output_rainlamp_separation"
ORIG = (r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard\projects\雨灯归航"
        r"\output\sequences\seq_a3d5b19b\srender_aca99c81.mp4")
files = {
    "orig": ORIG,
    "keep": D + "\\雨灯归航_保留轨_环境声与音效_48k_stereo.wav",
    "remove": D + "\\雨灯归航_去除轨_配乐及残留_48k_stereo.wav",
    "sep_mp4": D + "\\雨灯归航_分离版.mp4",
    "cut_mp4": D + "\\雨灯归航_剪辑版.mp4",
}
for k, f in files.items():
    r = subprocess.run([FP, "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", f], capture_output=True, text=True)
    print(f"{k}: {r.stdout.strip()} s")
print()
for k in ("orig", "keep", "remove"):
    f = files[k]
    r = subprocess.run([FF, "-hide_banner", "-nostats", "-i", f,
                        "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True)
    err = r.stderr.decode("utf-8", "replace")
    m = re.search(r"Integrated loudness:\s*\n\s*I:\s*(-?[\d.]+)\s*LUFS", err)
    i = m.group(1) if m else "?"
    print(f"{k}: I={i} LUFS")
print()


def rms_db(path, t0, dur):
    r = subprocess.run([FF, "-hide_banner", "-loglevel", "error",
                        "-ss", str(t0), "-t", str(dur), "-i", path,
                        "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                       capture_output=True)
    x = np.frombuffer(r.stdout, dtype=np.float32)
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


scenes = [("s01_riverside", 0, 39.5), ("s02_workshop", 39.5, 18.4),
          ("s03_tower", 57.9, 32.0)]
for name, t0, dur in scenes:
    o = rms_db(files["orig"], t0, dur)
    k = rms_db(files["keep"], t0, dur)
    print(f"{name}: orig_rms={o:.1f}dB keep_rms={k:.1f}dB delta={k - o:+.1f}dB")

