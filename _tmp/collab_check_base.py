"""Check local working tree against R1.1 PATCH_MANIFEST before/after hashes. Read-only."""
import hashlib
import json
from pathlib import Path

ROOT = Path(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard")
MANIFEST = Path(r"D:\isolated\COLLAB_FIX_R1_1_20261018\COLLAB_FIX_R1_1\PATCH_MANIFEST.json")

m = json.loads(MANIFEST.read_text(encoding="utf-8"))
match_before = match_after = mismatch = missing = 0
for e in m["files"]:
    p = ROOT / e["path"]
    if not p.is_file():
        print(f"MISSING        {e['path']}")
        missing += 1
        continue
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h == e["before_sha256"]:
        match_before += 1
    elif h == e["after_sha256"]:
        print(f"ALREADY_APPLIED {e['path']}")
        match_after += 1
    else:
        print(f"MISMATCH       {e['path']}\n  local={h}\n  before={e['before_sha256']}")
        mismatch += 1
print(f"\nsummary: before-match={match_before} already={match_after} mismatch={mismatch} missing={missing} total={len(m['files'])}")
