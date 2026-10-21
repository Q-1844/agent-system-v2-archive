# -*- coding: utf-8 -*-
"""P42 EXP2 反馈恢复 v2：全量扫描 + 最长值优先 + 逐图评语完整提取。"""
import glob, os, re, json

FILES = sorted(glob.glob(os.path.expandvars(
    r"%LOCALAPPDATA%/Microsoft/Edge/User Data/Default/Local Storage/leveldb/*")),
    key=os.path.getmtime)
print("files:", [os.path.basename(f) for f in FILES])

PRINTABLE = re.compile(r"[ -~一-鿿　-〿＀-￯（）：；、。，！？—…「」『』【】（）\s""]*")
out = {}
for fp in FILES:
    if not os.path.isfile(fp) or os.path.getsize(fp) == 0:
        continue
    data = open(fp, "rb").read()
    for m in re.finditer(rb"p42exp2_[A-Za-z0-9_]{2,60}", data):
        key = m.group().decode("ascii", "replace")
        tail = data[m.end(): m.end() + 20000]
        best = ""
        for off in range(0, 10):
            chunk = tail[off:]
            chunk = chunk[: len(chunk) - (len(chunk) % 2)]
            s = chunk.decode("utf-16-le", "ignore")
            run = PRINTABLE.match(s)
            if run and len(run.group()) > len(best):
                best = run.group()
        if best and len(best) > 2:
            # LevelDB 同键可能多版本（历史输入）——保留最长
            if key not in out or len(best) > len(out[key]):
                out[key] = best

# 归并：img_* 逐图评语（同名 key 可能因 log/ldb 分裂出现两个变体，取含中文的最长）
merged = {}
for k, v in sorted(out.items()):
    merged[k] = v

for k, v in merged.items():
    print("=" * 8, k)
    print(v)
with open("_tmp/p42_exp2_feedback_v2.json", "w", encoding="utf-8") as f:
    json.dump(merged, f, ensure_ascii=False, indent=1)
print("\nsaved -> _tmp/p42_exp2_feedback_v2.json", len(merged), "keys")
