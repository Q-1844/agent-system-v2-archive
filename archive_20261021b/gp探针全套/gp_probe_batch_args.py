# scratch 探针：真 Agnes 流式下，模型用 story.create_many 发【大参数】时
# 聚合出的 tool_call.arguments 到底是什么（定位 "scenes 必须是非空数组"）。
import asyncio
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from src.pipeline.controller import PipelineController
from src.agents.script_writer import SCRIPT_WRITER_TOOLS


async def main():
    ctrl = PipelineController()
    client = ctrl.agnes_client

    messages = [
        {"role": "system", "content": (
            "你是剧本助手。请直接调用工具 story.create_many 一次性创建 3 个故事段，"
            "每段 summary 必须是约 300 字的中文故事正文（内容丰富、含对话引号），"
            "characters 传空数组，expected_scenes_revision 传 'abcd1234'。"
            "不要解释，直接发工具调用。")},
        {"role": "user", "content": "开始创建，3 段，每段 300 字左右。"},
    ]

    finish = None
    async for ev in client.chat_completion_stream(
            messages, temperature=0.7, max_tokens=65536,
            thinking=False, tools=SCRIPT_WRITER_TOOLS, tool_choice="auto"):
        if ev["kind"] == "finish":
            finish = ev

    tcs = finish.get("tool_calls") if finish else None
    print("finish reason:", finish.get("reason") if finish else None)
    print("tool_calls count:", len(tcs) if tcs else 0)
    if not tcs:
        print("content:", (finish.get("content") or "")[:200] if finish else None)
        return
    for i, tc in enumerate(tcs):
        name = tc["function"]["name"]
        args_raw = tc["function"]["arguments"]
        print(f"\n--- tool_call[{i}] name={name!r} args_len={len(args_raw)} ---")
        print("raw head:", args_raw[:200])
        print("raw tail:", args_raw[-200:])
        try:
            parsed = json.loads(args_raw)
            print("json parse: OK; top-level keys:", list(parsed.keys()))
            scenes = parsed.get("scenes")
            print("scenes type:", type(scenes).__name__,
                  "len:", len(scenes) if isinstance(scenes, (list, str)) else "n/a")
            if isinstance(scenes, list) and scenes:
                print("scenes[0] type:", type(scenes[0]).__name__)
        except Exception as e:
            print("json parse FAILED:", e)


asyncio.run(main())
