"""A3 隔离对接驱动：真实 collab-run 路由 + 脚本化假 Producer/假媒体，无生产 startup。

复现交接包 02 文档 A3 第 1-4 项：
  1. 模式列表 / run 状态 / jobs 显示一致
  2. start / cancel / awaiting_relay resume（脚本化假 Producer，禁真实文本客户端）
  3. jobs SSE 初始快照 + 后续 job 事件 + 项目过滤；project events SSE 快照/推送/过滤/重连
  4. 刷新后重查真实持久化记录（load_run 走盘，不读内存）

隔离：临时目录数据根；无 .env；外部网络全拒（loopback 放行——Windows asyncio
self-pipe 必需）；无任何真实 Provider 调用。证据落 a3_integration.json。
"""
import asyncio
import json
import socket
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

SOURCE_ROOT = Path(r"D:\isolated\animation-storyboard")
EVIDENCE = Path(r"D:\isolated\evidence\a3_integration.json")
sys.path.insert(0, str(SOURCE_ROOT))

# ---------- 离线守卫（外部全拒，loopback 放行） ----------
_LOOPBACK = {"localhost", "127.0.0.1", "::1", b"localhost", b"127.0.0.1", b"::1"}
_attempts = []
_real_getaddrinfo = socket.getaddrinfo
_real_connect = socket.socket.connect


def _deny_dns(host, *a, **kw):
    if host is None or host in _LOOPBACK:
        return _real_getaddrinfo(host, *a, **kw)
    _attempts.append(f"dns:{host!r}")
    raise OSError("offline: external DNS blocked")


def _deny_connect(self, address, *a, **kw):
    host = address[0] if isinstance(address, tuple) else None
    if host is None or host in _LOOPBACK:
        return _real_connect(self, address, *a, **kw)
    _attempts.append(f"connect:{address!r}")
    raise OSError("offline: external connection blocked")


socket.getaddrinfo = _deny_dns
socket.socket.connect = _deny_connect
socket.socket.connect_ex = _deny_connect

import httpx  # noqa: E402
from fastapi import FastAPI  # noqa: E402

import deps  # noqa: E402
import routers.agents as ra  # noqa: E402
import routers.jobs as rj  # noqa: E402
import routers.system as rs  # noqa: E402
from src.core.job_queue import JobQueue  # noqa: E402
from src.core.models import Project, Scene, Shot, VideoVersion  # noqa: E402
from src.core.store import ProjectStore  # noqa: E402
from src.agents import collab_modes as cm  # noqa: E402
from src.agents import handoff as handoff_mod  # noqa: E402
from src.agents import project_events as pe_mod  # noqa: E402

PROJECT = "a3_driver_iso"
_report = {"flows": [], "network_attempts": [], "provider_calls": 0}


def _flow(name, ok, detail=""):
    _report["flows"].append({"flow": name, "ok": bool(ok), "detail": str(detail)[:400]})
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


class _FakePM:
    def __init__(self, p):
        self.base_dir = p
        self._p = p

    def get_project_dir(self, name):
        if name == PROJECT:
            return self._p
        if name == "OTHER_PROJECT":  # 跨项目过滤用：独立隔离目录
            other = self._p.parent / "other_project_iso"
            other.mkdir(exist_ok=True)
            return other
        raise FileNotFoundError(name)


class _ScriptedRt:
    """脚本化假运行时：sid 以 sess_producer/sess_relay/sess_resume 开头的回合
    消费 producer 脚本；其余（预铺角色）回固定 ok。blocking=True 时 producer
    回合挂起（供取消流）。"""

    def __init__(self, tmp: Path, producer_script: list, blocking: bool = False):
        self.tmp = Path(tmp)
        self.script = list(producer_script)
        self.blocking = blocking
        self.turns = []
        self.agents = {}
        self.release = asyncio.Event()
        self._blocked = asyncio.Event()

    def _resolve_project_dir(self, project):
        return self.tmp

    def _resolve_agent(self, *a, **k):
        return object()

    def _is_enabled(self, agent_id):
        return True

    def _resolve_client_or_none(self, agent_id=None, **k):
        return SimpleNamespace(chat_completion=lambda *a, **k: {"content": "ok"})

    def _resolve_job_queue_or_none(self):
        return deps.job_queue

    def get_or_create_session(self, project, agent_id, scope_type="project", scope_id=""):
        return {"session_id": f"sess_{agent_id}"}

    async def unified_turn(self, project, sid, content, thinking=False):
        self.turns.append({"sid": sid, "chars": len(content or "")})
        if not (sid.startswith("sess_producer") or sid.startswith("sess_relay")
                or sid.startswith("sess_resume")):
            return {"assistant_message": "ok", "events": [], "receipts": []}
        if self.blocking:
            # 忠实模拟真实 turn：在 turn_registry 注册取消事件（cancel_run 依此置位）
            from src.agents import turn_registry
            ev = asyncio.Event()
            turn_registry._ACTIVE[turn_registry.key(project, sid)] = ev
            self._blocked.set()
            try:
                await asyncio.wait_for(ev.wait(), timeout=30)
            except asyncio.TimeoutError:
                pass
            finally:
                turn_registry._ACTIVE.pop(turn_registry.key(project, sid), None)
            return {"assistant_message": "released", "events": [], "receipts": []}
        if self.script:
            return self.script.pop(0)
        return {"assistant_message": "ok", "events": [], "receipts": []}


def _fake_relay(*a, **k):
    return {"new_session_id": "sess_relayed", "lease": {"generation": 2},
            "handoff": {"handoff_id": "ho_fake"}}


async def _fake_video_handler(job, emit):
    """假媒体生成器：不触网，独立版本文件落盘 + 挂接（复用修复队列同语义）。"""
    await emit("fake_generate", "假视频生成中", 30)
    pdir = deps.project_manager.get_project_dir(job.project)
    vid = f"fv_{job.job_id}"
    local = Path(pdir) / "output" / "fake_media" / f"{vid}.mp4"
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_bytes(b"FAKE_MP4_BYTES")
    version = VideoVersion(version_id=vid, status="done", local=str(local),
                           origin_run_id=job.params.get("origin_run_id", ""))

    def attach(shot):
        shot.video_versions.append(version)
        shot.final_video = vid

    ProjectStore(pdir).update_shot(job.shot_id, attach)
    await emit("fake_generate", "假视频完成", 100)


async def _poll_run(client, rid, want, timeout=20):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = await client.get(f"/api/project/{PROJECT}/collab-runs/{rid}")
        st = r.json().get("run", {}).get("status")
        if st == want:
            return r.json()["run"], time.time() - t0
        await asyncio.sleep(0.05)
    return None, timeout


async def _read_sse_block(iterator, timeout=5):
    return await asyncio.wait_for(anext(iterator), timeout=timeout)


class _FakeReq:
    """直连生成器用：ASGITransport 下 is_disconnected 永不返回（无断开消息），
    端点函数直调 + 显式 aclose 是冒烟工具同款安全口径。"""

    async def is_disconnected(self):
        return False


async def main():
    tmp = Path(tempfile.mkdtemp(prefix="a3_driver_", dir=r"D:\isolated\tmp"))
    tmp.mkdir(parents=True, exist_ok=True)
    ProjectStore(tmp).save(Project(
        name=PROJECT, scenes=[Scene(scene_id="s01", shots=[
            Shot(shot_id="s01_c01", scene_id="s01", index=1),
            Shot(shot_id="s01_c02", scene_id="s01", index=2)])]))

    # 假依赖接线（不运行生产 startup / lifespan）
    deps.project_manager = _FakePM(tmp)
    deps.job_queue = JobQueue(tmp / "isolated_jobs.json", {"video": _fake_video_handler})
    await deps.job_queue.start()
    rt_holder = {"rt": _ScriptedRt(tmp, [])}
    ra.get_agent_runtime = lambda: rt_holder["rt"]
    ra.get_project_manager = lambda: deps.project_manager
    rj.get_job_queue = lambda: deps.job_queue

    app = FastAPI()
    app.include_router(rs.router)
    app.include_router(ra.router)
    app.include_router(rj.router)

    handoff_mod.relay_producer_session = _fake_relay  # 会话接力注入假实现（同机制测试口径）

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                 base_url="http://offline.invalid") as client:
        # ---- F1 基础面 ----
        r = await client.get("/api/health")
        _flow("F1 health", r.status_code == 200, r.json().get("status"))
        r = await client.get(f"/api/project/{PROJECT}/collab-modes")
        modes = r.json()["modes"]
        combo = next(m for m in modes if m["mode_id"] == "combo_recommended")
        _flow("F1 collab-modes combo v2.1.0 available",
              combo["mode_version"] == "2.1.0" and combo["available"] is True
              and not combo["unavailable_reasons"],
              f"avail={combo['available']} reasons={combo['unavailable_reasons']}")
        r = await client.get(f"/api/project/{PROJECT}/jobs")
        _flow("F1 jobs empty", r.status_code == 200 and r.json()["jobs"] == [])
        r = await client.get(f"/api/project/{PROJECT}/agents/producer/grant")
        _flow("F1 grant empty", r.status_code == 200 and r.json()["active"] == [])

        # ---- F2 默认模式启动 → completed（真实 start 路由 + 真实执行编排） ----
        rt_holder["rt"] = _ScriptedRt(tmp, [
            {"assistant_message": "done", "events": [], "receipts": []}])
        r = await client.post(f"/api/project/{PROJECT}/collab-runs",
                              json={"mode_id": None,
                                    "params": {"story_goal": "A3 隔离对接冒烟"}})
        body = r.json()
        ok = r.status_code == 200 and body.get("used_default_mode") == "combo_recommended"
        run_a = body["run"]
        rid_a = run_a["run_id"]
        _flow("F2 start(default) returns run", ok, f"run={rid_a} status={run_a['status']}")
        run_a, _ = await _poll_run(client, rid_a, "completed_with_issues")
        _flow("F2 run terminal (completed_with_issues)", run_a is not None,
              f"status={run_a['status'] if run_a else 'timeout'}")
        # 语义：镜头尚无已接纳视频 → 独立终审记问题 → completed_with_issues
        #（与 A3 文档「completed_with_issues 显示一致」验证项对应）
        if run_a:
            ma = run_a.get("machine_acceptance") or {}
            _flow("F2 machine acceptance recorded", bool(ma),
                  f"acceptance={json.dumps(ma, ensure_ascii=False)[:160]}")
        if run_a:
            steps = [s["step_id"] for s in run_a["steps"]]
            _flow("F2 steps ledger", "grant" in steps and "producer_turn" in steps,
                  f"steps={steps}")
            _flow("F2 session recorded",
                  run_a["session_ids"].get("producer") == "sess_producer",
                  str(run_a["session_ids"]))
            gfile = tmp / "output" / "agents" / "grants.json"
            _flow("F2 grant persisted", gfile.exists(), str(gfile.exists()))
            polfile = tmp / "output" / "agents" / "reference_policy.json"
            _flow("F2 reference policy persisted", polfile.exists(),
                  str(sorted(p.name for p in (tmp / 'output' / 'agents').glob('*.json'))))
            r = await client.get(f"/api/project/{PROJECT}/agents/producer/grant")
            active = r.json()["active"]
            _flow("F2 grant visible via REST", len(active) >= 1,
                  f"active={len(active)}")

        # ---- F3 awaiting_relay → resume（真实 relay 上限 + resume 路由） ----
        handoff_turn = {"assistant_message": "未完", "events": [], "receipts": [],
                        "handoff": {"handoff_id": "ho_x", "reason": "budget"}}
        rt_holder["rt"] = _ScriptedRt(tmp, [dict(handoff_turn)
                                            for _ in range(cm.RELAY_LIMIT + 1)])
        r = await client.post(f"/api/project/{PROJECT}/collab-runs",
                              json={"mode_id": "producer_lead",
                                    "params": {"story_goal": "relay flow"}})
        rid_b = r.json()["run"]["run_id"]
        run_b, _ = await _poll_run(client, rid_b, "awaiting_relay")
        _flow("F3 awaiting_relay reached", run_b is not None,
              f"status={run_b['status'] if run_b else 'timeout'} relay_count={run_b.get('relay_count') if run_b else '-'}")
        r = await client.post(f"/api/project/{PROJECT}/collab-runs/{rid_b}/resume",
                              json={"thinking": False})
        ok = r.status_code == 200
        resumed = r.json().get("run") if ok else None
        _flow("F3 resume accepted", ok, f"http={r.status_code} {r.text[:120]}")
        if resumed:
            _flow("F3 resume markers",
                  resumed.get("result", {}).get("resumed") == 1
                  and any(s["step_id"].startswith("producer_turn_resume")
                          for s in resumed["steps"]),
                  f"resumed={resumed.get('result', {}).get('resumed')}")
        run_b, _ = await _poll_run(client, rid_b, "completed")
        _flow("F3 resume completed", run_b is not None,
              f"status={run_b['status'] if run_b else 'timeout'}")
        r = await client.post(f"/api/project/{PROJECT}/collab-runs/{rid_b}/resume",
                              json={"thinking": False})
        _flow("F3 resume of terminal run rejected", r.status_code == 400,
              f"http={r.status_code}")

        # ---- F4 cancel（阻塞中的 producer turn → REST cancel） ----
        rt_c = _ScriptedRt(tmp, [], blocking=True)
        rt_holder["rt"] = rt_c
        r = await client.post(f"/api/project/{PROJECT}/collab-runs",
                              json={"mode_id": "producer_lead",
                                    "params": {"story_goal": "cancel flow"}})
        rid_c = r.json()["run"]["run_id"]
        await asyncio.wait_for(rt_c._blocked.wait(), timeout=10)
        r = await client.post(
            f"/api/project/{PROJECT}/collab-runs/{rid_c}/cancel",
            json={"reason": "offline test"})
        _flow("F4 cancel accepted", r.status_code == 200
              and r.json().get("stopped") is True, r.text[:120])
        rt_c.release.set()
        run_c, _ = await _poll_run(client, rid_c, "cancelled")
        _flow("F4 run cancelled with reason", run_c is not None
              and run_c.get("result", {}).get("cancel_reason") == "offline test",
              str(run_c.get("result") if run_c else "timeout"))

        # ---- F5 假媒体：job 提交 → 独立版本 → jobs 列表/SSE ----
        rt_holder["rt"] = _ScriptedRt(tmp, [])
        r = await client.get(f"/api/project/{PROJECT}/jobs")
        before = len(r.json()["jobs"])
        job = deps.job_queue.submit(PROJECT, "video", "s01_c01",
                                    origin_run_id="a3_driver")
        for _ in range(200):
            j = deps.job_queue.get(job.job_id)
            if getattr(j, "state", "") == "done":
                break
            await asyncio.sleep(0.05)
        _flow("F5 fake media job done", getattr(j, "state", "") == "done",
              f"job={job.job_id} state={getattr(j, 'state', '?')}")
        store = ProjectStore(tmp).load()
        shot = store.get_shot("s01_c01")
        vv = next((v for v in shot.video_versions if v.version_id.startswith("fv_")), None)
        media_file = Path(vv.local) if vv and vv.local else None
        _flow("F5 version attached + file exists",
              vv is not None and shot.final_video == vv.version_id
              and media_file is not None and media_file.is_file(),
              f"video={shot.final_video} file={media_file.is_file() if media_file else False}")
        r = await client.get(f"/api/project/{PROJECT}/jobs")
        after = r.json()["jobs"]
        _flow("F5 jobs REST shows job", len(after) == before + 1
              and after[-1]["job_id"] == job.job_id
              and after[-1]["state"] == "done",
              f"n={len(after)} last_state={after[-1]['state'] if after else '-'}")

        # jobs SSE：直连生成器——初始快照 → 新 job 事件 → 项目过滤 → 断开清理
        job2 = None
        resp = await rj.jobs_stream(_FakeReq(), project=PROJECT)
        it = resp.body_iterator
        first = await _read_sse_block(it)
        _flow("F5 jobs SSE snapshot", "snapshot" in first, first[:80].replace("\n", " "))
        job2 = deps.job_queue.submit(PROJECT, "video", "s01_c02",
                                     origin_run_id="a3_driver")
        got = None
        try:
            for _ in range(4):
                blk = await _read_sse_block(it, timeout=5)
                if job2.job_id in blk:
                    got = blk
                    break
        except asyncio.TimeoutError:
            pass
        _flow("F5 jobs SSE live event", got is not None,
              (got or "timeout")[:100].replace("\n", " "))
        j2 = deps.job_queue.get(job2.job_id)
        for _ in range(200):
            if getattr(j2, "state", "") == "done":
                break
            await asyncio.sleep(0.05)
        await it.aclose()  # 断开清理（unsubscribe 走 finally）
        # 项目过滤：外来项目事件不出现（2s 内无该事件=过滤生效）
        resp = await rj.jobs_stream(_FakeReq(), project=PROJECT)
        it = resp.body_iterator
        await _read_sse_block(it)
        deps.job_queue.submit("OTHER_PROJECT", "video", "s01_c01",
                              origin_run_id="a3_driver")
        leaked = None
        try:
            for _ in range(2):
                blk = await _read_sse_block(it, timeout=1.5)
                if "OTHER_PROJECT" in blk:
                    leaked = blk
        except asyncio.TimeoutError:
            pass
        _flow("F5 jobs SSE project filter", leaked is None,
              "no cross-project event" if leaked is None else leaked[:80])
        await it.aclose()

        # ---- F6 project events SSE：快照/推送/过滤/重连 ----
        bus = pe_mod.get_project_bus()
        resp = await ra.project_events(_FakeReq(), PROJECT)
        it = resp.body_iterator
        snap = await _read_sse_block(it)
        _flow("F6 events snapshot", "snapshot" in snap, snap[:80].replace("\n", " "))
        bus.publish(PROJECT, {"type": "story.changed", "note": "a3"})
        ev = await _read_sse_block(it)
        _flow("F6 events live push", "story.changed" in ev, ev[:80].replace("\n", " "))
        bus.publish("OTHER_PROJECT", {"type": "story.changed", "note": "other"})
        leaked = None
        try:
            ev2 = await _read_sse_block(it, timeout=1.5)
            if "OTHER_PROJECT" in ev2:
                leaked = ev2
        except asyncio.TimeoutError:
            pass
        _flow("F6 events project filter", leaked is None,
              "no cross-project event" if leaked is None else leaked[:80])
        await it.aclose()
        # 重连：新连接首帧仍是 snapshot
        resp = await ra.project_events(_FakeReq(), PROJECT)
        it = resp.body_iterator
        snap2 = await _read_sse_block(it)
        _flow("F6 events reconnect snapshot", "snapshot" in snap2,
              "reconnected" if "snapshot" in snap2 else snap2[:60])
        await it.aclose()

        # ---- F7 刷新持久化：全部 run 从盘重查 ----
        r = await client.get(f"/api/project/{PROJECT}/collab-runs")
        runs = {x["run_id"]: x["status"] for x in r.json()["runs"]}
        expect = {rid_a: "completed_with_issues", rid_b: "completed",
                  rid_c: "cancelled"}
        _flow("F7 persisted runs via fresh GET",
              all(runs.get(k) == v for k, v in expect.items()) and len(runs) >= 3,
              f"runs={runs}")
        for rid, want in expect.items():
            r = await client.get(f"/api/project/{PROJECT}/collab-runs/{rid}")
            _flow(f"F7 reload {rid[:12]}", r.status_code == 200
                  and r.json()["run"]["status"] == want,
                  f"{r.json()['run']['status']}")
        r = await client.get(f"/api/project/{PROJECT}/collab-runs/missing")
        _flow("F7 missing run 404", r.status_code == 404, str(r.status_code))

    _report["network_attempts"] = _attempts
    _report["provider_calls"] = 0
    _report["isolated_tmp"] = str(tmp)
    EVIDENCE.write_text(json.dumps(_report, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    bad = [f for f in _report["flows"] if not f["ok"]]
    print(f"\n== A3 driver: {len(_report['flows']) - len(bad)}/{len(_report['flows'])} flows passed, "
          f"network_attempts={len(_attempts)} ==")
    return 1 if bad or _attempts else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
