"""agnes-video-2.5-flash 真机 REST 全链 smoke（scratch，v2：等批次候选而非 legacy status）。
链路：种子项目 → 真实 Agnes 首帧（imgbb）→ choose →
  shot1: video?video_model=agnes-video-2.5-flash（新契约 keyframe/5s）
  shot2: video（默认 v2.0 回归）
"""
import sys, os, json, time, httpx
sys.path.insert(0, ".")

BASE = "http://localhost:8000"
PROJ = "__video25_smoke"


def post(path, **kw):
    r = httpx.post(f"{BASE}{path}", timeout=60, **kw)
    print(f"POST {path} -> {r.status_code} {r.text[:160]}")
    r.raise_for_status()
    return r.json()


def _proj():
    from src.core.store import ProjectStore
    return ProjectStore(f"projects/{PROJ}").load()


def _latest_batch(shot):
    for b in reversed(shot.first_frame_batches or []):
        if b.candidates:
            return b
    return None


def main():
    from src.core.store import ProjectStore
    if not os.path.exists(f"projects/{PROJ}/output/project.json"):
        __import__("gp_video25_smoke_seed").seed() if False else None
    # 首帧：已有批次则跳过生成
    for sid in ("s01_c01", "s01_c02"):
        if _latest_batch(_proj().get_shot(sid)) is None:
            post(f"/api/project/{PROJ}/shot/{sid}/first-frame", json={"variants": 1})
    # 等批次候选（job done 落 first_frame_batches；legacy first_frame.status 待 choose 才置 done）
    t0 = time.time()
    while time.time() - t0 < 600:
        p = _proj()
        if all(_latest_batch(p.get_shot(sid)) for sid in ("s01_c01", "s01_c02")):
            break
        time.sleep(4)
    else:
        raise TimeoutError("首帧批次超时")
    # choose（跨批次找候选；从最新批次取第一个）
    for sid in ("s01_c01", "s01_c02"):
        p = _proj()
        sh = p.get_shot(sid)
        if sh.first_frame.url_ready:
            print(f"  {sid} 已 choose，跳过")
            continue
        b = _latest_batch(sh)
        cid = b.candidates[0].candidate_id
        post(f"/api/project/{PROJ}/shot/{sid}/first-frame/choose", json={"candidate_id": cid})
    for sid in ("s01_c01", "s01_c02"):
        sh = _proj().get_shot(sid)
        assert sh.first_frame.url_ready, f"{sid} url_ready=False"
        print(f"  {sid} url_ready ok")
    # 视频
    p = _proj()
    if p.get_shot("s01_c01").video.status not in ("done",):
        post(f"/api/project/{PROJ}/shot/s01_c01/video",
             params={"video_model": "agnes-video-2.5-flash"})
    else:
        print("  s01_c01 视频已完成，跳过")
    if p.get_shot("s01_c02").video.status not in ("done",):
        post(f"/api/project/{PROJ}/shot/s01_c02/video")
    else:
        print("  s01_c02 视频已完成，跳过")

    t0 = time.time()
    last = ""
    while time.time() - t0 < 900:
        p = _proj()
        s1, s2 = p.get_shot("s01_c01"), p.get_shot("s01_c02")
        st1, st2 = s1.video.status, s2.video.status
        msg = f"video1(2.5flash)={st1} video2(v2.0)={st2}"
        if msg != last:
            print(f"  {msg} ({int(time.time()-t0)}s)"); last = msg
        if st1 in ("done", "failed") and st2 in ("done", "failed"):
            break
        time.sleep(5)
    else:
        raise TimeoutError("视频生成超时")

    p = _proj()
    s1, s2 = p.get_shot("s01_c01"), p.get_shot("s01_c02")
    assert s1.video.status == "done", f"2.5-flash 视频未完成: {s1.video.status}"
    assert s2.video.status == "done", f"v2.0 视频未完成: {s2.video.status}"
    assert os.path.exists(s1.video.local), s1.video.local
    assert os.path.exists(s2.video.local), s2.video.local
    v1 = [vv for vv in s1.video_versions if vv.model == "agnes-video-2.5-flash" and vv.local]
    v2 = [vv for vv in s2.video_versions if (not vv.model) and vv.local]
    assert v1, f"2.5 VideoVersion 缺失: {[(vv.model, vv.status) for vv in s1.video_versions]}"
    assert v2, f"v2.0 VideoVersion 缺失: {[(vv.model, vv.status) for vv in s2.video_versions]}"
    print("\n== SMOKE PASS ==")
    print(f"  2.5-flash: {s1.video.local}")
    print(f"             seconds={s1.video.seconds_returned} size={s1.video.size_returned} url={ (s1.video.url or '')[:70]}")
    print(f"  v2.0     : {s2.video.local}")
    print(f"             seconds={s2.video.seconds_returned} size={s2.video.size_returned}")
    print(f"  versions : {[(vv.version_id, vv.model, vv.seconds_returned) for vv in s1.video_versions + s2.video_versions]}")


if __name__ == "__main__":
    main()
