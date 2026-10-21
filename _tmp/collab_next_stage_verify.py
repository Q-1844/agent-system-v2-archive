"""Verify handoff package manifest hashes and list patch zip contents. Read-only."""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

PKG = Path(r"C:\Users\曹文淇\Desktop\ai工作流\.claude\压缩包\COLLAB_NEXT_STAGE")
manifest = json.loads((PKG / "HANDOFF_MANIFEST.json").read_text(encoding="utf-8"))

ok = True
for entry in manifest["files"]:
    p = PKG / entry["path"]
    if not p.is_file():
        print(f"MISSING {entry['path']}")
        ok = False
        continue
    data = p.read_bytes()
    h = hashlib.sha256(data).hexdigest()
    size_ok = len(data) == entry["bytes"]
    hash_ok = h == entry["sha256"]
    if not (size_ok and hash_ok):
        ok = False
        print(f"MISMATCH {entry['path']}: size={len(data)}/{entry['bytes']} sha256={h}")
print("manifest check:", "ALL PASS" if ok else "FAILED")

zip_path = PKG / "patches/COLLAB_FIX_R1_1_20261018.zip"
z = zipfile.ZipFile(zip_path)
names = z.namelist()
print(f"\npatch zip entries: {len(names)}")
for n in names:
    info = z.getinfo(n)
    print(f"  {info.file_size:>10}  {n}")
