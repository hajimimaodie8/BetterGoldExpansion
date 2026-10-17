# -*- coding: utf-8 -*-
"""去掉 §21.6 里重复的一行（占位替换时把同一句写了两遍）。"""
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

DOC = Path(__file__).resolve().parents[3] / "docs" / "1.7-混沌金与崩乱合金-需求立档.md"

DUP = ("判据 = 真扰动必须让**本段**红且点名 tag、只改注释必须仍 0 条、每例**逐字节复原 + SHA256 自证**。\n"
       "\n"
       "判据 = 真扰动必须让**本段**红且点名 tag、只改注释必须仍 0 条、每例**逐字节复原 + SHA256 自证**。\n")
FIX = ("判据 = 真扰动必须让**本段**红且点名 tag、只改注释必须仍 0 条、每例**逐字节复原 + SHA256 自证**。\n")


def main() -> None:
    raw = DOC.read_bytes()
    old = raw.decode("utf-8")
    if DUP not in old:
        # 幂等：已经去重过。⚠ 注意这句话在**两处**都合法存在（§20.5 = 上一轮的扰动矩阵，
        # §21.6 = 本轮），所以判据不能写 "全文件恰好 1 处"。
        print("already deduped (phrase still appears in §20.5 + §21.6, each once)")
        return
    assert old.count(DUP) == 1, "重复块不唯一（%d）" % old.count(DUP)
    text = old.replace(DUP, FIX, 1)
    DOC.write_bytes(text.encode("utf-8"))
    back = DOC.read_text(encoding="utf-8")
    assert back.count("判据 = 真扰动必须让**本段**红") == 2, "去重后应剩 2 处（§20.5 + §21.6）"
    print("dedup ok: %d -> %d bytes, sha %s -> %s"
          % (len(raw), len(back.encode("utf-8")),
             hashlib.sha256(raw).hexdigest()[:16].upper(),
             hashlib.sha256(back.encode("utf-8")).hexdigest()[:16].upper()))


if __name__ == "__main__":
    main()
