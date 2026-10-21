# -*- coding: utf-8 -*-
"""P42 EXP2 反馈恢复 v3：正确的 LevelDB log（WriteBatch）解析器。
格式：32KB block；record = crc(4)+len(2)+type(1)+payload；type 1=FULL/2=FIRST/3=MIDDLE/4=LAST。
WriteBatch payload：seq(8)+count(4)+entries[type(1)=put, keylen varint, key, vallen varint, value]。
localStorage 值：首字节 0x01=后续为 UTF-16LE；0x00=latin1。
"""
import glob, os, json, struct

def varint(buf, i):
    shift = 0; v = 0
    while i < len(buf):
        b = buf[i]; i += 1
        v |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return v, i

def parse_log(path, out):
    data = open(path, "rb").read()
    BLOCK = 32768
    pos = 0
    pending = b""      # FIRST/MIDDLE/LAST 重组
    while pos + 7 <= len(data):
        # block trailer：剩 <7 字节则跳到下一 block
        if len(data) - pos < 7:
            break
        crc, length, rtype = struct.unpack("<IHB", data[pos:pos+7])
        if rtype == 0 and length == 0:      # zero padding → 跳到 block 尾
            pos = (pos // BLOCK + 1) * BLOCK
            continue
        payload = data[pos+7 : pos+7+length]
        pos += 7 + length
        if pos % BLOCK + 7 > BLOCK:          # 下一条越界 → 对齐（保守）
            pass
        if rtype == 1:      rec = payload
        elif rtype == 2:    pending = payload; continue
        elif rtype == 3:    pending += payload; continue
        elif rtype == 4:    rec = pending + payload; pending = b""
        else:               rec = None
        if rec is None or len(rec) < 12:
            continue
        # WriteBatch
        i = 12   # 8 seq + 4 count
        try:
            count = struct.unpack("<I", rec[8:12])[0]
            for _ in range(min(count, 10000)):
                tag = rec[i]; i += 1
                if tag != 1:
                    break
                klen, i = varint(rec, i)
                key = rec[i:i+klen]; i += klen
                vlen, i = varint(rec, i)
                val = rec[i:i+vlen]; i += vlen
                ks = key.decode("utf-8", "replace")
                if "p42exp2" in ks:
                    # 去掉 origin 前缀（_file://\x00\x01...）
                    k = ks.split("\x00")[-1]
                    if k.startswith("\x01"):
                        k = k[1:]
                    if val and val[0] == 0x01:
                        v = val[1:].decode("utf-16-le", "replace")
                    else:
                        v = val.decode("utf-8", "replace")
                    if k not in out or len(v) > len(out[k]):
                        out[k] = v
        except (IndexError, struct.error):
            continue

out = {}
files = sorted(glob.glob(os.path.expandvars(
    r"%LOCALAPPDATA%/Microsoft/Edge/User Data/Default/Local Storage/leveldb/*.log")),
    key=os.path.getmtime)
print("logs:", files)
for f in files:
    parse_log(f, out)

# 排序输出：qa → sel → img
def sortkey(k):
    if k.startswith("p42exp2_qa"): return (0, k)
    if k.startswith("p42exp2_sel"): return (1, k)
    return (2, k)
for k in sorted(out, key=sortkey):
    print("=" * 8, k)
    print(out[k])
with open("_tmp/p42_exp2_feedback_v3.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\nTOTAL", len(out), "keys -> _tmp/p42_exp2_feedback_v3.json")
