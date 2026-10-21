# -*- coding: utf-8 -*-
"""AI-7D-R 批量工具真机 e2e 实测（throwaway 项目 __sw_batch_e2e）。

Phase A（create_many）：一次 turn 要求"末尾连续新增 5 段" ->
  期望：story.list -> 单次 story.create_many ok=True，零串行拒绝（无 ok=False
  写工具、无连续 story.create），磁盘 project.json 真落盘 11 段（s07~s11）。
Phase B（update_many）：同会话第二 turn 要求"把这 5 个新段的 summary 都改生动" ->
  期望：单次 story.update_many ok=True，结构不动（11 段同 id 同序），
  5 段 summary 磁盘真改、shots/characters 不动。

全程走真后端 :8000 /turn/stream（真 Agnes LLM），断言磁盘最终状态。
"""
import json
import shutil
import sys
from pathlib import Path

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent   # 脚本在 animation-storyboard 根，不是 scripts/
BASE = "http://localhost:8000"
P = "__sw_batch_e2e"


def _ensure_project():
    """重建全新 6 段 throwaway 项目（避免旧状态污染）。"""
    pdir = ROOT / "projects" / P
    if pdir.exists():
        shutil.rmtree(pdir)
    pdir.mkdir(parents=True)
    (pdir / "output").mkdir()
    from src.core.store import ProjectStore
    from src.core.models import Project, Scene, Character, StyleAnchor
    proj = Project(
        name=P, style=StyleAnchor(),
        story_text="小雨撑着伞走在雨夜的街道上。她发现了一只淋湿的小猫，用外套把它裹起来带回了家。回家后给小猫洗了澡，取名豆豆。第二天她在小猫项圈下发现了一张车票，于是开始寻找它的主人老奶奶。",
        characters=[Character(name="LinXia", description_en="a young woman with an umbrella")],
        scenes=[
            Scene(scene_id="s01", summary="雨夜回家路上", characters=["LinXia"], shots=[]),
            Scene(scene_id="s02", summary="发现淋湿的小猫", characters=["LinXia"], shots=[]),
            Scene(scene_id="s03", summary="用外套包裹小猫", characters=["LinXia"], shots=[]),
            Scene(scene_id="s04", summary="回家洗澡取名豆豆", characters=["LinXia"], shots=[]),
            Scene(scene_id="s05", summary="发现项圈下的车票", characters=["LinXia"], shots=[]),
            Scene(scene_id="s06", summary="寻找老奶奶归还", characters=["LinXia"], shots=[]),
        ],
        next_scene_seq=7,
    )
    ProjectStore(pdir).save(proj)
    print(f"[setup] 全新项目 {P}（6 段）")


def _disk():
    data = json.loads((ROOT / "projects" / P / "output" / "project.json")
                      .read_text(encoding="utf-8"))
    return data


def _run_turn(sid: str, content: str):
    """发一轮 /turn/stream，收集事件 -> (tool_calls, assistant_text, completed_result)"""
    tools, assistant, result, failed = [], "", None, None
    t0 = __import__("time").time()
    with httpx.stream("POST",
                      f"{BASE}/api/project/{P}/agents/sessions/{sid}/turn/stream",
                      json={"content": content, "thinking": False}, timeout=300) as resp:
        if resp.status_code != 200:
            body = resp.read().decode("utf-8", "replace")[:400]
            print(f"[HTTP {resp.status_code}] {body}")
            sys.exit(1)
        for line in resp.iter_lines():
            if not line or not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            try:
                ev = json.loads(payload)
            except Exception:
                continue
            t = ev.get("type")
            if t == "tool.completed":
                tools.append((ev.get("name"), ev.get("ok"), (ev.get("summary") or "")[:120]))
            elif t == "tool.failed":
                tools.append((ev.get("name"), False, (ev.get("error") or "tool.failed")[:120]))
            elif t == "assistant.delta":
                assistant += ev.get("delta", "")
            elif t == "turn.completed":
                result = ev.get("result")
            elif t == "turn.failed":
                failed = ev.get("error")
    dt = __import__("time").time() - t0
    if failed:
        print(f"[turn.failed] {failed}")
    print(f"[turn 耗时 {dt:.0f}s] 工具序列：")
    for name, ok, summary in tools:
        print(f"    - {name:22s} ok={ok}  {summary}")
    print(f"[assistant] {assistant[:300]}")
    return tools, assistant, result


def main():
    _ensure_project()
    r = httpx.post(f"{BASE}/api/project/{P}/agents/sessions",
                   json={"agent_id": "script_writer", "scope_type": "project", "scope_id": P},
                   timeout=15)
    r.raise_for_status()
    sid = r.json()["session_id"]
    print(f"[session] {sid}\n")

    # ---------- Phase A：批量创建 ----------
    print("=" * 64)
    print("Phase A · 批量创建（末尾连续新增 5 段）")
    print("=" * 64)
    content_a = ("请在剧本末尾连续新增 5 段故事：第1段小猫豆豆和邻居小孩在院子里玩耍；"
                 "第2段带豆豆去看兽医做体检；第3段豆豆在家里打翻了花瓶；"
                 "第4段小雨教豆豆握手；第5段半年后豆豆长大了变成了大猫。")
    tools_a, _, result_a = _run_turn(sid, content_a)

    print("\n[Phase A 校验]")
    a_pass = {}
    names = [t[0] for t in tools_a]
    a_pass["有且仅有一次 create_many"] = names.count("story.create_many") == 1
    a_pass["零次单写 story.create"] = names.count("story.create") == 0
    a_pass["零写失败/串行拒绝"] = all(ok for n, ok, _ in tools_a
                                     if n in ("story.create", "story.create_many",
                                              "story.update", "story.update_many"))
    disk = _disk()
    scenes = disk["scenes"]
    ids = [s["scene_id"] for s in scenes]
    a_pass["磁盘落盘 11 段"] = len(scenes) == 11
    a_pass["新段 id s07~s11 顺序正确"] = ids[6:] == ["s07", "s08", "s09", "s10", "s11"]
    new_summaries = " | ".join(s["summary"] for s in scenes[6:])
    print(f"    磁盘段数={len(scenes)} ids={ids}")
    print(f"    新段 summary：{new_summaries}")
    for k, v in a_pass.items():
        print(f"    {'PASS' if v else 'FAIL'} · {k}")

    # ---------- Phase B：批量修改 ----------
    print()
    print("=" * 64)
    print("Phase B · 批量修改（s07~s11 五段 summary 改生动）")
    print("=" * 64)
    before = {s["scene_id"]: s["summary"] for s in scenes[6:]}
    before_chars = {s["scene_id"]: s.get("characters") for s in scenes}
    content_b = "请把 s07 到 s11 这 5 段的 summary 都改写得更生动、更有画面感，保持原意不变，一次改完。"
    tools_b, _, result_b = _run_turn(sid, content_b)

    print("\n[Phase B 校验]")
    disk_b = _disk()
    scenes_b = disk_b["scenes"]
    ids_b = [s["scene_id"] for s in scenes_b]
    b_pass = {}
    names_b = [t[0] for t in tools_b]
    b_pass["有且仅有一次 update_many"] = names_b.count("story.update_many") == 1
    b_pass["零次单写 story.update"] = names_b.count("story.update") == 0
    b_pass["零写失败/串行拒绝"] = all(ok for n, ok, _ in tools_b
                                     if n in ("story.create", "story.create_many",
                                              "story.update", "story.update_many"))
    b_pass["结构不动（11 段同 id 同序）"] = ids_b == ids
    changed = [i for i in ("s07", "s08", "s09", "s10", "s11")
               if next(s for s in scenes_b if s["scene_id"] == i)["summary"] != before[i]]
    b_pass["5 段 summary 磁盘真改"] = len(changed) == 5
    b_pass["characters 未被动"] = all(
        next(s for s in scenes_b if s["scene_id"] == i)["characters"] == before_chars[i]
        for i in before_chars)
    for i in ("s07", "s08", "s09", "s10", "s11"):
        s = next(s for s in scenes_b if s["scene_id"] == i)
        mark = "->改" if i in changed else "->未改"
        print(f"    {i}{mark}: {s['summary'][:60]}")
    for k, v in b_pass.items():
        print(f"    {'PASS' if v else 'FAIL'} · {k}")

    all_ok = all(a_pass.values()) and all(b_pass.values())
    print()
    print("=" * 64)
    print(f"总判定：{'ALL PASS' if all_ok else '存在 FAIL，见上'}")
    print("=" * 64)
    sys.exit(0 if all_ok else 2)


if __name__ == "__main__":
    main()
