# -*- coding: utf-8 -*-
"""bgfinal3 关卡扰动实测矩阵：1 基线 + 逐条改坏 + "只改注释必须仍绿"反向对照 + 收尾基线。

契约（同前几轮）：
  * 每条用例：改坏 ⇒ 期望的**稳定 ASCII 断言 id** 出现在输出里 且 exit code == 期望值；
  * 脚本**显式报出"变更未生效"**（模式没命中 ⇒ SETUP-FAIL，不算命中）；
  * **exit 2（脚本自身出错）一律当作用例坏了**，不算命中；
  * 每条改完**按字节复原**并核对 SHA256（前后 manifest 逐行相同）；
  * 逐条打印 exit / hit_expected 两列，最后统计 mismatches。
"""
import hashlib
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(errors="replace")

REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
OUT = os.path.join(REPO, "build", "bgfinal3-evidence", "perturb.txt")

PALETTE = "src/main/resources/assets/bettergold/textures/trims/color_palettes/indigoseagold.png"
ZH = "src/main/resources/assets/bettergold/lang/zh_cn.json"
EN = "src/main/resources/assets/bettergold/lang/en_us.json"
SNAP = "tools/asset-generator/bgappend-requirements-snapshot/bg-book-8.md"
MEV = "src/main/java/com/hjmmd_8/bettergold/event/ModEvents.java"
ADVJSON = "src/main/resources/data/bettergold/advancement/agriculture/plant_gold_crop.json"
GENADV = "tools/asset-generator/generate_advancements.py"
VTRIM = "tools/asset-generator/validate_trim_assets.py"
VASSETS = "tools/asset-generator/validate_metal_assets.py"
VDATA = "tools/asset-generator/validate_metal_data.py"
VADV = "tools/asset-generator/validate_advancements.py"

FILES = [PALETTE, ZH, EN, SNAP, MEV, ADVJSON, GENADV, VTRIM]

QUARTZ_101 = None  # 由 git 取（HEAD 版 indigoseagold.png = quartz 白灰阶，101 B）

# ⚠ 行尾：本仓这几个被改文件都是 **LF**（实测 `ModEvents.java` 的 CRLF 计数 = 0、LF = 846；
#   生成的 advancement JSON 也是 LF）⇒ 多行模式必须用 `\n`。
#   （第一版用了 `\r\n` ⇒ 6 条用例 SETUP-FAIL —— 这正是"扰动没生效"与"关卡没红"必须分开报的原因。）
TRIGGER_BLOCK = (
    b"                if (player instanceof ServerPlayer serverPlayer) {\n"
    b"                    CriteriaTriggers.PLACED_BLOCK.trigger(serverPlayer, plantPos, held);\n"
    b"                }\n")


def path(rel):
    return os.path.join(REPO, rel.replace("/", os.sep))


def read_bytes(rel):
    with open(path(rel), "rb") as f:
        return f.read()


def write_bytes(rel, data):
    with open(path(rel), "wb") as f:
        f.write(data)


def sha(rel):
    return hashlib.sha256(read_bytes(rel)).hexdigest()


def sub_b(rel, old, new, count=1):
    """字节级唯一替换；模式没命中就抛 SETUP-FAIL（区分"关卡没红"与"扰动没生效"）。"""
    raw = read_bytes(rel)
    got = raw.count(old)
    if got != count:
        raise RuntimeError("SETUP-FAIL: %s 里模式出现 %d 次（期望 %d）: %r" % (rel, got, count, old[:60]))
    write_bytes(rel, raw.replace(old, new))
    return len(raw), len(raw) + count * (len(new) - len(old))


# ---------------------------------------------------------------- 用例定义

def q(rel, s):
    return s.encode("utf-8")


CASES = [
    # ---------------- 基线 / 收尾基线 ----------------
    ("BASE", "基线（未改任何文件）", [], [
        (VTRIM, 0, None), (VASSETS, 0, None), (VDATA, 0, None), (VADV, 0, None)]),

    # ---------------- ① 靛海金色卡 ----------------
    ("P01", "靛海金色卡换回原版 quartz 的字节（101 B）",
     [("bin", PALETTE, "QUARTZ")], [
         (VTRIM, 1, "bgfinal3-indigosea-not-quartz"),
         (VASSETS, 1, "bgfinal3-indigosea-not-quartz")]),
    ("P02", "靛海金色卡翻转最后 1 个字节",
     [("flip", PALETTE, -1)], [
         (VTRIM, 1, "bgfinal3-indigosea-palette-restored"),
         (VASSETS, 1, "bgfinal3-indigosea-palette-restored")]),

    # ---------------- ② 手册「任意一件」 ----------------
    ("P03", "zh_cn 回退成旧口径「全套的万坚金盔甲」",
     [("b", ZH, q(ZH, u"此外任意一件万坚金盔甲"), q(ZH, u"此外全套的万坚金盔甲"))], [
         (VDATA, 1, "bgfinal3-manual-barter-single-piece")]),
    ("P04", "en_us 回退成旧口径「a full set of」",
     [("b", EN, q(EN, u"any single piece of Sturdygold armor"),
       q(EN, u"a full set of Sturdygold armor"))], [
         (VDATA, 1, "bgfinal3-manual-barter-single-piece")]),
    ("P05", "冻结快照正文回退成旧口径（语言文件不改）",
     [("b", SNAP, q(SNAP, u"此外任意一件万坚金盔甲还能使猪灵以物易物的获取量翻倍。 |"),
       q(SNAP, u"此外全套的万坚金盔甲还能使猪灵以物易物的获取量翻倍。 |"))], [
         (VDATA, 1, "bgfinal3-manual-barter-single-piece"),
         (VDATA, 1, "bgbook8-texts-verbatim")]),
    ("P06", "ModEvents 的「任意一件」被改成「全套」（一个 || 改成 &&）",
     [("b", MEV, b"|| player.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.FEET)",
       b"&& player.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.FEET)")], [
         (VDATA, 1, "bgfinal3-manual-follows-code")]),
    ("P07", "ModEvents 少判一个部位（删掉护腿那一行）",
     [("b", MEV, b"                || player.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.LEGS).is(AllItems.STURDYGOLD_LEGGINGS.get())\n",
       b"")], [
         (VDATA, 1, "bgfinal3-manual-follows-code")]),

    # ---------------- ③ 金胡萝卜 ----------------
    ("P08", "删掉 ModEvents 里那一次 PLACED_BLOCK 触发",
     [("b", MEV, TRIGGER_BLOCK, b"")], [
         (VDATA, 1, "bgfinal3-carrot-placed-block-trigger")]),
    ("P09", "把触发挪到 setBlock 之前（判据会读到空气）",
     [("b", MEV, TRIGGER_BLOCK, b""),
      ("b", MEV, b"            if (cropState.canSurvive(level, plantPos)) {\n",
       b"            if (cropState.canSurvive(level, plantPos)) {\n"
       + TRIGGER_BLOCK)], [
         (VDATA, 1, "bgfinal3-carrot-placed-block-trigger")]),
    ("P10", "去掉 ServerPlayer 守卫（改成无条件触发）",
     [("b", MEV, b"                if (player instanceof ServerPlayer serverPlayer) {\n"
                 b"                    CriteriaTriggers.PLACED_BLOCK.trigger(serverPlayer, plantPos, held);\n"
                 b"                }\n",
       b"                CriteriaTriggers.PLACED_BLOCK.trigger((ServerPlayer) player, plantPos, held);\n")], [
         (VDATA, 1, "bgfinal3-carrot-placed-block-trigger")]),
    ("P11", "产物里 plant_carrot 的方块改成金麦（判据指错方块）",
     [("b", ADVJSON, b'"block": "bettergold:golden_carrot_crop"',
       b'"block": "bettergold:golden_wheat_crop"')], [
         (VADV, 1, "bgfinal3-adv-carrot-planting")]),
    ("P12", "产物里把 plant_carrot 从「种植」OR 组里踢出去",
     [("b", ADVJSON, b'      "plant_eggplant",\n      "plant_carrot"\n',
       b'      "plant_eggplant"\n')], [
         (VADV, 1, "bgfinal3-adv-carrot-planting"),
         (VADV, 1, "bgach-requirements-semantics")]),
    ("P13", "产物里整条 plant_carrot criteria 删掉",
     [("b", ADVJSON,
       b'    },\n    "plant_carrot": {\n      "trigger": "minecraft:placed_block",\n'
       b'      "conditions": {\n        "location": [\n          {\n'
       b'            "condition": "minecraft:block_state_property",\n'
       b'            "block": "bettergold:golden_carrot_crop"\n          }\n        ]\n'
       b'      }\n    }\n', b'    }\n'),
      ("b", ADVJSON, b'      "plant_eggplant",\n      "plant_carrot"\n', b'      "plant_eggplant"\n')], [
         (VADV, 1, "bgfinal3-adv-carrot-planting")]),
    ("P14", u"生成器里那条 criteria 被删（产物没重生成，判「根」有没有了）",
     [("b", GENADV, u'            "plant_carrot": c_plant_crop(f"{NS}:golden_carrot_crop"),\r\n'.encode("utf-8"),
       b"")], [
         (VADV, 1, "bgfinal3-adv-carrot-planting")]),

    # ---------------- 反向对照：只改注释必须仍绿 ----------------
    ("R1", u"① 只往 validate_trim_assets.py 加一句「靛海金等于 quartz 是预期的」注释",
     [("b", VTRIM, b'PROBLEMS: list[str] = []',
       u'# 旧口径注释：靛海金逐像素等于 quartz 是预期的\r\nPROBLEMS: list[str] = []'.encode("utf-8"))], [
         (VTRIM, 0, None), (VASSETS, 0, None)]),
    ("R2", u"② 只往 ModEvents 那个方法里加旧口径注释（全套 / 任意一件）",
     [("b", MEV, b"    public static boolean wearingAnySturdygoldArmor(Player player) {",
       u"    // 旧口径（已作废）：全套的万坚金盔甲\r\n    public static boolean wearingAnySturdygoldArmor(Player player) {".encode("utf-8"))], [
         (VDATA, 0, None)]),
    ("R3", u"③ 只往金胡萝卜分支里加一句「这里曾调用 PLACED_BLOCK.trigger」的注释",
     [("b", MEV, b"                if (player instanceof ServerPlayer serverPlayer) {",
       u"                // 旧写法（已删除）：CriteriaTriggers.PLACED_BLOCK.trigger(serverPlayer, plantPos, held);\r\n                if (player instanceof ServerPlayer serverPlayer) {".encode("utf-8"))], [
         (VDATA, 0, None), (VADV, 0, None)]),
    ("R4", u"④ 只往生成器加注释（金胡萝卜 / placed_block 字样出现在注释里）",
     [("b", GENADV, b"def c_plant_crop(block: str) -> dict:",
       u"# 金胡萝卜也走 placed_block（注释，不是代码）\r\ndef c_plant_crop(block: str) -> dict:".encode("utf-8"))], [
         (VADV, 0, None), (VDATA, 0, None)]),
]


def apply_case(edits):
    """返回实际改动过的文件列表（用于报"变更未生效"）。"""
    touched = []
    for e in edits:
        if e[0] == "b":
            _, rel, old, new = e
            sub_b(rel, old, new)
            touched.append(rel)
        elif e[0] == "bin":
            _, rel, src = e
            write_bytes(rel, QUARTZ_101)
            touched.append(rel)
        elif e[0] == "flip":
            _, rel, idx = e
            raw = bytearray(read_bytes(rel))
            raw[idx] ^= 0x01
            write_bytes(rel, bytes(raw))
            touched.append(rel)
        else:
            raise RuntimeError("unknown edit kind %r" % (e[0],))
    return touched


def run_gate(rel, expect_exit, expect_id):
    p = subprocess.run([sys.executable, path(rel)], cwd=REPO,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode("utf-8", "replace")
    hit = (expect_id is None) or (expect_id in out)
    return p.returncode, hit, out


def main():
    lines = []

    def w(s):
        lines.append(s)
        print(s)

    # 记录 8 个被改文件的原始字节（复原用）
    before = {rel: read_bytes(rel) for rel in FILES}
    before_sha = {rel: sha(rel) for rel in FILES}
    w("== bgfinal3 扰动实测矩阵 ==")
    w("扰动前 SHA256（8 个文件）：")
    for rel in FILES:
        w("  %s  %s" % (before_sha[rel], rel))

    mismatches = 0
    rows = 0
    for cid, desc, edits, checks in CASES:
        touched = []
        setup_fail = None
        try:
            touched = apply_case(edits)
        except Exception as exc:  # noqa: BLE001
            setup_fail = str(exc)
        w("")
        w("---- [%s] %s" % (cid, desc))
        if setup_fail:
            mismatches += 1
            w("     SETUP-FAIL（扰动没生效，不算命中）: %s" % setup_fail)
        for rel, expect_exit, expect_id in checks:
            if setup_fail:
                w("     %-34s exit=-- hit_expected=--  SKIPPED" % os.path.basename(rel))
                continue
            rows += 1
            code, hit, out = run_gate(rel, expect_exit, expect_id)
            ok = (code == expect_exit) and hit
            if not ok:
                mismatches += 1
            w("     %-34s exit=%d (期望 %d) hit_expected=%s  %s"
              % (os.path.basename(rel), code, expect_exit, hit, "OK" if ok else "MISMATCH"))
            if not ok:
                for ln in out.splitlines():
                    if "FAIL" in ln or "Traceback" in ln:
                        w("        | " + ln[:200])
        # 逐字节复原 + 自证
        for rel in FILES:
            write_bytes(rel, before[rel])
        bad = [rel for rel in FILES if sha(rel) != before_sha[rel]]
        if bad:
            mismatches += 1
            w("     RESTORE-FAIL: %s" % bad)
        else:
            w("     复原 OK（%d 个文件 SHA256 逐行相同）" % len(FILES))

    # 收尾基线
    w("")
    w("---- [FINAL-BASE] 收尾基线（全部复原后）")
    for rel in (VTRIM, VASSETS, VDATA, VADV):
        code, hit, out = run_gate(rel, 0, None)
        rows += 1
        if code != 0:
            mismatches += 1
        w("     %-34s exit=%d (期望 0) %s" % (os.path.basename(rel), code, "OK" if code == 0 else "MISMATCH"))
        if code != 0:
            for ln in out.splitlines():
                if "FAIL" in ln:
                    w("        | " + ln[:200])

    w("")
    w("== 汇总：用例行数 %d / mismatches %d ==" % (rows, mismatches))
    w("== 8 个文件最终 SHA256（应与扰动前逐行相同）==")
    for rel in FILES:
        now = sha(rel)
        w("  %s  %s  %s" % (now, "SAME" if now == before_sha[rel] else "DIFF!!", rel))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("\n[写出] %s" % OUT)
    return 1 if mismatches else 0


if __name__ == "__main__":
    # 取 HEAD 版 indigoseagold.png（= quartz 白灰阶，101 B）当"换回 quartz"的扰动用例
    r = subprocess.run(["git", "show", "HEAD:" + PALETTE.replace("\\", "/")],
                       cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise SystemExit("拿不到 HEAD 版色卡: " + r.stderr.decode("utf-8", "replace"))
    QUARTZ_101 = r.stdout
    print("HEAD 版 indigoseagold.png（quartz 白灰阶）: %d B sha256=%s"
          % (len(QUARTZ_101), hashlib.sha256(QUARTZ_101).hexdigest()))
    raise SystemExit(main())
