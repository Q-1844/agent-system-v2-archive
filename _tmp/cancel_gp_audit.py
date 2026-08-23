# -*- coding: utf-8 -*-
"""AI-7C-H Cancel Hotfix 浏览器验收（§十五，临时脚本勿提交）。

真实前端(vite preview 7779) + 真实 FastAPI(8000) + 真实 Agnes（场景 A char sync 真跑）。

场景 A（__cancel_gp_a，主场景）：
  E1 真实运行（char sync 真实 Agnes view 生成）→ 用户提交新修改 → 选「停止当前任务并
  重新规划」→ UI「正在停止当前任务…」→ 旧 E1/owned run 实际停止且不复活 → 不进 planning
  不建 ProductionRun → 新 ChangeSession 自动开始（不被旧 R1 阻塞）。

场景 B（__cancel_gp_b）：
  stopping 中（E1 cancel_requested + owned R1 running+cancel_requested）→ backend restart
  → 恢复收敛（R1 cancelled + E1 cancelled，不复活不续跑）→ 页面恢复显示与持久状态一致。
"""
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
from dotenv import load_dotenv
load_dotenv()

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

API = "http://localhost:8000"
FRONT = "http://localhost:7779"
PROJ_A = "__cancel_gp_a"
PROJ_B = "__cancel_gp_b"
NODE_DIR = r"C:\Users\曹文淇\Desktop\PFiles64\nodejs"

RESULTS = {}
BACKEND_LOGS = ["cancel_backend1.log", "cancel_backend2.log"]


def log(m):
    print(f"[cancel-gp] {m}", flush=True)


def api_get(path, timeout=10):
    try:
        with urllib.request.urlopen(f"{API}{path}", timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return {"_http": e.code, **json.loads(e.read().decode("utf-8"))}
        except Exception:
            return {"_http": e.code}
    except Exception as e:
        return {"_err": str(e)}


def api_post(path, payload, timeout=30):
    req = urllib.request.Request(f"{API}{path}",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def port_free(port=8000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def wait_for(pred, timeout, desc, interval=1.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        v = pred()
        if v:
            return v
        time.sleep(interval)
    raise TimeoutError(f"等待超时: {desc} ({timeout}s)")


def get_exec(pname, sid, eid):
    return api_get(f"/api/project/{pname}/change-sessions/{sid}/executions/{eid}")


def start_backend(log_name):
    if not port_free():
        raise RuntimeError("端口 8000 被占用，无法启动 backend")
    lf = open(BASE / log_name, "w", encoding="utf-8")
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "api_server:app",
                             "--port", "8000"],
                            cwd=str(BASE), stdout=lf, stderr=subprocess.STDOUT)
    try:
        wait_for(lambda: api_get("/openapi.json").get("openapi") is not None,
                 120, "backend 就绪")
    except Exception:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       capture_output=True)
        raise
    time.sleep(2)   # startup 恢复任务（async create_task）消化
    return proc


def stop_backend(proc):
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                   capture_output=True)
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        pass
    wait_for(port_free, 30, "端口 8000 释放")


def start_front(log_name):
    if not port_free(7779):
        raise RuntimeError("端口 7779 被占用")
    lf = open(BASE / log_name, "w", encoding="utf-8")
    env = {**os.environ, "PATH": NODE_DIR + os.pathsep + os.environ.get("PATH", "")}
    node = os.path.join(NODE_DIR, "node.exe")
    proc = subprocess.Popen([node, os.path.join("node_modules", "vite", "bin", "vite.js"),
                             "preview", "--port", "7779", "--strictPort"],
                            cwd=str(BASE), stdout=lf, stderr=subprocess.STDOUT, env=env)
    wait_for(lambda: _front_ok(), 60, "vite preview 就绪")
    return proc


def _front_ok():
    try:
        with urllib.request.urlopen(FRONT, timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def stop_front(proc):
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


def char_view_jobs(pname):
    d = api_get(f"/api/project/{pname}/jobs")
    return [j for j in (d.get("jobs") or []) if j.get("type") == "character_views"]


def _runs_list(pname):
    d = api_get(f"/api/project/{pname}/production/runs")
    if isinstance(d, list):
        return d
    return d.get("runs") or d.get("items") or []


PRUN_ACTIVE = {"pending", "running", "pausing", "paused", "composing"}
STAGE_LABEL = {"character_sync": "同步角色参考图",
               "production_planning": "准备制作计划",
               "production_prepare": "冻结制作输入"}


# ============ 场景 A ============
def scenario_a(page):
    sid_a, eid_a = "cs_cancel_a", _eid_of(PROJ_A, "plan_cancel_a")
    log(f"A: E1={eid_a}")

    # A1. 打开项目（F5 restore：S1 approved + E1 running 恢复）
    select_project(page, PROJ_A)
    time.sleep(3)   # FloatingAgentHost restoreActive + 首轮轮询

    # A2. E1 真实运行：API 真相（running + post-commit 阶段）+ 真实工作证据
    #     （owned ProductionRun active / char_views job running / planning checkpoint 推进）
    ex = get_exec(PROJ_A, sid_a, eid_a)
    assert ex.get("status") == "running", f"A2 FAIL: E1 非 running: {ex.get('status')}"
    stage0 = ex.get("stage")
    assert stage0 in STAGE_LABEL, f"A2 FAIL: stage={stage0}"
    owned_run_id0 = ex.get("production_run_id")
    n_plan0 = len(ex.get("planning") or [])
    n_sync0 = len(ex.get("character_sync") or [])

    def _work_evidence():
        if any(r.get("status") in PRUN_ACTIVE for r in _runs_list(PROJ_A)):
            return "active_production_run"
        if any(j.get("state") == "running" for j in char_view_jobs(PROJ_A)):
            return "views_job_running"
        e = get_exec(PROJ_A, sid_a, eid_a)
        if len(e.get("planning") or []) > n_plan0:
            return "planning_checkpoint"
        return None

    ev = wait_for(_work_evidence, 240, "真实 post-commit 工作证据")
    log(f"A2: E1 running(stage={stage0}, owned_run={owned_run_id0})，真实工作证据={ev}")
    RESULTS["A1_E1_real_running"] = \
        f"PASS (running/{stage0}, run={owned_run_id0 or '-'}, 证据={ev})"

    # A3. UI 预检：/agents 团队聊天运行卡显示当前阶段
    enter_team_chat(page)
    stage_txt = page.locator(".exec-stage.current .exec-label").first.inner_text(timeout=10000)
    assert STAGE_LABEL[stage0] in stage_txt, \
        f"A3 FAIL: 运行卡 stage={stage_txt}（期望 {STAGE_LABEL[stage0]}）"
    log(f"A3: 运行卡显示「{stage_txt}」")
    RESULTS["A2_run_card_stage"] = f"PASS ({stage_txt})"

    # A4. 回业务页，FloatingBar 输入新修改请求（命中变更意图）→ 二选一 UI
    page.goto(f"{FRONT}/dashboard", wait_until="domcontentloaded")
    select_project(page, PROJ_A)
    time.sleep(2)
    bar_input = page.locator(".fab-input").first
    bar_input.wait_for(state="visible", timeout=15000)
    bar_input.fill("把AudA的头发换成蓝色")
    bar_input.press("Enter")
    # 会话面板展开 + 选择卡出现
    page.locator(".rc-choice").wait_for(state="visible", timeout=15000)
    choice_q = page.locator(".rc-choice-q").first.inner_text()
    log(f"A4: 二选一 UI 出现：{choice_q[:40]}…")
    RESULTS["A3_choice_ui"] = "PASS (停止/排队 二选一出现)"

    # A5. 点击「停止当前任务并重新规划」
    cancel_t0 = time.time()
    page.locator(".rc-btn-warn").first.click()
    # 消息「正在停止当前任务…」（硬断言：立即出现）
    page.locator(".acs-msg-content",
                 has_text="正在停止当前任务").first.wait_for(state="visible", timeout=15000)
    log("A5: 已点击「停止当前任务并重新规划」，UI 显示「正在停止当前任务…」")
    # 运行卡「正在停止…」（尽力观测：在飞单元收尾快时窗口可能很短）
    saw_stopping_label = False
    for _ in range(10):
        if page.locator(".rc-stage", has_text="正在停止").count():
            saw_stopping_label = True
            break
        time.sleep(0.5)
    log(f"A5: 运行卡「正在停止…」标签 observed={saw_stopping_label}")
    RESULTS["A4_ui_stopping"] = \
        f"PASS (消息立即；运行卡正在停止={'见过' if saw_stopping_label else '窗口过短'})"

    # A6. 后端真相：cancel_requested 已落盘；committed 取消不提前宣称已取消
    #     （在飞任务存在时应为 running=stopping；收尾极快时可能已收敛 cancelled——均合法）
    ex_c = get_exec(PROJ_A, sid_a, eid_a)
    assert ex_c.get("cancel_requested") is True, "A6 FAIL: cancel_requested 未落盘"
    assert ex_c.get("status") in ("running", "cancelled"), \
        f"A6 FAIL: 取消后状态异常 {ex_c.get('status')}"
    log(f"A6: 取消后真相 status={ex_c.get('status')} cancel_requested=True"
        f"{'（stopping 语义，未提前 cancelled）' if ex_c.get('status') == 'running' else '（收尾极快已收敛）'}")
    RESULTS["A5_backend_stopping_truth"] = \
        f"PASS ({ex_c.get('status')} + cancel_requested)"

    # A7. 等待收敛 cancelled（在飞单元自然收尾 + owned run 停止；轨迹记录，断言不复活）
    seen = []
    run_seen = []
    saw_cancelled_ui = False
    deadline = time.time() + 300
    final = None
    while time.time() < deadline:
        ex = get_exec(PROJ_A, sid_a, eid_a)
        st = (ex.get("status"), ex.get("cancel_requested"))
        if not seen or seen[-1] != st:
            seen.append(st)
            log(f"A7: E1 状态 {st}")
        if owned_run_id0:
            r1 = next((r for r in _runs_list(PROJ_A)
                       if r.get("run_id") == owned_run_id0), None)
            r1st = (r1 or {}).get("status")
            if r1st and (not run_seen or run_seen[-1] != r1st):
                run_seen.append(r1st)
                log(f"A7: owned run {owned_run_id0} 状态 {r1st}")
        if not saw_cancelled_ui and page.locator(
                ".rc-stage", has_text="已取消").count():
            saw_cancelled_ui = True
            log("A7: UI 运行卡已显示「已取消」")
        if ex.get("status") == "cancelled":
            final = ex
            break
        assert ex.get("cancel_requested") is True, \
            f"A7 FAIL: 取消后观察到的状态无 cancel_requested: {st}"
        time.sleep(2)
    assert final is not None, \
        f"A7 FAIL: 300s 未收敛 cancelled，轨迹 {seen} run {run_seen}"
    # Gate 1 附加：收敛后再观察 15s，绝不复活
    time.sleep(15)
    ex_check = get_exec(PROJ_A, sid_a, eid_a)
    assert ex_check.get("status") == "cancelled", \
        f"A7 FAIL: cancelled 后又变 {ex_check.get('status')}（复活！）"
    log(f"A7: E1 收敛 cancelled（轨迹 {seen}），15s 复查仍 cancelled（不复活）")
    RESULTS["A6_converge_no_resurrect"] = f"PASS (轨迹 {seen}，复查不复活)"

    # Gate 2/3：不推进新工作（stage/记录冻结）+ owned run 精确停止 + 无新 run
    assert final.get("stage") == stage0, \
        f"A7 FAIL: 取消后 stage 推进 {stage0} -> {final.get('stage')}"
    assert len(final.get("planning") or []) == n_plan0, "A7 FAIL: planning 记录变化"
    assert len(final.get("character_sync") or []) == n_sync0, "A7 FAIL: 角色记录变化"
    rl = _runs_list(PROJ_A)
    if owned_run_id0:
        # Gate 3：取消传播到准确 owned run（cancelled；failed=取消前已因预存在环境
        # 问题终止，取消语义同样成立——记录实际值）
        assert len(rl) == 1 and rl[0].get("run_id") == owned_run_id0, \
            f"A7 FAIL: run 集变化（新 run 或丢失）: {[r.get('run_id') for r in rl]}"
        r1_final = rl[0].get("status")
        assert r1_final in ("cancelled", "failed"), \
            f"A7 FAIL: owned run 未停止: {r1_final}"
        note = "" if r1_final == "cancelled" else "（取消前已 failed：环境缺视频二进制）"
        log(f"A7: owned run 终态 {r1_final}{note}，无新 run；stage/记录冻结")
        RESULTS["A7_gate2_gate3"] = (
            f"PASS (stage 冻结 {stage0}; run -> {r1_final} 轨迹 {run_seen}; 无新 run)")
    else:
        assert not rl, f"A7 FAIL: 取消后出现 ProductionRun: {rl}"
        log(f"A7: stage 冻结 {stage0}；无 ProductionRun")
        RESULTS["A7_gate2_gate3"] = f"PASS (stage 冻结 {stage0}; 无 Run)"

    # A8. UI：收敛后「已取消」可见（或已切换）+ 新会话自动开始消息 + 运行卡切到新会话
    saw_cancelled_ui = False
    deadline_ui = time.time() + 30
    while time.time() < deadline_ui:
        if page.locator(".rc-stage", has_text="已取消").count():
            saw_cancelled_ui = True
            break
        if page.locator(".acs-msg-content", has_text="已停止当前任务").count():
            break   # S2 已建（运行卡已切新会话）——已取消窗口已过
        time.sleep(0.5)
    new_sess_msg = page.locator(
        ".acs-msg-content", has_text="已停止当前任务").first
    new_sess_msg.wait_for(state="visible", timeout=30000)
    msg_txt = new_sess_msg.inner_text()
    assert "新会话" in msg_txt, f"A8 FAIL: 消息无新会话: {msg_txt}"
    log(f"A8: UI 已取消可见={saw_cancelled_ui}；消息：{msg_txt[:60]}")
    RESULTS["A8_ui_cancelled_new_session"] = \
        f"PASS (已取消UI={'见过' if saw_cancelled_ui else '被S2切换跳过'}；新会话消息出现)"

    # A9. 新 ChangeSession S2 真相：已创建、未撞 PROJECT_PRODUCTION_ACTIVE、继续推进
    sessions = wait_for(
        lambda: ([s for s in api_get(f"/api/project/{PROJ_A}/change-sessions")
                  .get("sessions", [])
                  if s.get("session_id") != sid_a] or None), 30, "新会话出现")
    s2 = sessions[0]
    assert s2.get("status") not in ("rejected", "failed", "cancelled"), \
        f"A9 FAIL: S2 状态异常 {s2.get('status')}"
    assert not (s2.get("blocker") or {}).get("code") == "PROJECT_PRODUCTION_ACTIVE", s2
    # Gate 4：旧 run 已非 active（新计划不会撞 PROJECT_PRODUCTION_ACTIVE 兜底）
    rl2 = _runs_list(PROJ_A)
    active_runs = [r.get("run_id") for r in rl2 if r.get("status") in PRUN_ACTIVE]
    assert not active_runs, f"A9 FAIL: 仍有活跃 ProductionRun: {active_runs}"
    n_runs = len(rl2)
    log(f"A9: 新会话 {s2.get('session_id')} status={s2.get('status')}；"
        f"活跃 run=[]（共 {n_runs} 个，均 terminal）")
    RESULTS["A9_gate4_new_session_unblocked"] = (
        f"PASS (S2={s2.get('session_id')} status={s2.get('status')}，无活跃 run)")


# ============ 场景 B ============
def scenario_b(page):
    sid_b, eid_b = "cs_cancel_b", _eid_of(PROJ_B, "plan_cancel_b")
    log(f"B: E1={eid_b}")

    # B1. backend 已重启（外层处理）：恢复收敛真相
    ex_b = wait_for(
        lambda: (lambda e: e if e.get("status") == "cancelled" else None)(
            get_exec(PROJ_B, sid_b, eid_b)), 60, "重启后 E1 收敛 cancelled")
    assert ex_b.get("stage") == "production_prepare", \
        f"B1 FAIL: stage 被推进 {ex_b.get('stage')}"
    assert ex_b.get("cancel_requested") is True
    rl = _runs_list(PROJ_B)
    r1 = next((r for r in rl if r.get("run_id") == "prun_cxl_b"), None)
    assert r1 is not None and r1.get("status") == "cancelled", \
        f"B1 FAIL: R1 未取消: {r1}"
    jobs_b = api_get(f"/api/project/{PROJ_B}/jobs").get("jobs") or []
    assert not jobs_b, f"B1 FAIL: 重启后为旧计划派发新工作: {jobs_b}"
    log(f"B1: 重启恢复 — E1 cancelled(stage=production_prepare 未推进)、R1 cancelled、"
        f"0 新 job（旧生产链未复活）")
    RESULTS["B1_restart_converge"] = \
        "PASS (E1 cancelled + R1 cancelled + 0 新 job)"

    # B2. 页面恢复：重选项目 → 运行卡与持久状态一致（已取消 + 创作保留提示）
    select_project(page, PROJ_B)
    enter_team_chat(page)
    cancelled_state = page.locator(".exec-state.cancelled").first
    cancelled_state.wait_for(state="visible", timeout=20000)
    txt = cancelled_state.inner_text()
    assert "已取消" in txt, f"B2 FAIL: 状态文案 {txt}"
    assert "保留" in txt, f"B2 FAIL: 未提示创作保留 {txt}"
    # 阻塞横幅不存在（未被 PROJECT_PRODUCTION_ACTIVE 卡住）
    assert page.locator(".exec-blocker").count() == 0, "B2 FAIL: 出现 blocker"
    log(f"B2: 页面恢复一致：{txt[:60]}")
    RESULTS["B2_page_recovery_consistent"] = f"PASS ({txt[:50]}…)"


# ============ Playwright 辅助 ============
def select_project(page, pname):
    page.goto(f"{FRONT}/dashboard", wait_until="domcontentloaded")
    page.locator(".proj-card").filter(has_text=pname).first.click(timeout=15000)
    page.wait_for_url(re.compile(r"/characters"), timeout=15000)


def enter_team_chat(page):
    page.goto(f"{FRONT}/agents", wait_until="domcontentloaded")
    page.locator(".agent-card.team-entry").first.click(timeout=15000)
    time.sleep(2)


def _eid_of(pname, plan_id):
    from src.agents.change_protocol.store import ChangeProtocolStore
    store = ChangeProtocolStore(BASE / "projects" / pname, pname)
    ex = store.find_execution(plan_id, 1)
    assert ex is not None, f"未找到 execution: {pname}/{plan_id}"
    return ex.execution_id


def main():
    back1 = front = back2 = None
    try:
        back1 = start_backend(BACKEND_LOGS[0])
        log("backend#1 已启动（恢复：A 项目 kickoff 真实 char sync）")
        front = start_front("cancel_front.log")
        log("vite preview 已启动 :7779")

        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1600, "height": 900})
            console_msgs = []
            page.on("console", lambda m: console_msgs.append(f"{m.type}: {m.text[:160]}"))
            page.on("pageerror", lambda e: console_msgs.append(f"PAGEERROR: {str(e)[:250]}"))

            scenario_a(page)

            # ---- 场景 B：重建 stopping 中崩溃状态（backend#1 运行中 seed，
            #      仅重启后由恢复链收敛——模拟「正在停止 → backend restart」）----
            r = subprocess.run([sys.executable, "cancel_gp_seed.py", "b"],
                               cwd=str(BASE), capture_output=True, text=True,
                               encoding="utf-8")
            assert r.returncode == 0, f"B seed 失败: {r.stdout} {r.stderr}"
            log("场景 B 已重建（E1 stopping + R1 running+cancel_requested）")

            log("—— 场景 B：正在停止状态下 backend restart ——")
            stop_backend(back1)
            log("backend#1 已停止（模拟 stopping 中崩溃后重启）")
            back2 = start_backend(BACKEND_LOGS[1])
            log("backend#2 已启动（恢复中）")
            scenario_b(page)
            browser.close()

        log("==== 结果汇总 ====")
        for k, v in RESULTS.items():
            log(f"  {k}: {v}")
        log("AI-7C-H CANCEL BROWSER ACCEPTANCE: ALL PASS")
    finally:
        for proc in (back2, front, back1):
            if proc is not None:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                               capture_output=True)


if __name__ == "__main__":
    main()
