# gp_gate_evidence.py — SCRATCH：抽取 truth-gate 跨轮误触发证据 turn
import json, glob, io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
out = io.open("gp_gate_evidence.txt", "w", encoding="utf-8")
def w(*a): print(*a, file=out)

f = glob.glob('projects/__e2e_ai5b_case9_20260815_231616/output/agents/sessions/*.json')[0]
d = json.load(open(f, encoding='utf-8'))
msgs = d['messages']
w("session:", f, "messages:", len(msgs))
targets = ["请说明一下你调用工具的流程", "你调用工具了吗", "你没有调用是出现了什么错误",
           "你上次执行的流程", "你能查看到剧本的内容嘛", "目前是几条故事段", "为什么这么慢"]
for i, m in enumerate(msgs):
    if m.get('role') != 'user':
        continue
    c = m.get('content') or ''
    if any(t in c for t in targets):
        w("=" * 70)
        w("USER:", c[:150])
        for j in range(i + 1, min(i + 4, len(msgs))):
            am = msgs[j]
            if am.get('role') == 'assistant':
                meta = am.get('meta') or {}
                w("ASSISTANT(status=%s intent=%s write_attempts=%s write_success=%s):" % (
                    am.get('status'), meta.get('intent'),
                    meta.get('write_attempts'), meta.get('write_success')))
                w((am.get('content') or '')[:600])
                w("TRACE:", [(t.get('tool'), t.get('result'), (t.get('error') or '')[:50])
                             for t in (meta.get('trace') or [])])
                break
out.close()
print("done")
