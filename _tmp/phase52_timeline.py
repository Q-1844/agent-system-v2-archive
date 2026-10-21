# -*- coding: utf-8 -*-
"""Phase52 时间线生成器：从真实数据源构建可解释时间线 CSV。

数据源（全部真实，无模拟）：
  S1 workflow runs_index.json        —— run 级时间线
  S2 最近 P51_E run 的事件 events.jsonl（完成 + 失败两个 run）—— 节点/attempt 级
  S3 cache/p50_timing_ledger.jsonl   —— 生成链视频事件（video_*）

时区口径：
  - S1/S2 历史事件为 local-as-Z（修复前 store._now_iso），本脚本按 -8h 换算为真 UTC，
    source 列标注 tz_corrected_local_as_Z。
  - S3 timing_ledger 为真 UTC（+00:00），原样使用。
等待原因：由事件类型推导（waiting_human=等待人审；needs_reconciliation=提交不明/输入过期；
video 轮询=服务端处理中；限流等待=本地限流）。不编造缺失字段。
"""
import csv, json, pathlib
from datetime import datetime, timedelta, timezone

REPO = pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard")
OUT = pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流\PHASE52_TIMELINE.csv")
LOCAL_OFFSET = timedelta(hours=8)   # local-as-Z 修复前偏差

def fix_local_as_Z(ts: str):
    """把 local-as-Z 时间戳换算为真 UTC ISO；无法解析返回原值。"""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (dt - LOCAL_OFFSET).astimezone(timezone.utc).isoformat(timespec="milliseconds")
    except Exception:
        return ts

def true_utc(ts: str):
    try:
        dt = datetime.fromisoformat(ts)
        return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds")
    except Exception:
        return ts

rows = []
def add(run_id, task_id, logical, attempt, input_ver, out_ver, event, ts,
        wait_reason, source, evidence):
    rows.append({
        "run_id": run_id, "task_id": task_id, "logical_task": logical,
        "attempt": attempt, "input_version": input_ver, "output_version": out_ver,
        "event": event, "timestamp_utc": ts, "wait_reason": wait_reason,
        "source": source, "evidence": evidence,
    })

# ---- S1: run 级（全部 run）----
idx = json.loads((REPO / "projects/P50_B/output/workflows/runs/runs_index.json").read_text(encoding="utf-8"))
for rid, r in sorted(idx.items(), key=lambda kv: kv[1].get("createdAt") or ""):
    add(rid, "", f"workflow {r.get('workflowId')}", "", "", "",
        f"run.{r.get('status')}", fix_local_as_Z(r.get("createdAt")),
        "", "S1:runs_index.json(tz_corrected_local_as_Z)", "projects/P50_B/output/workflows/runs/runs_index.json")
    if r.get("createdAt") != r.get("updatedAt"):
        add(rid, "", f"workflow {r.get('workflowId')}", "", "", "",
            f"run.last_update({r.get('status')})", fix_local_as_Z(r.get("updatedAt")),
            "等待人审" if r.get("status") == "waiting_human" else "",
            "S1:runs_index.json(tz_corrected_local_as_Z)", "projects/P50_B/output/workflows/runs/runs_index.json")

# ---- S2: 节点/attempt 级（P51_E 两个 run）----
for run_id, label in [("run_9a05fd44f358", "P51_E run1(failed)"), ("run_58a5f25aeeec", "P51_E run2(completed)")]:
    ev_path = REPO / "projects/P50_B/output/workflows/runs" / run_id / "events.jsonl"
    if not ev_path.exists():
        continue
    for line in ev_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except Exception:
            continue
        kind = e.get("kind") or ""
        wait = ""
        if e.get("status") == "waiting_human" or kind == "review.created":
            wait = "等待人审"
        detail = ""
        if kind == "node.state":
            detail = f"{e.get('from_')}->{e.get('to')}"
            if e.get("to") == "needs_reconciliation":
                wait = "提交不明/输入过期"
        elif kind == "attempt.result":
            detail = str(e.get("summary") or e.get("status") or "")[:60]
        elif kind == "run.state":
            detail = str(e.get("status") or "")
        elif kind == "review.decided":
            detail = f"decision={e.get('decision')}"
        add(run_id, e.get("attemptId") or "", e.get("nodeId") or label,
            e.get("attemptId") or "", "", "", f"{kind}" + (f"({detail})" if detail else ""),
            fix_local_as_Z(e.get("ts")), wait,
            "S2:events.jsonl(tz_corrected_local_as_Z)", f"projects/P50_B/output/workflows/runs/{run_id}/events.jsonl#seq={e.get('seq')}")

# ---- S3: 生成链视频事件（P50_B 真实生产，全部 video_* 事件）----
tl = REPO / "cache" / "p50_timing_ledger.jsonl"
if tl.exists():
    for line in tl.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("event") not in ("video_ready", "video_submitted", "video_completed",
                                  "video_downloaded", "video_failed"):
            continue
        if e.get("project") != "P50_B":
            continue
        # 事件缺 epoch 时用 utc 字段；timing ledger utc 为真 UTC
        ts = true_utc(e.get("utc")) if e.get("utc") else ""
        wait = "服务端处理中" if e.get("event") == "video_ready" else ""
        add("", e.get("job_id") or "", f"{e.get('project')}/{e.get('shot_id')} video",
            "", "", e.get("video_id") or "", e.get("event"), ts, wait,
            "S3:p50_timing_ledger.jsonl(true_utc)", "cache/p50_timing_ledger.jsonl")

# 排序输出
rows.sort(key=lambda r: r["timestamp_utc"] or "")
with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("PHASE52_TIMELINE.csv rows:", len(rows))
from collections import Counter
print("by source:", dict(Counter(r["source"].split(":")[0] for r in rows)))
print("by wait_reason:", dict(Counter(r["wait_reason"] for r in rows if r["wait_reason"])))
