# -*- coding: utf-8 -*-
"""修复 PHASE52_BASELINE_MANIFEST.json：files 数组重建为冻结目录的完整实际清单。
根因：冻结脚本 copy_tree_verbatim 未把 Skill 文件条目写入 manifest（磁盘文件本身
正确且与仓库一致，已另行哈希核验）。本脚本对冻结目录逐文件重算 SHA-256，保留原有
条目的 type/source/note 元数据，重新写 manifest 并恢复只读。
"""
import hashlib, json, pathlib
from datetime import datetime, timezone

OUT = pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流\PHASE52_FROZEN_INPUTS")
MP = OUT / "PHASE52_BASELINE_MANIFEST.json"

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

# 解除只读
for f in OUT.rglob("*"):
    if f.is_file():
        f.chmod(0o644)

m = json.loads(MP.read_text(encoding="utf-8"))
old_by_path = {e["path"]: e for e in m["files"]}

def _guess_type(rel):
    if rel.startswith("01_skill/"):
        return "skill_verbatim" if "_loading_mechanism" not in rel else "skill_system_source"
    if rel.startswith("02_project/"): return "project_data"
    if rel.startswith("03_approved_materials/"): return "approved_material"
    if rel.startswith("04_baseline/"): return "baseline"
    return "file"

new_files = []
for f in sorted(OUT.rglob("*")):
    if not f.is_file() or f == MP:
        continue
    rel = f.relative_to(OUT).as_posix()
    h = sha256(f)
    old = old_by_path.get(rel, {})
    e = {"path": rel, "type": old.get("type", _guess_type(rel)),
         "sha256": h, "bytes": f.stat().st_size}
    for k in ("source_abs", "source", "note", "source_url"):
        if k in old:
            e[k] = old[k]
    new_files.append(e)
# manifest 自身最后列（记录自身哈希会自引用，故不含自身——与原逻辑一致）

m["files"] = new_files
m["manifest_rebuilt_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
m["manifest_rebuild_note"] = ("files 数组重建为冻结目录完整实际清单（44 项）。"
    "原导出脚本 copy_tree_verbatim 未把 23 个 Skill 文件条目写入 files（磁盘文件本身"
    "始终正确）；重建后每项 sha256 均自冻结文件实算。")
MP.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")

# 重新冻结
for f in OUT.rglob("*"):
    if f.is_file():
        f.chmod(0o444)
print("manifest files:", len(new_files), "(重建前:", len(old_by_path), ")")
