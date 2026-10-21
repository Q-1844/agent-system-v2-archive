# -*- coding: utf-8 -*-
"""P42 EXP2 反馈恢复 v4：完整 LevelDB 解析（log WriteBatch + ldb 表块/前缀压缩/snappy）。"""
import glob, os, json, struct

# ---------- snappy 最小解压 ----------
def snappy_decompress(data):
    # 变长长度头
    i = 0; shift = 0; out_len = 0
    while True:
        b = data[i]; i += 1
        out_len |= (b & 0x7F) << shift
        if not (b & 0x80): break
        shift += 7
    out = bytearray()
    while i < len(data):
        tag = data[i]; i += 1
        t = tag & 3
        if t == 0:   # literal
            ln = tag >> 2
            if ln >= 60:
                nb = ln - 59
                ln = int.from_bytes(data[i:i+nb], "little"); i += nb
            else:
                ln += 1
            out += data[i:i+ln]; i += ln
        else:
            if t == 1:
                ln = ((tag >> 2) & 7) + 4
                off = ((tag >> 5) << 8) | data[i]; i += 1
            elif t == 2:
                ln = (tag >> 2) + 1
                off = int.from_bytes(data[i:i+2], "little"); i += 2
            else:
                ln = (tag >> 2) + 1
                off = int.from_bytes(data[i:i+4], "little"); i += 4
            if off == 0 or off > len(out): break
            for _ in range(ln):
                out.append(out[-off])
    return bytes(out)

def varint(buf, i):
    shift = 0; v = 0
    while i < len(buf):
        b = buf[i]; i += 1
        v |= (b & 0x7F) << shift
        if not (b & 0x80): break
        shift += 7
    return v, i

def decode_val(val):
    if not val: return ""
    if val[0] == 0x01:
        return val[1:].decode("utf-16-le", "replace")
    # Chrome 新版：偶长且含 \x00 → raw UTF-16LE；否则 utf-8
    if len(val) % 2 == 0 and b"\x00" in val:
        return val.decode("utf-16-le", "replace")
    return val.decode("utf-8", "replace")

# ---------- .log（WriteBatch） ----------
def parse_log(path, out):
    data = open(path, "rb").read()
    BLOCK = 32768; pos = 0; pending = b""
    while pos + 7 <= len(data):
        crc, length, rtype = struct.unpack("<IHB", data[pos:pos+7])
        if rtype == 0 and length == 0:
            pos = (pos // BLOCK + 1) * BLOCK; continue
        payload = data[pos+7 : pos+7+length]
        pos += 7 + length
        if rtype == 1: rec = payload
        elif rtype == 2: pending = payload; continue
        elif rtype == 3: pending += payload; continue
        elif rtype == 4: rec = pending + payload; pending = b""
        else: rec = None
        if not rec or len(rec) < 12: continue
        try:
            count = struct.unpack("<I", rec[8:12])[0]
            i = 12
            for _ in range(min(count, 100000)):
                tag = rec[i]; i += 1
                if tag != 1: break
                klen, i = varint(rec, i)
                key = rec[i:i+klen]; i += klen
                vlen, i = varint(rec, i)
                val = rec[i:i+vlen]; i += vlen
                ks = key.decode("utf-8", "replace")
                if "p42exp2" in ks:
                    k = ks.split("\x00")[-1].lstrip("\x01")
                    v = decode_val(val)
                    if k not in out or len(v) > len(out[k]):
                        out[k] = v
        except (IndexError, struct.error):
            continue

# ---------- .ldb（表块：footer→index→data，前缀压缩+snappy） ----------
def block_at(data, off, size):
    raw = data[off:off+size]
    comp = data[off+size]
    if comp == 1:
        return snappy_decompress(raw)
    return raw

def parse_ldb(path, out):
    data = open(path, "rb").read()
    if len(data) < 48 or data[-8:] != b"\x57\xfb\x80\x8b\x24\x75\x47\xdb":
        return
    fh = data[-48:-8]
    i = 0
    _, i = varint(fh, i)          # metaindex off
    _, i = varint(fh, i)          # metaindex size
    ioff, i = varint(fh, i)
    isize, i = varint(fh, i)
    try:
        idx = block_at(data, ioff, isize)
    except Exception:
        return
    # 解 index 块：entries(shared,non_shared,val_len,key_delta,value=block_handle)
    def entries(block):
        # 跳过尾部 restart 数组：直接顺序解到尽头（容忍尾部垃圾）
        j = 0; key = b""
        while j < len(block) - 4:
            try:
                sh, j2 = varint(block, j)
                nsh, j2 = varint(block, j2)
                vl, j2 = varint(block, j2)
            except Exception:
                return
            if nsh > len(block) - j2 or vl > len(block) - j2 - nsh:
                return
            key = key[:sh] + block[j2:j2+nsh]; j2 += nsh
            val = block[j2:j2+vl]; j2 += vl
            j = j2
            yield key, val
    for ikey, ival in entries(idx):
        try:
            off, j = varint(ival, 0)
            size, j = varint(ival, j)
        except Exception:
            continue
        try:
            blk = block_at(data, off, size)
        except Exception:
            continue
        for ekey, eval_ in entries(blk):
            ks = ekey.decode("utf-8", "replace")
            if "p42exp2" in ks:
                k = ks.split("\x00")[-1].lstrip("\x01")
                v = decode_val(eval_)
                if k not in out or len(v) > len(out[k]):
                    out[k] = v

out = {}
base = os.path.expandvars(r"%LOCALAPPDATA%/Microsoft/Edge/User Data/Default/Local Storage/leveldb")
for f in sorted(glob.glob(base + "/*.ldb"), key=os.path.getmtime):
    try:
        parse_ldb(f, out)
    except Exception as e:
        print("ldb fail", os.path.basename(f), e)
for f in sorted(glob.glob(base + "/*.log"), key=os.path.getmtime):
    parse_log(f, out)

def sortkey(k):
    if "qa3" in k: return (0, k)
    if "qa4" in k: return (1, k)
    if "sel" in k: return (2, k)
    return (3, k)
for k in sorted(out, key=sortkey):
    print("=" * 8, k)
    print(out[k])
with open("_tmp/p42_exp2_feedback_v4.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\nTOTAL", len(out), "keys -> _tmp/p42_exp2_feedback_v4.json")
