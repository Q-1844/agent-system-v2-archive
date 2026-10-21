# -*- coding: utf-8 -*-
"""gp_patch3.py：script_writer_turn 调用点 + except 分支（日志/类型名/保 partial）。"""
import io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard\src\agents\script_writer.py"
src = io.open(P, encoding="utf-8").read()

OLD = '''        try:
            final = await _run_tool_loop(rt, client, project, messages, content, user_msg.message_id,
                                         thinking=thinking, event_cb=event_cb)
'''
NEW = '''        loop_state: dict = {}   # 异常时仍可取回已执行的 trace/receipts/events（可观测性）
        try:
            final = await _run_tool_loop(rt, client, project, messages, content, user_msg.message_id,
                                         thinking=thinking, event_cb=event_cb,
                                         state=loop_state)
'''
assert src.count(OLD) == 1, f"call-site x{src.count(OLD)}"
src = src.replace(OLD, NEW)
print("OK call-site")

OLD2 = '''        except Exception as e:
            assistant_text = f"[执行失败: {str(e)[:200]}]"
            status = ResultStatus.FAILED.value
            trace = []
'''
NEW2 = '''        except Exception as e:
            # 可观测性：完整 traceback 进日志（定位网络断/服务端错误的真实身份）；
            # str(e) 可能为空（如 TimeoutError），文本带异常类型名保证用户可见失败原因。
            log.exception("script_writer_turn 工具循环异常（project=%s session=%s）",
                          project, session_id)
            e_desc = str(e).strip()
            assistant_text = f"[执行失败: {type(e).__name__}: {e_desc}]"[:300]
            status = ResultStatus.FAILED.value
            # 保留已执行的部分（哪些写已真实落盘），不再清空成黑盒；
            # bool 标志保持 False（intent 退回 conversation，失败态下不猜测变更类别）。
            events = loop_state.get("events", [])
            receipts = pre_exec_receipts + loop_state.get("receipts", [])
            trace = (pre_trace + loop_state.get("trace", [])) if pre_trace else loop_state.get("trace", [])
'''
assert src.count(OLD2) == 1, f"except x{src.count(OLD2)}"
src = src.replace(OLD2, NEW2)
print("OK except-branch")

io.open(P, "w", encoding="utf-8").write(src)
print("done")
