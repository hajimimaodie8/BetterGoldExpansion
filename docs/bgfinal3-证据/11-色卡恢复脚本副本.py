# -*- coding: utf-8 -*-
"""bgfinal3 第一步：把作者 zip 里的靛海金纹饰色卡按**字节原样**落到项目路径。

- 只认 "靛海金" + "色卡" 唯一命中；命中数 != 1 直接 exit 2（不猜）。
- 落点：src/main/resources/assets/bettergold/textures/trims/color_palettes/indigoseagold.png
- 打印源文件 / 落点两份 SHA256，并断言相等。
"""
import hashlib
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(r"E:\mc\mcmod\bettergold-template-1.21.1")
ZIP = Path(r"E:\mc\mc资料\更有用的金 新约7.zip")
DST = REPO / "src/main/resources/assets/bettergold/textures/trims/color_palettes/indigoseagold.png"

WANT_SRC = "9c966b7f80c2e2550064a822730a704e8a68aeac9047fa9f1aabfda7eb9e6b6d"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    with zipfile.ZipFile(ZIP) as z:
        hits = [n for n in z.namelist()
                if ("靛海金" in n or "indigosea" in n.lower())
                and ("色卡" in n or "palette" in n.lower())]
        print("zip 候选（靛海金 + 色卡）:", hits)
        if len(hits) != 1:
            print("候选数 != 1 ⇒ 停下报告（不猜）")
            return 2
        entry = hits[0]
        data = z.read(entry)
        info = z.getinfo(entry)
    print("zip 条目:", entry, "size=", info.file_size, "compress=", info.compress_type)
    print("源 SHA256     :", sha(data))
    if sha(data) != WANT_SRC:
        print("⚠ 源哈希与 docs/bg7-证据/04a 记的历史值不一致 ⇒ 停下")
        return 2
    before = DST.read_bytes()
    print("落点(改前) SHA256:", sha(before), "size=", len(before))
    DST.write_bytes(data)
    after = DST.read_bytes()
    print("落点(改后) SHA256:", sha(after), "size=", len(after))
    ok = sha(data) == sha(after) == WANT_SRC
    print("三重一致(源 == 落点 == 历史留档):", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
