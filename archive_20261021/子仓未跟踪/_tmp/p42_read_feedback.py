# -*- coding: utf-8 -*-
"""从 Edge localStorage leveldb 落盘文件里恢复 P42 EXP2 评审反馈。"""
import glob, os, re, json

FILES = glob.glob(os.path.expandvars(
    r"%LOCALAPPDATA%/Microsoft/Edge/User Data/Default/Local Storage/leveldb/*"))
out = {}
for fp in FILES:
    if not os.path.isfile(fp) or os.path.getsize(fp) == 0:
        continue
    data = open(fp, "rb").read()
    for m in re.finditer(rb"p42exp2_[A-Za-z0-9_]+", data):
        key_start = m.start()
        key = m.group().decode("ascii", "replace")
        # 值紧跟 key 之后（同一条 LevelDB 记录）：先试 UTF-16LE（中文必走此编码）
        tail = data[m.end(): m.end() + 8000]
        # 跳过 key 尾与值头之间的少量结构字节（0x01/0x00/长度前缀）
        best = None
        for off in range(0, 24):
            chunk = tail[off:]
            if len(chunk) < 4:
                continue
            # UTF-16LE: 首字节常为 0x01..0x63（长度或标记），解码到不可读处为止
            try:
                # 取偶数长度
                s = chunk[: len(chunk) - (len(chunk) % 2)].decode("utf-16-le",
                                                                 "ignore")
                # 取可打印前缀（中文/ASCII/常用标点）
                run = re.match(r"[ -~一-鿿　-〿＀-￯"
                               r"（）：；、。，！？—…「」『』【】\s]*", s)
                if run and len(run.group()) > (len(best) if best else 2):
                    best = run.group()
            except Exception:
                pass
        if best:
            # 键可能跨记录重复（log+ldb），保留最长值
            if key not in out or len(best) > len(out[key]):
                out[key] = best
            print(f"{key}  =>  {best[:160]}")
        else:
            print(f"{key}  =>  <未解析出值>  ctx={data[key_start:key_start+120]!r}"
                  .encode("unicode_escape").decode()[:200])

with open("_tmp/p42_exp2_feedback_recovered.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\nsaved -> _tmp/p42_exp2_feedback_recovered.json")
