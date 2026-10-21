# -*- coding: utf-8 -*-
"""gp_patch2.py：第二段补丁（三列表共享容器），从 patch1 后的状态继续。"""
import io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard\src\agents\script_writer.py"
src = io.open(P, encoding="utf-8").read()


def rep(old, new):
    global src
    n = src.count(old)
    assert n == 1, f"匹配 x{n}: {old[:60]}"
    src = src.replace(old, new)
    print("OK", repr(old[:50]))


# _run_tool_loop 初始化块（receipts 带注释 + write_attempts 跟随 = 独有组合）
rep("    events: list = []\n"
    "    receipts: list = []          # 本轮所有写工具调用的真实回执（成功与失败都记）\n"
    "    write_attempts = 0",
    "    events: list = (state or {}).setdefault(\"events\", [])\n"
    "    receipts: list = (state or {}).setdefault(\"receipts\", [])   # 本轮所有写工具调用的真实回执（成功与失败都记）\n"
    "    write_attempts = 0")

rep("    trace: list = []\n    last_read_after_write = -1",
    "    trace: list = (state or {}).setdefault(\"trace\", [])\n    last_read_after_write = -1")

io.open(P, "w", encoding="utf-8").write(src)
print("done")
