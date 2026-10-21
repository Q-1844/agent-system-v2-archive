"""E 批 E0 预检与冻结清单（2026-10-19）。只读收集 + 哈希，不做真实调用。"""
import hashlib
import json
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard")
SRC = ROOT / "projects" / "P56_P2_SIGNAL"
OUT = Path(r"D:\isolated\evidence\e_batch")
OUT.mkdir(parents=True, exist_ok=True)

report = {"schema": "e0_preflight_v1", "generated_at": time.time()}

# 1. 日期口径
now_bj = datetime.now()
la = datetime.now(timezone(timedelta(hours=-7)))
report["dates"] = {
    "beijing": now_bj.strftime("%Y-%m-%d %H:%M"),
    "los_angeles": la.strftime("%Y-%m-%d %H:%M"),
    "plan_gate": "real_video_not_before 2026-10-19 (America/Los_Angeles)",
    "gate_note": ("LA 日历尚未到 10-19（差约 15h）；本批以配额所有者 2026-10-19 早"
                  "（北京时间）显式指示『配额已重置，继续完成』作为放行依据，如实记录。"),
}

# 2. 契约事实（config 为准，含 2026-09-28 官方文档核读注释）
report["contract"] = {
    "video_model": "agnes-video-2.5-flash",
    "video_contract": "mode text/keyframe/reference + seconds 字符串 4-12s, 720P",
    "num_frames_rule": "8n+1, <=441 (720p 档)",
    "text_model": "agnes-3.0-flash",
    "vision_review_model": "agnes-2.5-flash (director_vision_review 定版)",
    "rpm_video": 1, "video_inflight_default": 1,
    "quota_daily": {"video_seconds": 500, "images": 4000, "text_calls": 7200},
    "image_host": "github_pages (Q-1844/agnes-frame-host, 按文件哈希缓存)",
}

# 3. 配额账本（本机口径，自动按日 rollover；非服务端真值）
qf = ROOT / "cache" / "quota.json"
report["quota_ledger"] = {
    "file": str(qf), "yesterday": json.loads(qf.read_text(encoding="utf-8")),
    "today_expected": {"date": "2026-10-19", "video_seconds": 0.0},
    "note": "Token Plan 口径；用户已确认配额重置。消费后快照逐笔存档。",
}

# 4. 后端与模式可用性
def api(path):
    with urllib.request.urlopen(f"http://127.0.0.1:8000{path}", timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))

health = api("/api/health")
modes = api("/api/project/P56_P2_SIGNAL/collab-modes")["modes"]
combo = next(m for m in modes if m["mode_id"] == "combo_recommended")
report["backend"] = {
    "health": health, "branch": "feat/phase55-collab-parallel @ da123e2 (R1.1+R1.1.1)",
    "combo_recommended": {"version": combo["mode_version"],
                           "available": combo["available"],
                           "reasons": combo["unavailable_reasons"],
                           "concurrency_default": combo.get("concurrency"),
                           "review_profile": combo.get("review_policy", {}).get("profile")},
}

# 5. 冻结输入包（P56_P2_SIGNAL：批准 Look + 选定首帧 + 绑定；零生图预算）
def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None

proj = json.loads((SRC / "output" / "project.json").read_text(encoding="utf-8"))
assets = []

def resolve(local: str) -> Path | None:
    if not local:
        return None
    p = Path(local)
    if p.is_absolute() and p.is_file():
        return p
    cand = ROOT / local          # 仓根相对（projects\\P56_...\\output\\...）
    if cand.is_file():
        return cand
    cand2 = SRC / local
    return cand2 if cand2.is_file() else None

for c in proj.get("characters", []):
    for view, a in (c.get("views") or {}).items():
        f = resolve(a.get("local"))
        if f is not None:
            assets.append({"kind": "character_look", "name": c.get("name"),
                           "view": view, "path": str(f.relative_to(ROOT)),
                           "sha256": sha(f)})
for sc in proj.get("scenes", []):
    for sh in sc.get("shots", []):
        ff = sh.get("first_frame") or {}
        cands = ff.get("candidates") or []
        if cands and ff.get("status") == "done":
            sel = cands[ff.get("selected_index", 0)]
            f = resolve(sel.get("local"))
            if f is not None:
                assets.append({"kind": "first_frame", "shot_id": sh["shot_id"],
                               "path": str(f.relative_to(ROOT)), "sha256": sha(f)})
bindings = SRC / "output" / "shot_production_bindings.json"
report["frozen_package"] = {
    "source_project": "P56_P2_SIGNAL",
    "source_manifest": "dfbfc4d00e78 (Phase56 C 批冻结)",
    "project_json_sha256": sha(SRC / "output" / "project.json"),
    "bindings_sha256": sha(bindings) if bindings.is_file() else None,
    "shots_total": sum(len(sc.get("shots", [])) for sc in proj.get("scenes", [])),
    "relay_chain": ["s01_c01", "s01_c02", "s01_c03"],
    "independent_shots": ["s01_c04", "s01_c05", "s02_c01"],
    "approved_assets": assets,
    "image_generation_budget_today": 0,
}

# 6. 今日计划（≤74s/17 上限内的执行子集；R2 组 not_implemented）
report["plan_today"] = {
    "smoke": {"shots": ["s01_c01"], "seconds": 4, "calls": 1,
              "vehicle": "直发 REST video job（无文本模型）→ 版本回执/任务ID/配额链核对"},
    "group_r11": {"project": "P56_E_R11_A", "shots": 6, "seconds": 24,
                  "vehicle": "combo_recommended v2.1.0 + approved_package（真实 Producer）",
                  "concurrency": "mode default 1（已验证基线，不做扩容试验）"},
    "repair_cap": {"calls": 1, "seconds": 6},
    "r2_group": "not_implemented（B 批纵切片未接真实 settlement，不做真实验证）",
    "caps_today": {"seconds_max": 34, "calls_max": 8},
}

(OUT / "E0_preflight.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: report[k] for k in ("dates", "backend")}, ensure_ascii=False, indent=1))
print(f"frozen assets: {len(assets)} | plan today: <=34s / <=8 calls")
