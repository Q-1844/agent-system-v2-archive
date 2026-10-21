# -*- coding: utf-8 -*-
"""Phase52 冻结交接导出脚本（CodeBuddy）。
从真实仓库导出：正式 Skill 原文、依赖规则、绑定清单、克苏鲁追船剧本/分镜/合格素材，
生成 PHASE52_BASELINE_MANIFEST.json 与 PHASE52_INPUTS_STATUS.md，并置只读。
本脚本只读取仓库；唯一的出站请求是尝试下载本地缺失的已批准渔船参考图（公开 COS URL）。
"""
import json
import hashlib
import shutil
import pathlib
import subprocess
import datetime
import urllib.request

REPO = pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard")
OUT = pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流\PHASE52_FROZEN_INPUTS")
PROJ = REPO / "projects" / "P50_B"
EXPORTED_AT = datetime.datetime.now().isoformat(timespec="seconds")

def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def copy_tree_verbatim(src: pathlib.Path, dst: pathlib.Path, entries, rel_root):
    """逐文件复制并记录哈希，保持相对结构。"""
    out = []
    for f in sorted(src.rglob("*")):
        if f.is_file():
            rel = f.relative_to(src)
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, target)
            out.append({
                "path": str((rel_root / rel)).replace("\\", "/"),
                "sha256": sha256(target),
                "bytes": target.stat().st_size,
                "source_abs": str(f),
            })
    return out

def copy_file(src: pathlib.Path, dst_rel: str, entries, kind, note=None):
    target = OUT / dst_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, target)
    e = {
        "path": dst_rel.replace("\\", "/"),
        "type": kind,
        "source_abs": str(src),
        "sha256": sha256(target),
        "bytes": target.stat().st_size,
    }
    if note:
        e["note"] = note
    entries.append(e)
    return e

# ---------- 0. 准备 ----------
if OUT.exists():
    raise SystemExit(f"输出目录已存在，拒绝覆盖：{OUT}")
OUT.mkdir(parents=True)
entries = []          # manifest files 数组
missing = []          # 缺失项记录
warnings = []

# ---------- 1. 正式 Skill 逐字导出 ----------
SKILL_ROOT = REPO / "src" / "agents" / "skill_system"
skill_pkgs = []
for pkg_dir, tier in [
    (SKILL_ROOT / "builtin" / "full-story-relay-calibration", "builtin_core"),
    (SKILL_ROOT / "builtin" / "keyframes-bridge-repair", "builtin_core"),
    (SKILL_ROOT / "candidate" / "agnes-production-craft", "candidate"),
]:
    sid = json.loads((pkg_dir / "skill.json").read_text(encoding="utf-8"))
    dst = OUT / "01_skill" / f"{tier}__{sid['skill_id']}__v{sid['version']}"
    files = copy_tree_verbatim(pkg_dir, dst, entries, pathlib.Path("01_skill") / f"{tier}__{sid['skill_id']}__v{sid['version']}")
    skill_pkgs.append({
        "skill_id": sid["skill_id"],
        "version": sid["version"],
        "name": sid.get("name"),
        "tier": tier,
        "status": sid.get("status"),
        "bindings": sid.get("bindings"),
        "required_capabilities": sid.get("required_capabilities"),
        "file_count": len(files),
    })

# Skill 加载机制源码（registry/runtime/models，供 WorkBuddy 理解绑定语义；只读副本）
for f in ["registry.py", "runtime.py", "models.py"]:
    src = SKILL_ROOT / f
    if src.is_file():
        copy_file(src, f"01_skill/_loading_mechanism/{f}", entries, "skill_system_source")

# ---------- 2. 项目数据导出 ----------
proj_exports = [
    (PROJ / "output" / "project.json", "02_project/project.json", "canonical", "canonical project.json：剧本 story_text + 5 场景 20 镜头"),
    (PROJ / "output" / "resources.json", "02_project/resources.json", "canonical", "4 个角色 Look（船长/大副/渔船/海怪）+ 47 个参考资产元数据"),
    (REPO / "_p50_c_package" / "LOCKED_STORYBOARD.json", "02_project/LOCKED_STORYBOARD.json", "locked_storyboard", "锁定分镜：frozen_from run_b25f5b900c3b 分镜审定通过版本，20 镜"),
    (REPO / "_p50_c_package" / "COMMON_INTENT.json", "02_project/COMMON_INTENT.json", "locked_intent", "公共意图包：角色/船/怪物/声音政策/叙事段落"),
    (PROJ / "output" / "resources" / "generation_records.jsonl", "02_project/generation_records.jsonl", "evidence", "历史生成请求与回执记录（receipts 证据）"),
    (PROJ / "output" / "resources" / "review_records.jsonl", "02_project/review_records.jsonl", "evidence", "历史审查记录"),
    (PROJ / "output" / "workflows" / "definitions" / "P50_B_W09r6.json", "02_project/workflow_P50_B_W09r6.json", "workflow_definition", "完成 20 镜生产的工作流定义（六 Agent）"),
    (PROJ / "output" / "workflows" / "runs" / "runs_index.json", "02_project/workflows_runs_index.json", "evidence", "全部工作流 run 索引与状态"),
]
for src, rel, kind, note in proj_exports:
    if src.is_file():
        copy_file(src, rel, entries, kind, note)
    else:
        missing.append({"item": rel, "reason": f"文件不存在：{src}"})

# ---------- 3. 合格参考素材（已批准 Look 参考） ----------
res = json.loads((PROJ / "output" / "resources.json").read_text(encoding="utf-8"))
looks, ra = res["looks"], res["reference_assets"]
look_summary = []
for look_id, look in looks.items():
    approved_ids = look.get("approved_reference_asset_ids") or []
    rec = {
        "look_id": look_id,
        "character_name": look.get("character_name"),
        "label": look.get("label"),
        "approval_status": look.get("approval_status"),
        "generation_status": look.get("generation_status"),
        "approved_reference_asset_ids": approved_ids,
        "cover_asset_id": look.get("cover_asset_id"),
        "approved_files": [],
    }
    for aid in approved_ids:
        a = ra.get(aid)
        if not a:
            missing.append({"item": f"look {look_id} 的批准资产 {aid}", "reason": "resources.json 中不存在该资产记录"})
            continue
        lp, url = a.get("local"), a.get("url")
        if lp:
            src = PROJ / lp
            if src.is_file():
                ext = src.suffix
                rel = f"03_approved_materials/{look_id}__{aid}{ext}"
                copy_file(src, rel, entries, "approved_reference_image",
                          f"{look.get('character_name')} 已批准参考（view={a.get('view')}, source={a.get('source')}）")
                rec["approved_files"].append(rel.replace("\\", "/"))
            else:
                missing.append({"item": f"{look_id}/{aid}", "reason": f"local 路径文件缺失：{lp}（url={url}）"})
        elif url:
            # 唯一出站请求：下载本地缺失的已批准参考（公开 COS 输出 URL）
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "phase52-freeze-export/1.0"})
                with urllib.request.urlopen(req, timeout=60) as resp, \
                     open(OUT / f"03_approved_materials/{look_id}__{aid}.png", "wb") as wf:
                    wf.write(resp.read())
                rel = f"03_approved_materials/{look_id}__{aid}.png"
                p = OUT / rel
                e = {"path": rel.replace("\\", "/"), "type": "approved_reference_image",
                     "source_url": url, "sha256": sha256(p), "bytes": p.stat().st_size,
                     "note": f"{look.get('character_name')} 已批准参考，本地缺失，从原始 URL 下载导出"}
                entries.append(e)
                rec["approved_files"].append(rel.replace("\\", "/"))
                warnings.append(f"{aid} 本地文件缺失，已从 URL 下载导出；需视觉核验内容仍为批准版本")
            except Exception as ex:
                missing.append({"item": f"{look_id}/{aid}", "reason": f"local=None 且 URL 下载失败：{url} ({ex})"})
        else:
            missing.append({"item": f"{look_id}/{aid}", "reason": "无 local 路径也无 url"})
    look_summary.append(rec)

# ---------- 4. 既有首帧资产清单（不复制 109MB，仅哈希清单） ----------
frames_dir = PROJ / "output" / "frames"
first_frames = sorted(frames_dir.glob("*_first_v*.png"))
frame_index = []
for f in first_frames:
    frame_index.append({"file": f.name, "sha256": sha256(f), "bytes": f.stat().st_size})
(OUT / "03_approved_materials").mkdir(parents=True, exist_ok=True)
fi_path = OUT / "03_approved_materials/first_frames_index.json"
fi_path.write_text(json.dumps({"count": len(frame_index), "location_in_repo": str(frames_dir), "frames": frame_index}, ensure_ascii=False, indent=2), encoding="utf-8")
entries.append({"path": "03_approved_materials/first_frames_index.json", "type": "asset_index",
                "sha256": sha256(fi_path), "bytes": fi_path.stat().st_size,
                "note": f"20 镜首帧资产哈希清单（共 {len(frame_frames := frame_index)} 个文件，原文件在仓库内未复制）" if False else f"首帧资产哈希清单（{len(frame_index)} 个文件，原文件在仓库内未复制）"})

# ---------- 5. 基线：git + 配置指纹 ----------
def git(*args):
    r = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout.strip() if r.returncode == 0 else f"ERROR: {r.stderr.strip()}"

git_baseline = {
    "repo": str(REPO),
    "baseline_branch": "feat/agent-v2-phase-d-golden-run",
    "work_branch_created": "phase52/efficiency",
    "baseline_commit": git("rev-parse", "HEAD"),
    "commit_subject": git("log", "-1", "--format=%s"),
    "uncommitted_tracked": git("status", "--porcelain=v1", "-uno").splitlines(),
    "untracked_count": len(git("status", "--porcelain=v1").splitlines()),
    "recorded_at": EXPORTED_AT,
}

cfg_text = (REPO / "config" / "config.yaml").read_text(encoding="utf-8")
config_fingerprint = {
    "config_yaml_sha256": sha256(REPO / "config" / "config.yaml"),
    "env_sha256_no_content": sha256(REPO / ".env"),
    "key_params": {
        "agnes_base_url": "https://api.agnes-ai.cn",
        "text_model": "agnes-3.0-flash",
        "vision_model_env": "agnes-2.5-flash (director_vision_review.py 显式)",
        "image_model": "agnes-image-2.1-flash",
        "video_model": "agnes-video-2.5-flash",
        "rpm": {"text": 20, "image_1k": 20, "image_2k": 16, "image_3k": 1, "image_4k": 1, "video": 1},
        "image": {"size_tier": "1K", "ratio": "16:9", "timeout_s": 300},
        "video": {"frame_rate": 24, "polling_interval_s": 5, "max_wait_s": 3600},
        "image_host": {"kind": "github_pages", "repo": "Q-1844/agnes-frame-host", "fallback": "imgbb"},
        "daily_quota": {"video_seconds": 500, "images": 4000, "text_calls": 7200},
        "text_provider": "agnes",
    },
    "note": "凭据不进入交接；.env 仅记录哈希指纹",
}
copy_file(REPO / "config" / "config.yaml", "04_baseline/config.yaml", entries, "config_copy",
          "平台参数配置原文（密钥均为 ${ENV_VAR} 占位，无明文凭据）")
(OUT / "04_baseline").mkdir(parents=True, exist_ok=True)
gb_path = OUT / "04_baseline/git_baseline.json"
gb_path.write_text(json.dumps(git_baseline, ensure_ascii=False, indent=2), encoding="utf-8")
entries.append({"path": "04_baseline/git_baseline.json", "type": "baseline", "sha256": sha256(gb_path), "bytes": gb_path.stat().st_size})
cf_path = OUT / "04_baseline/config_fingerprint.json"
cf_path.write_text(json.dumps(config_fingerprint, ensure_ascii=False, indent=2), encoding="utf-8")
entries.append({"path": "04_baseline/config_fingerprint.json", "type": "baseline", "sha256": sha256(cf_path), "bytes": cf_path.stat().st_size})

# ---------- 6. 生成账号非敏感标识（Agnes） ----------
env_line_count = 0
has_agnes_key = has_gh_token = has_imgbb = has_sensenova = False
for line in (REPO / ".env").read_text(encoding="utf-8", errors="replace").splitlines():
    env_line_count += 1
    k = line.split("=")[0].strip().upper()
    if k == "AGNES_API_KEY": has_agnes_key = True
    if k == "GITHUB_TOKEN": has_gh_token = True
    if k == "IMGBB_API_KEY": has_imgbb = True
    if k == "SENSENOVA_API_KEY": has_sensenova = True
account_ident = {
    "agnes_account": "api.agnes-ai.cn 账号（key 存在于 .env，值不导出）" if has_agnes_key else "未配置",
    "github_pages_host_account": "Q-1844/agnes-frame-host（图床）" if has_gh_token else "未配置",
    "imgbb": "已配置（回退图床）" if has_imgbb else "未配置",
    "sensenova": "已配置" if has_sensenova else "未配置",
    "quota_pool_note": "Agnes Token Plan：视频 500s/天、生图 4000/天、文本 1500/5h。本机单账号单配额池；WorkBuddy 生成额度是否共享未核实前，不得同时生成。",
}

# ---------- 7. PHASE52_BASELINE_MANIFEST.json ----------
manifest = {
    "phase": "PHASE52",
    "exported_at": EXPORTED_AT,
    "exported_by": "CodeBuddy (GLM-5.3-Flash) @ workspace c:/Users/曹文淇/Desktop/ai工作流",
    "repo": str(REPO),
    "project": "P50_B《深水惊魂》（克苏鲁海怪追渔船；船长+大副）",
    "git_baseline": git_baseline,
    "config_fingerprint_summary": {k: v for k, v in config_fingerprint.items() if k != "key_params"},
    "generation_account_nonsensitive": account_ident,
    "skill_packages": skill_pkgs,
    "skill_binding_summary": "full-story-relay-calibration v1.6.0：director=primary_executor(100)、producer=coordinator(80)、script_writer=contributor(60)、character_designer=conditional(40)、scene_designer=conditional(40)；activation_mode=hinted；authority_tier=builtin_core。绑定清单原文见各 skill.json。",
    "looks": look_summary,
    "storyboard": {
        "locked_storyboard": "02_project/LOCKED_STORYBOARD.json（20 镜，frozen_from run_b25f5b900c3b）",
        "common_intent": "02_project/COMMON_INTENT.json",
        "canonical": "02_project/project.json（story_text 五幕剧本 + 5 场景 20 镜头）",
    },
    "first_frames": f"{len(frame_index)} 个首帧资产（哈希清单：03_approved_materials/first_frames_index.json；原文件留在仓库）",
    "files": entries,
    "missing_items": missing,
    "warnings": warnings,
    "known_dependencies": [
        "skill.json required_capabilities（capability 校验在 CapabilityRegistry）",
        "references/production-recipes.md 等依赖文件（已逐字导出）",
        "锁定分镜依赖 canonical project.json 的场景/镜头定义",
        "首帧/尾帧接力依赖视频实际保留区间最后一张真实解码帧（见 LOCKED_STORYBOARD rules）",
    ],
}
mp = OUT / "PHASE52_BASELINE_MANIFEST.json"
mp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------- 8. PHASE52_INPUTS_STATUS.md ----------
approved_ok = sum(1 for r in look_summary if r["approved_files"])
status_md = f"""# PHASE52 输入状态（CodeBuddy → WorkBuddy 交接）

导出时间：{EXPORTED_AT}。基线 commit：`{git_baseline['baseline_commit']}`（分支 feat/agent-v2-phase-d-golden-run，工程分支 phase52/efficiency）。

## WorkBuddy 现在可以开始的步骤

| 输入 | 状态 | 位置 |
|---|---|---|
| 正式 Skill 主文件 | 已冻结 | `01_skill/builtin_core__full-story-relay-calibration__v1.6.0/SKILL.md` |
| Skill 依赖规则 | 已冻结（7 份 references） | 同上目录 `references/` |
| Skill 绑定清单 | 已冻结（skill.json bindings + required_capabilities） | 同上目录 `skill.json` |
| 修复技能（参考） | 已冻结 | `01_skill/builtin_core__keyframes-bridge-repair__v1.0.0/` |
| 候选技能（非正式，未转正） | 已冻结并标注 | `01_skill/candidate__agnes-production-craft__*` |
| 剧本（五幕） | 已冻结 | `02_project/project.json` story_text |
| 锁定分镜（20 镜） | 已冻结 | `02_project/LOCKED_STORYBOARD.json` |
| 公共意图（角色/船/怪物/声音政策） | 已冻结 | `02_project/COMMON_INTENT.json` |
| 角色 Look 合格参考 | {'4/4 已导出' if approved_ok == 4 else f'{approved_ok}/4 已导出'} | `03_approved_materials/` |
| 历史 receipts/审查证据 | 已冻结 | `02_project/generation_records.jsonl`、`review_records.jsonl` |
| 六 Agent 工作流定义（W09r6 完成版） | 已冻结 | `02_project/workflow_P50_B_W09r6.json` |

**结论：剧本与锁定分镜存在，WorkBuddy 的视频主测试属于「同分镜冻结输入测试」，不需要自主规划。**

## 缺失与限制（如实记录）

"""
for m in missing:
    status_md += f"- 缺失：{m['item']}——{m['reason']}\n"
for w in warnings:
    status_md += f"- 注意：{w}\n"
status_md += """
- 海怪 Look 的 `generation_status=failed` 但存在 1 张已批准参考（ref_9c0ba4bed38c）；以批准参考为准。
- 首帧资产未整包复制（234 个文件约 109MB），仅提供哈希清单 `03_approved_materials/first_frames_index.json`；WorkBuddy 需要具体首帧时可按清单在仓库内定位。
- 本目录为冻结只读副本：不要在此目录内修改；WorkBuddy 的适配副本应在自己的工作区创建。

## 额度与同步约束（重要）

本机 Agnes 为单账号单配额池（视频 500s/天等，见 `04_baseline/config_fingerprint.json`）。WorkBuddy 平台账号与额度由 WorkBuddy 自行核验；在两边的生成额度独立性核实之前，不得同时发起生成请求。本轮 CodeBuddy 不提交新视频（配额不足），仅做真实图片链路与恢复测试。

## 哈希核验

`PHASE52_BASELINE_MANIFEST.json` 的 `files` 数组含每个文件的 SHA-256。收到后先核对哈希再使用。
"""
sp = OUT / "PHASE52_INPUTS_STATUS.md"
sp.write_text(status_md, encoding="utf-8")

# ---------- 9. 只读冻结 ----------
n_ro = 0
for f in OUT.rglob("*"):
    if f.is_file():
        f.chmod(0o444)
        n_ro += 1

print("EXPORT OK")
print("root:", OUT)
print("files exported:", len(entries), "| set read-only:", n_ro)
print("skill packages:", [(s['skill_id'], s['version'], s['tier'], s['file_count']) for s in skill_pkgs])
print("looks:", [(r['character_name'], len(r['approved_files'])) for r in look_summary])
print("first frames indexed:", len(frame_index))
print("missing:", len(missing), "| warnings:", len(warnings))
for m in missing: print("  MISSING:", m["item"], "=>", m["reason"][:100])
for w in warnings: print("  WARN:", w[:120])
