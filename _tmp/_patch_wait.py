# -*- coding: utf-8 -*-
"""AI-7C-H §十/§十五：restart 等待窗口 30s -> 240s（覆盖真实 Agnes view 生成时长，
保留超时回退）。精确字符串替换，UTF-8 无 BOM。"""
from pathlib import Path

p = Path("src/store/agentUi.ts")
s = p.read_text(encoding="utf-8")
old = "const stopped = await csStore.waitForExecutionStopped(30000);"
new = ("// AI-7C-H §十/§十五：窗口须覆盖真实生产收尾（Agnes view 生成 ~1-3min/角色），\n"
       "      // 否则 §十五「新 ChangeSession 自动开始」退化为暂存回退。超时仍有不丢请求回退。\n"
       "      const stopped = await csStore.waitForExecutionStopped(240000);")
assert s.count(old) == 1, f"expect 1 occurrence, got {s.count(old)}"
p.write_text(s.replace(old, new), encoding="utf-8", newline="")
print("agentUi.ts restart wait window -> 240s OK")
