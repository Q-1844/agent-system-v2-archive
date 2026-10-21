"""Extract COLLAB_FIX_R1_1_20261018.zip to D:\isolated, fixing GBK filenames."""
import zipfile
from pathlib import Path

ZIP = Path(r"C:\Users\曹文淇\Desktop\ai工作流\.claude\压缩包\COLLAB_NEXT_STAGE\patches\COLLAB_FIX_R1_1_20261018.zip")
OUT = Path(r"D:\isolated\COLLAB_FIX_R1_1_20261018")

z = zipfile.ZipFile(ZIP)
count = 0
for info in z.infolist():
    name = info.filename
    if not (info.flag_bits & 0x800):  # not UTF-8 flagged -> decode cp437 then gbk
        try:
            name = info.filename.encode("cp437").decode("gbk")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    target = OUT / name
    if info.is_dir():
        target.mkdir(parents=True, exist_ok=True)
        continue
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(z.read(info))
    count += 1
print(f"extracted {count} files to {OUT}")
