# -*- coding: utf-8 -*-
"""Phase55 接线冒烟（任务书 §11.2-1）：② producer_lead 预设经产品 REST 入口真实启动。
- 新项目 P55_SMOKE2（微型 2 镜故事，受当日剩余额度约束 segment_count=两）；
- run 启动后轮询状态至终态（或超时），打印步骤账本。
用法：python p55_smoke2_run.py START   # 建项目+启动 run
      python p55_smoke2_run.py POLL    # 只轮询已有 run
"""
import json
import sys
import time
import urllib.request

BASE = "http://127.0.0.1:8000"
PROJ = "P55_SMOKE2B"

STORY_GOAL = ("微型冒烟片《雨夜递伞》：雨夜便利店门口，穿黄色雨衣的店员把伞递给门前"
              "避雨的顾客，两人相视一笑。仅两段：①店员在店内隔着玻璃门注意到门外避雨"
              "的顾客（雨夜氛围/店内灯光）；②店员开门递伞，两人门口相视一笑（门开/"
              "两人同框收尾）。单场景（便利店门口），角色仅店员与顾客两人，无台词，"
              "无道具要求。")


def req(path, body=None, method="GET", timeout=120):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    r = urllib.request.Request(BASE + path, data=data,
                               headers={"Content-Type": "application/json"},
                               method=method)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.load(resp)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "POLL"
    if mode == "START":
        try:
            req(f"/api/projects/create?name={PROJ}&render_family=photorealistic"
                f"&art_direction=%E5%86%99%E5%AE%9E%E5%BE%AE%E5%9E%8B%E5%86%92%E7%83%9F",
                None, "POST")
            print(f"project {PROJ} created")
        except Exception as e:
            print(f"create(可能已存在): {e}")
        out = req(f"/api/project/{PROJ}/collab-runs", {
            "mode_id": "producer_lead",
            "granted_by": "p55-smoke",
            "params": {"story_goal": STORY_GOAL,
                       "segment_count": "两",
                       "duration_hint": "8-12 秒"},
        }, "POST")
        run = out["run"]
        print("run_id=", run["run_id"], "status=", run["status"],
              "hash=", run["snapshot_hash"][:24])
        print("RUNID_FILE:", run["run_id"])
        with open("P55_SMOKE2_RUNID.txt", "w", encoding="utf-8") as f:
            f.write(run["run_id"])
        return
    # POLL
    run_id = open("P55_SMOKE2_RUNID.txt", encoding="utf-8").read().strip()
    run = req(f"/api/project/{PROJ}/collab-runs/{run_id}")["run"]
    print("status=", run["status"], "elapsed=%.0fs" % (time.time() - run["created_at"]))
    for s in run.get("steps") or []:
        d = s.get("detail") or {}
        print(f"  [{s['status']:>8}] {s['step_id']}"
              + (f"  {json.dumps({k: v for k, v in list(d.items())[:3]}, ensure_ascii=False)[:160]}"
                 if d else ""))
    if run.get("result"):
        print("result:", json.dumps(run["result"], ensure_ascii=False)[:400])
    if run.get("result_handoff_pending"):
        print("HANDOFF PENDING:", json.dumps(run["result_handoff_pending"],
                                             ensure_ascii=False)[:200])


if __name__ == "__main__":
    main()
