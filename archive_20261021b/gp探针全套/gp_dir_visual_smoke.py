# -*- coding: utf-8 -*-
"""真机 smoke：Director Visual Production（2026-08-31）。

A. 批量图片：s02_c01..c04 各生成一张首帧（真机 Agnes 图片 ×4）。
B. 单视频：s02_c02 生成视频（真机 Agnes 视频 ×1）。
C. 停止/锁释放：s03_c01..c04 批量生成中途取消 → 锁释放 + 已完成资产保留。
D. 整体重设保留 shot_id：s02「太平了，重新设计得更有张力」→ 期望 update 不 delete、
   已生成图片批次保留；story/character canonical 字节级不变。
E. SSE 事件序列：resource.locked → storyboard.changed → resource.unlocked。

结果同时打印与写入 _smoke_visual.txt。
"""
import asyncio
import hashlib
import json
import sys
import threading
import time

import httpx

BASE = "http://localhost:8000"
PROJECT = "Director冒烟测试"
PJ = f"projects/{PROJECT}/output/project.json"

OUT = []
def say(msg=""):
    print(msg)
    OUT.append(str(msg))


def sha(s) -> str:
    return hashlib.sha256(json.dumps(s, ensure_ascii=False, sort_keys=True)
                          .encode("utf-8")).hexdigest()[:16]


def project_state():
    d = json.load(open(PJ, encoding="utf-8"))
    shots = {}
    for sc in d.get("scenes", []):
        for sh in sc.get("shots", []):
            shots[sh["shot_id"]] = sh
    return d, shots


def domain_hashes():
    d, _ = project_state()
    return {"story_text": sha(d.get("story_text", "")),
            "scenes_text": sha([(sc.get("scene_id"), sc.get("summary"), sc.get("characters"))
                                for sc in d.get("scenes", [])]),
            "characters": sha(d.get("characters", []))}


def batch_count(shots, sid=None):
    n = 0
    for k, sh in shots.items():
        if sid and not k.startswith(sid):
            continue
        n += len(sh.get("first_frame_batches") or [])
    return n


async def watch_events(stop: asyncio.Event, seen: list):
    async with httpx.AsyncClient(timeout=700) as c:
        async with c.stream("GET", f"{BASE}/api/project/{PROJECT}/events") as resp:
            async for line in resp.aiter_lines():
                if stop.is_set():
                    return
                if not line.startswith("data: "):
                    continue
                try:
                    ev = json.loads(line[6:])
                except Exception:
                    continue
                t = ev.get("type")
                if t in ("resource.locked", "resource.unlocked", "storyboard.changed"):
                    seen.append((t, ev.get("resource") or ev.get("operation"),
                                 round(time.time(), 1)))
                    print(f"  [bus] {t} {ev.get('resource') or ev.get('operation')}")


async def run_turn(client: httpx.AsyncClient, sid: str, content: str,
                   cancel_after: float | None = None) -> tuple:
    """消费 turn 流，返回 (final_result, tool_progress_events)。

    语义不活跃看门狗（2026-08-31）：INACTIVITY 秒内没有收到任何真实
    Agent/tool/progress/completed 事件（keepalive/注释/空行不重置计时），
    就 POST /turn/cancel 结束当前回合，宽限 GRACE 秒等收尾，然后有限重试
    （MAX_ATTEMPTS 次）。同会话 turn 互斥（409）：重试前用 /turn/cancel
    探测会话是否空闲（返回 stopped=False 即无活动任务）。不无限重试。"""
    INACTIVITY = 420   # 大 tool_call（update_many 数千字参数）静默期也可能几分钟，取 7 分钟
    GRACE = 300        # 看门狗触发后等待后端收尾（后端自身看门狗 360s 会兜底打断挂死流）
    MAX_ATTEMPTS = 2

    async def _attempt() -> tuple:
        progresses = []
        final = None
        url = f"{BASE}/api/project/{PROJECT}/agents/sessions/{sid}/turn/stream"
        async with client.stream("POST", url,
                                 json={"content": content, "thinking": False},
                                 timeout=httpx.Timeout(700, connect=30)) as resp:
            if resp.status_code == 409:
                say("  [busy] 会话仍有任务在跑（409），稍候重试")
                return "BUSY", progresses
            t0 = time.time()
            cancelled = False
            wd_fired = False
            deadline = None
            last_act = time.monotonic()
            it = resp.aiter_lines().__aiter__()
            while True:
                if wd_fired:
                    remaining = deadline - time.monotonic()
                else:
                    remaining = last_act + INACTIVITY - time.monotonic()
                try:
                    if remaining <= 0:
                        raise asyncio.TimeoutError
                    line = await asyncio.wait_for(it.__anext__(), timeout=max(remaining, 0.1))
                except StopAsyncIteration:
                    break
                except asyncio.TimeoutError:
                    if wd_fired:
                        say("  [watchdog] 宽限期仍无收尾事件，放弃本回合")
                        break
                    wd_fired = True
                    deadline = time.monotonic() + GRACE
                    say(f"  [watchdog] {INACTIVITY}s 无真实事件（keepalive 不重置计时），"
                        "发送 /turn/cancel 并等待收尾")
                    try:
                        await client.post(
                            f"{BASE}/api/project/{PROJECT}/agents/sessions/{sid}/turn/cancel",
                            timeout=30)
                    except Exception as e:
                        say(f"  [cancel] 失败: {e}")
                    continue
                except Exception as e:
                    # 看门狗取消后 httpx 行迭代器可能不可恢复，直接放弃本回合
                    say(f"  [stream] 读取中断: {type(e).__name__}: {str(e)[:120]}")
                    break
                if cancel_after is not None and not cancelled and time.time() - t0 > cancel_after:
                    cancelled = True
                    try:
                        await client.post(
                            f"{BASE}/api/project/{PROJECT}/agents/sessions/{sid}/turn/cancel",
                            timeout=30)
                        say("  [cancel] 已发送 /turn/cancel")
                    except Exception as e:
                        say(f"  [cancel] 失败: {e}")
                if not line.startswith("data: "):
                    continue   # keepalive/注释行：不重置语义不活跃计时
                try:
                    ev = json.loads(line[6:])
                except Exception:
                    continue
                last_act = time.monotonic()   # 真实事件才重置
                t = ev.get("type")
                if t == "tool.started":
                    say(f"  [tool] {ev.get('label')} ({ev.get('name')})")
                elif t == "tool.progress":
                    progresses.append(ev.get("message"))
                    say(f"  [prog] {ev.get('message')}")
                elif t == "tool.completed":
                    say(f"  -> ok={ev.get('ok')} {ev.get('summary')}")
                elif t == "tool.failed":
                    say(f"  -> FAILED {ev.get('error')}")
                elif t == "turn.completed":
                    final = ev.get("result")
                elif t == "turn.failed":
                    say(f"  turn.failed: {ev.get('error')}")
        return final, progresses

    async def _wait_session_free():
        """等上一回合真正结束（后端 _ACTIVE_TURN_EVENTS 清除）。/turn/cancel 在
        没有活动任务时返回 stopped=False，以此作为空闲探测；有活动任务则顺带再次
        请求取消。最多等 15 分钟，不无限等。"""
        for _ in range(45):
            try:
                r = await client.post(
                    f"{BASE}/api/project/{PROJECT}/agents/sessions/{sid}/turn/cancel",
                    timeout=30)
                if not r.json().get("stopped"):
                    return
            except Exception:
                pass
            await asyncio.sleep(20)
        say("  [busy] 等待会话空闲超时（15 分钟）")

    for attempt in range(1, MAX_ATTEMPTS + 1):
        final, progresses = await _attempt()
        if final is not None and final != "BUSY":
            return final, progresses
        if final != "BUSY":
            say(f"  [watchdog] 第 {attempt}/{MAX_ATTEMPTS} 次尝试未得到结果"
                f"{'，重试' if attempt < MAX_ATTEMPTS else '，放弃'}")
        await _wait_session_free()
    return None, []


def print_meta(final):
    if not final:
        say("  (no final)")
        return
    meta = (final.get("message") or {}).get("meta") or {}
    msg = final.get("message") or {}
    say(f"  status={msg.get('status')} write_success={meta.get('write_success')}"
        f"/{meta.get('write_attempts')} generated_assets={len(meta.get('generated_assets') or [])}")
    for r in meta.get("receipts", []):
        say(f"  receipt {r.get('operation')} ok={r.get('ok')} verified={r.get('verified')}"
            f" cancelled={r.get('cancelled')} count={r.get('count')}")
        for it in (r.get("results") or [])[:8]:
            say(f"    {it.get('shot_id')} {it.get('frame')} {it.get('status')}"
                f" ok={it.get('ok')} {('err=' + str(it.get('error'))[:60]) if it.get('error') else ''}")
    say("  assistant: " + (final.get("assistant_message") or "")[:220].replace("\n", " "))


async def main():
    results = []
    only = sys.argv[1].upper() if len(sys.argv) > 1 else None   # A/B/C/D/E 单场景重跑

    def want(x: str) -> bool:
        return only is None or only == x

    def check(name, ok, detail=""):
        results.append((name, ok, detail))
        say(f"  [{'PASS' if ok else 'FAIL'}] {name} {detail}")

    async with httpx.AsyncClient(timeout=700) as c:
        r = await c.post(f"{BASE}/api/project/{PROJECT}/agents/sessions",
                         json={"agent_id": "director", "scope_type": "project", "scope_id": PROJECT})
        sid = r.json()["session_id"]
        say(f"session={sid}")

        stop = asyncio.Event()
        seen = []
        watcher = asyncio.ensure_future(watch_events(stop, seen))
        await asyncio.sleep(0.5)

        # ---------- A. 批量图片（真机 ×4） ----------
        if want("A"):
            say("\n=== A. 批量图片 s02_c01..c04 ===")
            d0, s0 = project_state()
            h_before_shots = batch_count(s0, "s02")
            t0 = time.time()
            final_a, prog_a = await run_turn(c, sid, "给故事段 s02 的前四个镜头（s02_c01 到 s02_c04）各生成一张首帧图，每个镜头一张就够。")
            say(f"  turn A 耗时 {time.time()-t0:.0f}s, progress 条数 {len(prog_a)}")
            print_meta(final_a)
            d1, s1 = project_state()
            gen_files = 0
            for k in ("s02_c01", "s02_c02", "s02_c03", "s02_c04"):
                sh = s1.get(k) or {}
                ok_batch = [b for b in (sh.get("first_frame_batches") or [])
                            if any((cand.get("local")) for cand in (b.get("candidates") or []))]
                for b in ok_batch:
                    for cand in b["candidates"]:
                        import os
                        if cand.get("local") and os.path.exists(cand["local"]):
                            gen_files += 1
            check("A1 批量回执 verified", bool(
                [r for r in ((final_a or {}).get("message", {}).get("meta", {}).get("receipts") or [])
                 if r.get("operation") == "shot.generate_images" and r.get("ok") and r.get("verified")]))
            check("A2 4 镜均有落盘首帧文件", gen_files >= 4, f"files={gen_files}")
            check("A3 有 tool.progress 进度事件", len(prog_a) >= 1)
            check("A4 storyboard 锁事件成对", any(e[0] == "resource.locked" for e in seen)
                  and any(e[0] == "resource.unlocked" for e in seen))
            locks = (await c.get(f"{BASE}/api/project/{PROJECT}/resource-locks")).json().get("locks", [])
            check("A5 turn 结束锁已释放", not locks, f"locks={locks}")

        # ---------- B. 单视频（真机 ×1） ----------
        if want("B"):
            say("\n=== B. 单视频 s02_c02 ===")
            t0 = time.time()
            final_b, prog_b = await run_turn(c, sid, "给镜头 s02_c02 生成视频。")
            say(f"  turn B 耗时 {time.time()-t0:.0f}s")
            print_meta(final_b)
            d2, s2 = project_state()
            sh2 = s2.get("s02_c02") or {}
            import os
            vid_local = None
            for vv in (sh2.get("video_versions") or []):
                if vv.get("local") and os.path.exists(vv["local"]):
                    vid_local = vv["local"]
            check("B1 视频回执 verified", bool(
                [r for r in ((final_b or {}).get("message", {}).get("meta", {}).get("receipts") or [])
                 if r.get("operation") == "shot.generate_videos" and r.get("ok") and r.get("verified")]))
            check("B2 视频文件落盘且 final_video 指向", bool(vid_local) and bool(sh2.get("final_video")),
                  f"local={vid_local}")

        # ---------- C. 停止 → 锁释放 + 部分保留 ----------
        if want("C"):
            say("\n=== C. 批量生成中途停止（s03_c01..c04） ===")
            _, _sc0 = project_state()          # 单场景重跑时自取状态，不依赖 B 段变量
            n_batches_c0 = batch_count(_sc0, "s03")
            t0 = time.time()
            final_c, _ = await run_turn(c, sid, "给故事段 s03 的前四个镜头（s03_c01 到 s03_c04）各生成一张首帧图。",
                                        cancel_after=60)
            say(f"  turn C 耗时 {time.time()-t0:.0f}s")
            print_meta(final_c)
            d3, s3 = project_state()
            n_batches_c1 = batch_count(s3, "s03")
            locks = (await c.get(f"{BASE}/api/project/{PROJECT}/resource-locks")).json().get("locks", [])
            check("C1 停止后锁释放", not locks, f"locks={locks}")
            check("C2 已完成资产保留", n_batches_c1 >= n_batches_c0,
                  f"s03 批次 {n_batches_c0} -> {n_batches_c1}")
            check("C3 收尾状态 stopped 或如实汇报",
                  bool(final_c) and ((final_c.get("message") or {}).get("status") == "stopped"
                                     or "取消" in (final_c.get("assistant_message") or "")
                                     or "停止" in (final_c.get("assistant_message") or "")))

        # ---------- D. 整体重设保留 shot_id ----------
        if want("D"):
            say("\n=== D. 整体重设 s02（期望 update_many，不 delete） ===")
            _, _sd0 = project_state()          # 单场景重跑时自取状态，不依赖 C 段变量
            ids_before = [k for k in _sd0 if k.startswith("s02")]
            h_before = domain_hashes()
            batches_before = {k: len(_sd0[k].get("first_frame_batches") or []) for k in ids_before}
            t0 = time.time()
            final_d, _ = await run_turn(c, sid, "s02 这组镜头太平了，整体重新设计得更有张力。")
            say(f"  turn D 耗时 {time.time()-t0:.0f}s")
            print_meta(final_d)
            d4, s4 = project_state()
            ids_after = [k for k in s4 if k.startswith("s02")]
            h_after = domain_hashes()
            meta_d = (final_d or {}).get("message", {}).get("meta", {})
            ops = [r.get("operation") for r in (meta_d.get("receipts") or [])]
            check("D1 无 delete（update 优先）", "shot.delete" not in ops, f"ops={ops}")
            check("D2 shot_id 集合保持", set(ids_before) == set(ids_after),
                  f"before={sorted(ids_before)} after={sorted(ids_after)}")
            check("D3 已生成图片批次保留",
                  all((len(s4.get(k, {}).get("first_frame_batches") or [])) >= v
                      for k, v in batches_before.items()),
                  f"before={batches_before}")
            check("D4 story/character canonical 字节不变",
                  h_before == h_after, f"before={h_before} after={h_after}")
            check("D5 有真实 update 回执（verified）",
                  bool([r for r in (meta_d.get("receipts") or [])
                        if r.get("operation") in ("shot.update_many", "shot.update")
                        and r.get("ok") and r.get("verified")]))

        stop.set()
        await asyncio.gather(watcher, return_exceptions=True)

        # ---------- E. SSE 事件序列 ----------
        if want("E"):
            say("\n=== E. 项目事件序列（锁定→changed→解锁） ===")
            seq = [e[0] for e in seen]
            changed_after_lock = False
            locked_seen = unlocked_seen = False
            for e in seq:
                if e == "resource.locked":
                    locked_seen = True
                elif e == "storyboard.changed" and locked_seen:
                    changed_after_lock = True
                elif e == "resource.unlocked" and locked_seen:
                    unlocked_seen = True
            check("E1 locked→changed→unlocked 序列出现", locked_seen and changed_after_lock and unlocked_seen,
                  f"n_events={len(seq)}")

    say("\n===== SMOKE SUMMARY =====")
    all_ok = True
    for name, ok, detail in results:
        all_ok &= ok
        say(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")
    say(f"OVERALL: {'ALL PASS' if all_ok else 'HAS FAILURES'}")


if __name__ == "__main__":
    _only = sys.argv[1] if len(sys.argv) > 1 else None
    _out = f"_smoke_visual_{_only}.txt" if _only else "_smoke_visual.txt"
    try:
        asyncio.run(main())
    finally:
        with open(_out, "w", encoding="utf-8") as f:
            f.write("\n".join(OUT))
