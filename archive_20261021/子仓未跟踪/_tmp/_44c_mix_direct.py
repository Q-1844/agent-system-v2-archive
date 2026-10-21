# -*- coding: utf-8 -*-
"""调试：混音图直出 WAV（绕过 AAC），定位峰值超限层级（临时脚本）。"""
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
PDIR = BASE / "projects" / "雨灯归航"

from src.sequence.service import SequenceService

svc = SequenceService(PDIR, "雨灯归航")
SEQ = "seq_a3d5b19b"
entry = svc.get_entry(SEQ)
plan = svc.get_audio_plan(SEQ)
done = [r for r in entry.render_versions if r.status == "done"]
base_rv = next(r for r in reversed(done) if r.base_render_version_id)
base_file = PDIR / "output" / "sequences" / SEQ / f"{base_rv.base_render_version_id}.mp4"

from src.sequence.audio_mix import (MixLayer, build_audio_mix_plan,
                                    compile_audio_filter_graph)
from src.sequence.audio_basis import resolve_audio_source

mix_layers = [MixLayer(layer_id=l.layer_id, role=l.role,
                       source_file=str(resolve_audio_source(PDIR, l.layer_id, l.source).file),
                       source_in_ms=l.source_in_ms, duration_ms=l.duration_ms,
                       start_ms=l.start_ms, gain_db=l.gain_db,
                       fade_in_ms=l.fade_in_ms, fade_out_ms=l.fade_out_ms)
              for l in plan.layers]
mix = build_audio_mix_plan(
    str(base_file), base_rv.base_render_version_id, mix_layers,
    base_gain_db=plan.base_gain_db,
    ducking=plan.ducking.semantic_snapshot() if plan.ducking else None,
    loudness=plan.loudness.semantic_snapshot() if plan.loudness else None)
g = compile_audio_filter_graph(mix)

out = BASE / "_tmp" / "_44c_mix_direct.wav"
cmd = (["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(base_file)]
       + g["input_args"] + ["-filter_complex", g["filter_complex"]]
       + ["-map", "0:v", "-map", "[final]", "-c:a", "pcm_s16le", "-ar", "48000",
          "-map_metadata", "-1", "-an", str(out)])
# -an 不行（要音频）；改正确参数
cmd = (["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(base_file)]
       + g["input_args"] + ["-filter_complex", g["filter_complex"]]
       + ["-map", "[final]", "-c:a", "pcm_s16le", "-ar", "48000",
          "-map_metadata", "-1", str(out)])
subprocess.run(cmd, check=True, timeout=600)
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(out), "-af", "ebur128=peak=true",
                    "-f", "null", "-"], capture_output=True, text=True).stderr
for line in r.splitlines():
    if line.strip().startswith(("Peak:", "True peak:", "I:", "LRA:")):
        print(" ", line.strip())
# 分层诊断：单独测 music 层 duck 后峰值、narration 叠加段
print("layers:", [(l.layer_id, l.role, l.gain_db) for l in plan.layers])
