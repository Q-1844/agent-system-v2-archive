# -*- coding: utf-8 -*-
"""调试旁白 stem 的 amix 失败（临时脚本）。"""
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
t = json.loads((BASE / "_44c" / "cue_table.json").read_text(encoding="utf-8"))
inputs = []
fc = []
i = 1
for r in t["narration_cues"]:
    p = (BASE / "projects" / "雨灯归航" / "output" / r["file"])
    inputs += ["-i", str(p)]
    d = r["duration_ms"] / 1000
    fc.append(f"[{i}:a]atrim=start=0.000000:end={d:.6f},asetpts=PTS-STARTPTS,"
              f"volume=2.0dB,afade=t=in:st=0:d=0.03,"
              f"afade=t=out:st={d - 0.06:.3f}:d=0.06,"
              f"adelay=delays={r['start_ms']}:all=1[s{i}]")
    i += 1
fc.append("".join(f"[s{j}]" for j in range(1, i))
          + "amix=inputs=5:duration=longest:normalize=0[stem]")
out = BASE / "_tmp" / "_44c_stem_test.wav"
cmd = (["ffmpeg", "-hide_banner", "-y"] + inputs
       + ["-filter_complex", ";".join(fc), "-map", "[stem]",
          "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", str(out)])
pr = subprocess.run(cmd, capture_output=True, text=True)
print("rc:", pr.returncode)
print("stderr tail:", pr.stderr[-900:])
