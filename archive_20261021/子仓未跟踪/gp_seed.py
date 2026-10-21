# -*- coding: utf-8 -*-
"""AI-7C-H Golden Path 项目 seed（一次性，临时脚本勿提交）。
创建 AGNES_GoldenPath_H：2 chars / 2 scenes / 2 shots（均带旧视频资产）/ approved plans。
前置条件满足 §29：>=2 Character，>=1 有 done 三视图（seed 后用 generate-chain API 真生成），
多 Scene，现有 Shot，>=1 已生成视频（复制自 __gated_7c_e2e），compose 路径有效。
"""
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.utils.project_manager import ProjectManager
from src.core.models import Project, Scene, Shot, Character, StyleAnchor, Asset
from src.core.store import ProjectStore
from src.ai.production_planner import sanitize_plan
from routers.production_planner import _read_plans, _write_plans

PNAME = "AGNES_GoldenPath_H"
SRC = Path("projects/__gated_7c_e2e/output")


def seed():
    pm = ProjectManager(base_dir=str(Path(__file__).resolve().parent / "projects"))
    shutil.rmtree(pm.base_dir / PNAME, ignore_errors=True)
    pdir = pm.create_project(PNAME)

    flame = "赤焰守卫"
    pilot = "翼驾驶员"
    proj = Project(
        name=PNAME,
        style=StyleAnchor(art_style="anime, cinematic", aspect_ratio="16:9",
                          size_tier="1K"),
        story_text="赤焰守卫穿越荒原抵达前线基地；翼驾驶员在控制室接收信号，"
                   "两人的命运在机库第一次交汇。",
        characters=[
            Character(name=flame,
                      description_en="a flame guardian with red spiky hair and "
                                     "crimson armor, glowing ember eyes"),
            Character(name=pilot,
                      description_en="a calm pilot wearing a silver flight suit"),
        ],
        scenes=[
            Scene(scene_id="s01", summary="赤焰守卫第一次进入机库",
                  characters=[flame],
                  shots=[Shot(shot_id="s01_c01", scene_id="s01", index=1,
                              description="the flame guardian enters the vast "
                                          "hangar, footsteps echoing",
                              characters=[flame], target_duration_s=5.0,
                              link_mode="i2v", opening_source="independent")]),
            Scene(scene_id="s02", summary="翼驾驶员在控制室监控",
                  characters=[pilot],
                  shots=[Shot(shot_id="s02_c01", scene_id="s02", index=1,
                              description="the pilot monitors screens in the "
                                          "control room",
                              characters=[pilot], target_duration_s=5.0,
                              link_mode="i2v", opening_source="independent")]),
        ])
    ProjectStore(pdir).save(proj)

    # ---- 旧视频/帧资产：两个 shot 各复制一份（模拟"已有生产"）----
    out = pdir / "output"
    (out / "videos").mkdir(parents=True, exist_ok=True)
    (out / "frames").mkdir(parents=True, exist_ok=True)
    now = time.time()
    for sid in ("s01_c01", "s02_c01"):
        shutil.copy2(SRC / "videos/s01_c01.mp4", out / "videos" / f"{sid}.mp4")
        for f in ("s01_c01_first_v1.png", "s01_c01_video_end.png"):
            shutil.copy2(SRC / "frames" / f,
                         out / "frames" / f.replace("s01_c01", sid))
    # 更新 shot 资产状态（first_frame done + video done + final_video）
    store = ProjectStore(pdir)
    p = store.load()
    for sh in [p.scenes[0].shots[0], p.scenes[1].shots[0]]:
        sid = sh.shot_id
        sh.first_frame = {
            "candidates": [{"local": f"projects/{PNAME}/output/frames/{sid}_first_v1.png",
                            "url": "https://legacy/first.png", "status": "done",
                            "error": None, "updated_at": now}],
            "selected_index": 0, "status": "done", "error": None, "updated_at": now}
        sh.video = {"local": f"projects/{PNAME}/output/videos/{sid}.mp4",
                    "url": "https://legacy/video.mp4", "status": "done",
                    "error": None, "updated_at": now,
                    "num_frames": 121, "frame_rate": 24, "attempts": 1}
        sh.final_video = "legacy_video"
    store.save(p)

    # ---- approved production plans（两 scene）----
    plans = _read_plans(pdir)
    for sc in p.scenes:
        ai = {"overview": "seed", "shots": [
            {"shot_id": sh.shot_id, "opening_source": "independent",
             "link_mode": "i2v", "reason": "seed"} for sh in sc.shots]}
        plan = sanitize_plan(sc, ai, run_seed=42, project_name=PNAME)
        plan.status = "approved"
        plan.approved_at = time.time()
        plans[sc.scene_id] = plan
    _write_plans(pdir, plans)

    print(f"SEEDED {PNAME}")
    print(json.dumps({"chars": [c.name for c in p.characters],
                      "scenes": [sc.scene_id for sc in p.scenes],
                      "shots": [sh.shot_id for sc in p.scenes for sh in sc.shots],
                      "videos": [str(x.name) for x in (out / 'videos').glob('*.mp4')]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    seed()
