# -*- coding: utf-8 -*-
"""扰动用例 `double-bottle`：把返瓶"加成两个"（模拟双返），跑完**逐字节复原**。

注入形态（真实世界里最容易写出来的那种）：
  配方层 `getRemainingItems` 里，除了催化剂那格，**兑换物那格也塞一个玻璃瓶**
  ⇒ 一次合成回到 2 个瓶（关卡 `[bgn10rc2-remainder-unique]` 与 A 级 `_bottle_total` 都该红）。

⚠ 只用 bytes 读写（Windows 的文本管道会把中文注释写坏）。⚠ 复原后复核 SHA256。
"""
import hashlib
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
TARGET = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "recipe" / "RawSturdygoldRecipe.java"
SAVED = REPO / "probe" / "bgn10rc2" / "RawSturdygoldRecipe.java.orig"

ANCHOR = "            if (stack.is(this.catalyst)) {\r\n"
ANCHOR_UNIX = "            if (stack.is(this.catalyst)) {\n"

INJECT_TAIL = "            } else if (stack.is(this.exchange)) {   // PERTURB: 模拟双返（第二格也塞一个瓶）\n"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "inject"
    SAVED.parent.mkdir(parents=True, exist_ok=True)
    if mode == "inject":
        raw = TARGET.read_bytes()
        if not SAVED.exists():
            shutil.copyfile(TARGET, SAVED)                # 逐字节备份
        text = raw.decode("utf-8")
        eol = "\r\n" if "\r\n" in text else "\n"
        if "PERTURB" in text:
            print("already injected; sha=%s" % sha(TARGET)[:16])
            return
        # 在 "remaining.set(i, new ItemStack(Items.GLASS_BOTTLE)); ... }" 的闭合括号后插 else-if
        needle = "                remaining.set(i, new ItemStack(Items.GLASS_BOTTLE));"
        idx = text.find(needle)
        assert idx >= 0, "找不到返瓶那一行"
        close = text.find("}", idx)
        assert close > idx, "找不到闭合括号"
        tail = (eol + "            } else if (stack.is(this.exchange)) {" + eol
                + "                remaining.set(i, new ItemStack(Items.GLASS_BOTTLE));"
                + " // PERTURB 第二格也塞瓶" + eol + "            ")
        text = text[:close] + tail + text[close:]
        TARGET.write_bytes(text.encode("utf-8"))
        print("injected: sha %s -> %s" % (sha(SAVED)[:16], sha(TARGET)[:16]))
    else:
        assert SAVED.exists(), "没有备份，无法复原"
        shutil.copyfile(SAVED, TARGET)
        ok = sha(TARGET) == sha(SAVED)
        print("restored: sha=%s byte-identical=%s" % (sha(TARGET)[:16], ok))
        if not ok:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
