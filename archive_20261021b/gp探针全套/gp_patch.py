# -*- coding: utf-8 -*-
"""gp_patch.py：对 script_writer.py 做可观测性修复（幂等，可重跑）。"""
import io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard\src\agents\script_writer.py"
src = io.open(P, encoding="utf-8").read()
orig = src


def rep(old, new, must=True):
    global src
    if old in src:
        n = src.count(old)
        assert n == 1, f"非唯一匹配 x{n}: {old[:60]}"
        src = src.replace(old, new)
        print(f"OK  {old[:50]!r}...")
    elif must:
        raise SystemExit(f"NOT FOUND: {old[:80]}")
    else:
        print(f"SKIP(已改) {old[:50]!r}")


# 1. _run_tool_loop 签名加 state（用 max_steps 锚点区分 script_writer_turn 签名）
rep("                         max_steps: int = DEFAULT_MAX_TOOL_STEPS,\n"
    "                         thinking: bool = False,\n"
    "                         event_cb=None) -> dict:",
    "                         max_steps: int = DEFAULT_MAX_TOOL_STEPS,\n"
    "                         thinking: bool = False,\n"
    "                         event_cb=None,\n"
    "                         state: Optional[dict] = None) -> dict:")

# 2. docstring 末尾加 state 说明
rep("    max_steps 仅防死循环（LLM 循环步数），非业务数量限制；批量拆分等长任务由调用方上调。\n    \"\"\"",
    "    max_steps 仅防死循环（LLM 循环步数），非业务数量限制；批量拆分等长任务由调用方上调。\n"
    "\n"
    "    state：可选共享容器（调用方传 dict）。events/receipts/trace 三个累积列表放进去，\n"
    "    工具循环中途抛异常（网络断/服务端错误）时调用方 except 仍能拿到已执行的部分——\n"
    "    诊断「跑到第几步、哪些写已真实落盘」不再黑盒。不传时行为与原先完全一致（局部列表）。\n"
    "    \"\"\"")

# 3. 三个累积列表走共享容器
rep("    events: list = []\n",
    "    events: list = (state or {}).setdefault(\"events\", [])\n", must=False)
rep("    receipts: list = []          # 本轮所有写工具调用的真实回执（成功与失败都记）\n",
    "    receipts: list = (state or {}).setdefault(\"receipts\", [])   # 本轮所有写工具调用的真实回执（成功与失败都记）\n",
    must=False)
rep("    trace: list = []\n",
    "    trace: list = (state or {}).setdefault(\"trace\", [])\n", must=False)

io.open(P, "w", encoding="utf-8").write(src)
print("\npatch applied:", len(orig) != len(src))
