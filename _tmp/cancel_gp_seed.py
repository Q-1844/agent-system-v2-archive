# -*- coding: utf-8 -*-
"""AI-7C-H Cancel Hotfix 浏览器验收 seed（临时脚本，勿提交）。

场景 A（__cancel_gp_a）：2 chars / 2 scenes / 2 shots + approved 双角色 update_character
plan + committed E1（stage=character_sync）。backend 启动恢复会 kickoff 真实 char sync
（真实 Agnes view 生成），供「停止并重新规划」主场景取消。

场景 B（__cancel_gp_b）：1 char/1 scene + committed E1（手动推进 production_prepare +
关联 R1 + cancel_requested=true，模拟 stopping 中崩溃）+ R1 run.json（running +
cancel_requested=true）。供「正在停止 → backend restart → 页面恢复」场景。
"""
import asyncio
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.core.models import Project, Scene, Shot, Character, StyleAnchor
from src.core.store import ProjectStore
from src.agents.runtime import AgentRuntime
from src.agents.change_protocol import execution_service as cpx
from src.agents.change_protocol.store import ChangeProtocolStore
from src.agents.change_protocol.models import (UnifiedChangePlan, PlanPreviewArtifact,
                                                PlanApproval, ChangeSession)
from src.revision.models import ChangeOperation, BeforeAfter, creative_source_signature
from src.revision.changeset import preview_operations_on_project
from src.utils.project_manager import ProjectManager

BASE = Path(__file__).resolve().parent
PROJ_A = "__cancel_gp_a"
PROJ_B = "__cancel_gp_b"


class _NoCall:
    async def chat(self, *a, **k):
        raise AssertionError("seed 不应调 Agnes")


def _mk_proj(pname, chars, scenes):
    return Project(name=pname, style=StyleAnchor(art_style="anime, cinematic",
                                                 aspect_ratio="16:9", size_tier="1K"),
                   story_text="cancel hotfix golden path",
                   characters=chars, scenes=scenes)


def _shot(sid, scene_id, desc, chs):
    return Shot(shot_id=sid, scene_id=scene_id, index=1, description=desc,
                characters=chs, target_duration_s=4.0, link_mode="i2v",
                opening_source="independent")


async def seed(pname, chars, scenes, ops, sid, pid):
    pm = ProjectManager(BASE / "projects")
    pdir = BASE / "projects" / pname
    shutil.rmtree(pdir, ignore_errors=True)
    pdir = pm.create_project(pname)
    proj = _mk_proj(pname, chars, scenes)
    ProjectStore(pdir).save(proj)

    rt = AgentRuntime(project_dir_resolver=lambda name: BASE / "projects" / name,
                      settings_path=BASE / "projects" / pname / "agents_data" / "settings.json",
                      client=_NoCall())
    sig = creative_source_signature(proj.to_dict())
    store = ChangeProtocolStore(pdir, pname)
    now = time.time()
    store.save_session(ChangeSession(session_id=sid, project_name=pname,
                                      status="approved_for_execution",
                                      active_plan_id=pid, plan_version=1,
                                      source_snapshot_signature=sig, schema_version=2,
                                      created_at=now, updated_at=now))
    source = ProjectStore(pdir).load()
    candidate, _d, impact, _w = preview_operations_on_project(source, ops)
    projected = creative_source_signature(candidate.to_dict())
    plan = UnifiedChangePlan(plan_id=pid, change_session_id=sid, project_name=pname,
                             version=1, source_snapshot_signature=sig,
                             status="approved_for_execution",
                             steps=[{"step_id": "step_ch", "module": "character",
                                     "owner_agent_id": "character_designer",
                                     "plan_item_ids": [], "depends_on_step_ids": [],
                                     "parallel_group": None}],
                             preview_id=f"pv_{pid}", created_at=now)
    plan.approval = PlanApproval(plan_id=pid, plan_version=1, decision="approved",
                                 source_snapshot_signature=sig, decided_at=now).to_dict()
    store.save_plan(plan)
    store.save_preview(PlanPreviewArtifact(
        preview_id=f"pv_{pid}", change_session_id=sid, plan_id=pid, plan_version=1,
        source_snapshot_signature=sig,
        module_operations=[{"step_id": "step_ch", "module": "character",
                            "owner_agent_id": "character_designer",
                            "proposal_item_ids": [],
                            "operations": [o.to_dict() for o in ops]}],
        aggregate_impact=impact.to_dict(), projected_signature=projected,
        applyable=False, created_at=now))
    res = await cpx.start_replay_commit(rt, pname, sid, pid, 1, "affected_production")
    ex = res["execution"]
    assert ex["canonical_commit"]["status"] == "committed", ex
    return rt, store, ex["execution_id"]


def seed_b():
    # ---- 场景 B：stopping 中崩溃（E1 cancel_requested + owned R1 running + cancel_requested）----
    b1 = Character(name="AudC",
                   description_en="a quiet traveler with a grey coat")
    scenes_b = [
        Scene(scene_id="s01", summary="AudC waits", characters=["AudC"],
              shots=[_shot("s01_c01", "s01",
                           "AudC waits under the old clock tower", ["AudC"])]),
    ]
    ops_b = [ChangeOperation(op_type="update_character", character_name="AudC",
                             description_en=BeforeAfter(
                                 before="a quiet traveler with a grey coat",
                                 after="a quiet traveler with a dark leather jacket"))]
    rt_b, store_b, eid_b = asyncio.run(
        seed(PROJ_B, [b1], scenes_b, ops_b, "cs_cancel_b", "plan_cancel_b"))
    ex_b = store_b.get_execution(eid_b)
    ex_b.stage = "production_prepare"
    ex_b.production_run_id = "prun_cxl_b"
    ex_b.status = "running"
    ex_b.cancel_requested = True          # stopping 中崩溃
    store_b.save_execution(ex_b)
    # R1 run.json：running + cancel_requested（重启后 recover_runs -> cancelled）
    run_dir = BASE / "projects" / PROJ_B / "output" / "production_runs" / "prun_cxl_b"
    run_dir.mkdir(parents=True, exist_ok=True)
    now = time.time()
    (run_dir / "run.json").write_text(json.dumps({
        "run_id": "prun_cxl_b", "project_name": PROJ_B, "status": "running",
        "stage": "scenes", "respect_locked": True, "pause_requested": False,
        "cancel_requested": True, "current_scene_id": None, "current_child_run_id": None,
        "scenes": [], "source_signature": {}, "source_snapshot_file": None,
        "plans_snapshot_file": None, "composition_manifest_file": None,
        "final_output": None, "final_duration_s": None, "final_size_bytes": None,
        "error": None, "error_code": None, "target_scene_ids": ["s01"],
        "target_shot_ids": None, "shot_actions": None,
        "parent_change_execution_id": eid_b,
        "created_at": now, "updated_at": now,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"B: {PROJ_B} E1={eid_b} stage=production_prepare status=running "
          f"cancel_requested=True run=prun_cxl_b")


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None   # None=全部, "b"=仅重建 B
    if only != "b":
        # ---- 场景 A：双角色 update_character（char sync 2 单元，真实 Agnes）----
        a1 = Character(name="AudA",
                       description_en="a calm girl with silver short hair and blue eyes")
        a2 = Character(name="AudB",
                       description_en="a tall boy with messy brown hair wearing a green scarf")
        scenes_a = [
            Scene(scene_id="s01", summary="AudA arrives at the station", characters=["AudA"],
                  shots=[_shot("s01_c01", "s01",
                               "AudA walks along the quiet platform at dawn", ["AudA"])]),
            Scene(scene_id="s02", summary="AudA meets AudB", characters=["AudA", "AudB"],
                  shots=[_shot("s02_c01", "s02",
                               "AudA and AudB greet each other by the train", ["AudA", "AudB"])]),
        ]
        ops_a = [
            ChangeOperation(op_type="update_character", character_name="AudA",
                            description_en=BeforeAfter(
                                before="a calm girl with silver short hair and blue eyes",
                                after="a calm girl with long silver hair and violet eyes")),
            ChangeOperation(op_type="update_character", character_name="AudB",
                            description_en=BeforeAfter(
                                before="a tall boy with messy brown hair wearing a green scarf",
                                after="a tall boy with neat black hair wearing a red scarf")),
        ]
        rt_a, store_a, eid_a = asyncio.run(
            seed(PROJ_A, [a1, a2], scenes_a, ops_a, "cs_cancel_a", "plan_cancel_a"))
        ex_a = store_a.get_execution(eid_a)
        print(f"A: {PROJ_A} E1={eid_a} stage={ex_a.stage} status={ex_a.status}")
    seed_b()
    print("SEEDED OK")


if __name__ == "__main__":
    main()
