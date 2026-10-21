"""Phase 2 真机验收 — 种子项目。

创建全新安全测试项目 __producer_phase2_smoke（不动正式项目），写入受控 canonical：
4 场景 / 2 角色 / s01-s03 各有镜头、s04 空（供 Director 添加或 SW 改后半段）。
让 Producer 三案例都有真实可读、可改的项目状态。
"""
import sys
sys.path.insert(0, ".")
from src.core.models import Project, Scene, Shot, Character, StyleAnchor
from src.core.store import ProjectStore

PROJ = "__producer_phase2_smoke"


def _shots(scene_id, n, base_desc):
    return [Shot(shot_id=f"{scene_id}_c{i:02d}", scene_id=scene_id, index=i,
                 description=f"{base_desc}（第{i}镜）",
                 characters=["林小雨"],
                 shot_size="medium shot", target_duration_s=4)
            for i in range(1, n + 1)]


def build():
    s01 = Scene(scene_id="s01", summary="林小雨在雨夜推开咖啡馆的门，心情低落。",
                characters=["林小雨"], shots=_shots("s01", 2, "林小雨走进咖啡馆"))
    s02 = Scene(scene_id="s02", summary="她靠窗坐下，陈默沉默地坐在对面。",
                characters=["林小雨", "陈默"],
                shots=_shots("s02", 2, "两人对坐"))
    s03 = Scene(scene_id="s03", summary="窗外雨声渐大，两人回忆起往事。",
                characters=["林小雨", "陈默"],
                shots=_shots("s03", 2, "回忆闪回"))
    s04 = Scene(scene_id="s04", summary="雨停了，林小雨起身离开，故事在沉默中结束。",
                characters=["林小雨"], shots=[])
    proj = Project(
        name=PROJ, style=StyleAnchor(),
        story_text=(
            "短片《雨夜咖啡馆》。\n\n"
            "第一幕：雨夜，林小雨推开咖啡馆的门，心情低落，靠窗坐下。陈默沉默地坐在对面。"
            "窗外雨声渐大，两人回忆起往事。\n\n"
            "第二幕：雨停了，林小雨起身离开，故事在沉默中结束。目前结尾略仓促，"
            "人物动机不够清晰——林小雨为什么离开？陈默的沉默意味着什么？后半段节奏偏快。"
        ),
        characters=[
            Character(name="林小雨",
                      description_en="a young woman in a red coat, tired eyes"),
            Character(name="陈默",
                      description_en="a tall man with glasses, quiet demeanor"),
        ],
        scenes=[s01, s02, s03, s04], next_scene_seq=5)
    return proj


if __name__ == "__main__":
    import os
    base = f"projects/{PROJ}"
    os.makedirs(f"{base}/output", exist_ok=True)
    ProjectStore(base).save(build())
    print(f"seeded project '{PROJ}' -> {base}/output/project.json")
    p = ProjectStore(base).load()
    print(f"  scenes={len(p.scenes)} shots={sum(len(s.shots or []) for s in p.scenes)} "
          f"chars={len(p.characters)} story_len={len(p.story_text)}")
