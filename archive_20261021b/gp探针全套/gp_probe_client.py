import asyncio, json, sys, httpx
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAISE = object()
class TimeoutScripted:
    def __init__(self, script):
        self.script = list(script); self.calls = []
    async def chat_completion(self, messages, **kw):
        self.calls.append(messages)
        if not self.script:
            return {"content": "空", "tool_calls": None}
        item = self.script.pop(0)
        if item is RAISE:
            raise httpx.ReadTimeout()
        if callable(item):
            r = item(messages)
            print("callable->", type(r).__name__, repr(r)[:80])
            return r
        print("item->", type(item).__name__, repr(item)[:80])
        return item

def _tc(name, args):
    return {"id":"c1","type":"function","function":{"name":name,"arguments":json.dumps(args, ensure_ascii=False)}}
def _um(updates, rev): return _tc("story.update_many", {"updates":updates,"expected_revision":rev})

rev = "deadbeef"
items = [{"scene_id":f"s0{i}","summary":f"新{i}"} for i in range(1,6)]
def um_batch(lo,hi):
    return lambda m: {"content":"", "tool_calls":[_um(items[lo:hi], rev)]}

c = TimeoutScripted([RAISE, um_batch(0,2)])
async def go():
    for _ in range(3):
        try:
            r = await c.chat_completion([])
            print("  ret type:", type(r).__name__, "is_dict=", isinstance(r, dict))
        except httpx.ReadTimeout:
            print("  RAISE")
asyncio.run(go())
