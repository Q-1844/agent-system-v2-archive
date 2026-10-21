# -*- coding: utf-8 -*-
"""探针：直接用 AgnesClient.chat_completion_stream + 完整 DIRECTOR_TOOLS，
验证新增 shot.generate_images schema 是否导致 GLM function-calling 挂起/拒答。"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, ".")
# 加载 .env（与 api_server.py 同逻辑）
_env = Path(".env")
if _env.exists():
    for _line in _env.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

from src.pipeline.controller import PipelineController  # noqa: E402


async def main():
    client = PipelineController().agnes_client
    from src.agents.director import DIRECTOR_TOOLS, DIRECTOR_SYSTEM

    messages = [
        {"role": "system", "content": DIRECTOR_SYSTEM.format(
            project_name="Director冒烟测试", scenes_count=3, shots_count=16,
            max_create_batch=10, max_update_batch=12)},
        {"role": "user", "content": "给镜头 s02_c01 生成一张首帧图。"},
    ]
    t0 = time.time()
    buf_content = []
    tool_names = []
    try:
        async def consume():
            async for ev in client.chat_completion_stream(
                    messages, temperature=0.7, max_tokens=65536,
                    thinking=False, tools=DIRECTOR_TOOLS, tool_choice="auto"):
                k = ev.get("kind")
                if k == "content_delta":
                    buf_content.append(ev["delta"])
                elif k == "tool_call_pending":
                    tool_names.append(ev.get("name"))
                    print(f"[{time.time()-t0:.0f}s] tool_call_pending: {ev.get('name')}")
                elif k == "finish":
                    print(f"[{time.time()-t0:.0f}s] finish")
        await asyncio.wait_for(consume(), timeout=240)
    except asyncio.TimeoutError:
        print(f"[{time.time()-t0:.0f}s] TIMEOUT 240s —— 流挂起")
    except Exception as e:
        print(f"[{time.time()-t0:.0f}s] EXC {type(e).__name__}: {str(e)[:200]}")
    print("tool_names:", tool_names)
    text = "".join(buf_content)
    print("content head:", text[:400].replace("\n", " "))


if __name__ == "__main__":
    asyncio.run(main())
