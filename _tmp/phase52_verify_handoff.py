# -*- coding: utf-8 -*-
"""WorkBuddy skill_copy 与冻结基线哈希对账（严格版）。"""
import hashlib, pathlib, json
WS = pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流")
m = json.loads((WS / "PHASE52_FROZEN_INPUTS/PHASE52_BASELINE_MANIFEST.json").read_text(encoding="utf-8"))
src = {e["path"]: e["sha256"] for e in m["files"]}
wb_root = WS / "PHASE52_WORKBUDDY_TEST"
ok = bad = missing_in_manifest = 0
for f in sorted(wb_root.rglob("*")):
    if not f.is_file():
        continue
    rel = f.relative_to(wb_root).as_posix()          # 统一 posix 斜杠
    h = hashlib.sha256(f.read_bytes()).hexdigest()
    # WorkBuddy 的 skill_copy/... 对应清单 01_skill/...；其余（分镜/参考图）对应
    # 02_project/ 与 03_approved_materials/ 按文件名匹配
    cand = []
    if rel.startswith("skill_copy/"):
        cand.append("01_skill/" + rel[len("skill_copy/"):])
    else:
        name = rel.rsplit("/", 1)[-1]
        cand = [p for p in src if p.rsplit("/", 1)[-1] == name]
    if not cand:
        print("NOT-IN-MANIFEST:", rel)
        missing_in_manifest += 1
    elif any(src.get(c) == h for c in cand):
        ok += 1
    else:
        bad += 1
        print("MISMATCH:", rel)
print(f"对账结果: {ok} 一致 / {bad} 不一致 / {missing_in_manifest} 不在清单")
