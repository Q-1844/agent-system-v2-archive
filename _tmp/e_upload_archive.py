"""上传归档 tar 到 GitHub Release 资产（顺序+逐个校验）。"""
import json
import subprocess
import time
from pathlib import Path

ARC = Path(r"D:\isolated\github_archive")
REL_ID = "417460021"
TOKEN = None
for line in Path(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard\.env").read_text(encoding="utf-8").splitlines():
    if line.startswith("GITHUB_TOKEN="):
        TOKEN = line.split("=", 1)[1].strip().strip("\r")
assert TOKEN

tars = sorted(ARC.glob("*.tar"))
print(f"{len(tars)} tars, total {sum(t.stat().st_size for t in tars)/1e6:.0f} MB")
results = []
for t in tars:
    size = t.stat().st_size
    name = t.name
    for attempt in (1, 2, 3):
        r = subprocess.run(
            ["curl", "-s", "--max-time", "3600", "-X", "POST",
             "-H", f"Authorization: Bearer {TOKEN}",
             "-H", "Content-Type: application/octet-stream",
             "--data-binary", f"@{t}",
             f"https://uploads.github.com/repos/Q-1844/agnes-frame-host/releases/{REL_ID}/assets?name={name}"],
            capture_output=True, text=True, timeout=3700)
        try:
            resp = json.loads(r.stdout)
        except Exception:
            resp = {}
        if resp.get("id") and resp.get("size") == size:
            results.append({"name": name, "ok": True, "size": size})
            print(f"OK {name} {size/1e6:.0f}MB")
            break
        status = resp.get("errors") or resp.get("message") or r.stdout[:150]
        print(f"RETRY{attempt} {name}: {str(status)[:120]}")
        time.sleep(5)
    else:
        results.append({"name": name, "ok": False, "size": size})

ok = sum(1 for r in results if r["ok"])
Path(r"D:\isolated\evidence\e_batch\upload_results.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"DONE: {ok}/{len(results)} uploaded")
