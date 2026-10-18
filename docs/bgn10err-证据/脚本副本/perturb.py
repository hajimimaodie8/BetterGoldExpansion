# -*- coding: utf-8 -*-
"""bgn10err 扰动矩阵（Python bytes 改/复原；每个用例逐字节复原 + SHA256 自证）。

用例：
  baseline  不改                                   期望 绿
  P1        把错误图标换回原版 container/anvil/error  期望 红（灰矩形回来）
  P2        删掉新精灵                               期望 红
  P3        只往 Screen 加一行注释                    期望 仍绿
  P4        把新精灵 (0,0) 改成原版灰 #C6C6C6        期望 红（灰搬进来了）
  P5        把新精灵一个红叉像素改回作者像素           期望 红（红叉 80 个）

用法: py -3 probe/bgn10err/perturb.py
"""
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCREEN = ROOT / "src/main/java/com/hjmmd_8/bettergold/client/SturdygoldAnvilScreen.java"
SPRITE = ROOT / "src/main/resources/assets/bettergold/textures/gui/sprites/container/sturdygold_anvil/error.png"
VALIDATOR = ROOT / "tools/asset-generator/validate_metal_data.py"
OUT = ROOT / "docs/bgn10err-证据" / "04-扰动矩阵.txt"
BAK = ROOT / "build" / "bgn10err_perturb_bak"
LINES = []


def w(s=""):
    LINES.append(s)
    print(s)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_validator(tag: str):
    r = subprocess.run([sys.executable, str(VALIDATOR)], capture_output=True, cwd=str(ROOT))
    out = r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")
    (ROOT / "build" / ("bgn10err_perturb_%s.out" % tag)).write_text(out, encoding="utf-8")
    return r.returncode, out


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    BAK.mkdir(parents=True, exist_ok=True)
    screen0 = SCREEN.read_bytes()
    sprite0 = SPRITE.read_bytes()
    (BAK / "screen.java").write_bytes(screen0)
    (BAK / "error.png").write_bytes(sprite0)
    sha_s0, sha_p0 = sha(SCREEN), sha(SPRITE)
    w("bgn10err 扰动矩阵（脚本 probe/bgn10err/perturb.py）")
    w("baseline SHA：Screen = %s / error.png = %s" % (sha_s0, sha_p0))
    w("")

    cases = []

    def add(name, apply, expect_green, want_tag):
        cases.append((name, apply, expect_green, want_tag))

    def p1():
        t = SCREEN.read_text(encoding="utf-8")
        old = 'ResourceLocation.fromNamespaceAndPath(bettergold.MODID, "container/sturdygold_anvil/error")'
        assert t.count(old) == 1
        SCREEN.write_bytes(t.replace(old, 'ResourceLocation.withDefaultNamespace("container/anvil/error")', 1)
                           .encode("utf-8"))
        return "ERROR_SPRITE 指回原版 minecraft:container/anvil/error"

    def p2():
        SPRITE.unlink()
        return "删掉新精灵 error.png"

    def p3():
        t = SCREEN.read_bytes()
        SCREEN.write_bytes(t + "\n// bg-n10err perturb: 只加这一行注释（必须仍绿）\n".encode("utf-8"))
        return "只在 Screen 末尾加一行注释"

    def p4():
        import zlib
        import struct
        # 直接改字节：用 PIL 读、改一个像素、写回（只动这一张我们自己生成的文件）
        from PIL import Image
        im = Image.open(SPRITE).convert("RGBA")
        im.putpixel((0, 0), (198, 198, 198, 255))
        im.save(SPRITE)
        return "新精灵 (0,0) 改成原版灰 #C6C6C6"

    def p5():
        from PIL import Image
        im = Image.open(SPRITE).convert("RGBA")
        own = Image.open(ROOT / "src/main/resources/assets/bettergold/textures/gui/container/sturdygold_anvil.png").convert("RGBA")
        # (13,10) 是红叉正中的一撇（掩码第 10 行 `............RRR.............`）：改回作者同坐标像素 ⇒ 红叉只剩 80 个
        im.putpixel((13, 10), own.getpixel((99 + 13, 45 + 10)))
        im.save(SPRITE)
        return "新精灵 (13,10) 红叉像素改回作者像素（红叉 80 个）"

    add("baseline", lambda: "不改", True, None)
    add("P1", p1, False, "bgn10err-screen")
    add("P2", p2, False, "bgn10err-sprite")
    add("P3", p3, True, None)
    add("P4", p4, False, "bgn10err-pixels")
    add("P5", p5, False, "bgn10err-pixels")

    ok_all = True
    for name, fn, expect_green, want_tag in cases:
        desc = fn()
        code, out = run_validator(name)
        if expect_green:
            hit = code == 0
            detail = "exit=%d（期望 0）" % code
        else:
            hit = code == 1 and want_tag is not None and ("[%s]" % want_tag) in out
            detail = "exit=%d（期望 1）/ 命中 [%s] = %s" % (code, want_tag, ("[%s]" % want_tag) in out)
        # 复原
        SCREEN.write_bytes(screen0)
        SPRITE.write_bytes(sprite0)
        r_ok = sha(SCREEN) == sha_s0 and sha(SPRITE) == sha_p0
        if not r_ok or not hit:
            ok_all = False
        w("%-9s %-52s %s；复原逐字节 = %s"
          % (name, desc, detail, "是" if r_ok else "否!!"))
        if not hit:
            # 打一行最相关的失败/结论行
            for line in out.splitlines():
                if ("[bgn10err-" in line) or ("bgn10err）问题" in line):
                    w("            └─ " + line.strip())
                    break
    w("")
    w("SUMMARY 全部用例符合期望 = %s；Screen 复原 SHA = %s（baseline %s）；error.png 复原 SHA = %s（baseline %s）"
      % (ok_all, sha(SCREEN), sha_s0, sha(SPRITE), sha_p0))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(LINES) + "\n", encoding="utf-8")
    print("\n[saved] %s" % OUT)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
