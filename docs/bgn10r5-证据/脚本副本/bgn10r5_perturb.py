# -*- coding: utf-8 -*-
"""轮5 扰动矩阵：证明 [bgn10r5-*] 门禁"能红"，且只改注释仍是绿的。
每个用例：备份字节 -> 改 -> 跑 validate_metal_data.py（只看 exit 与命中 tag）-> 逐字节复原 -> SHA256 自证。
用法：py -3 bgn10r5_perturb.py
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = Path(__file__).resolve().parents[3]
JAVA = REPO / "src/main/java/com/hjmmd_8/bettergold"
RES = REPO / "src/main/resources"
VALIDATOR = REPO / "tools/asset-generator/validate_metal_data.py"
OUT = REPO / "docs/bgn10r5-证据/03-扰动矩阵.txt"

FLOWER = JAVA / "block/GoldenTorchflowerBlock.java"
CROP = JAVA / "block/GoldenTorchflowerCropBlock.java"
METAL_EVENTS = JAVA / "material/MetalEvents.java"
TEX = RES / "assets/bettergold/textures/item/refined_alchemic_oil.png"
EN = RES / "assets/bettergold/lang/en_us.json"

LOG = ["# 轮5 扰动矩阵（每个用例：改 -> 跑 -> 复原 -> SHA256 自证）\n"]
RESULTS = []


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest().upper()


def run_validator():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, str(VALIDATOR)], cwd=str(REPO),
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def record(name, code, want_exit, tag_hit, same, ok, out, want_tag):
    line = ("%-48s exit=%-2d want_exit=%-2d tag_hit=%-5s restored_sha_ok=%-5s => %s"
            % (name, code, want_exit, tag_hit, same, "HIT" if ok else "MISS"))
    print(line)
    LOG.append(line)
    if want_tag:
        for ln in out.splitlines():
            if want_tag in ln:
                LOG.append("    └ " + ln.strip()[:320])
                break
    RESULTS.append(ok)


def case_bytes(name, path, mutate, want_tag, want_exit):
    """通用：备份 <path> 的字节 -> mutate() -> 跑 -> 写回备份 -> SHA 自证。"""
    before = Path(path).read_bytes()
    mutate()
    code, out = run_validator()
    Path(path).write_bytes(before)
    same = sha_bytes(before) == hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()
    hit = (want_tag in out) if want_tag else True
    record(name, code, want_exit, hit if want_tag else "-", same,
           (code == want_exit) and hit, out, want_tag)


def replace_once(path, old, new):
    t = Path(path).read_bytes().decode("utf-8")
    if old not in t:
        raise SystemExit("[perturb] needle not found in %s: %r" % (Path(path).name, old))
    return t.replace(old, new, 1).encode("utf-8")


def main():
    # ① 亮度：把喂引擎的值改回作者原数 16
    case_bytes("① ENGINE_LIGHT 改回 AUTHOR_LIGHT(16)", FLOWER,
               lambda: FLOWER.write_bytes(replace_once(
                   FLOWER, "ENGINE_LIGHT = Math.min(15, AUTHOR_LIGHT)", "ENGINE_LIGHT = AUTHOR_LIGHT")),
               "[bgn10r5-light]", 1)

    # ② 作物状态定义：add(AGE) 换成 add(AGE_7)
    case_bytes("② createBlockStateDefinition 改回 add(AGE_7)", CROP,
               lambda: CROP.write_bytes(replace_once(
                   CROP, "builder.add(AGE);",
                   "builder.add(net.minecraft.world.level.block.state.properties.BlockStateProperties.AGE_7);")),
               "[bgn10r5-crop]", 1)

    # ③ 删一张贴图（改名 -> 跑 -> 改回）
    bak = TEX.with_name(TEX.name + ".bak")
    TEX.rename(bak)
    code, out = run_validator()
    bak.rename(TEX)
    same = hashlib.sha256(TEX.read_bytes()).hexdigest().upper() == (
        "D5858CD06AE5915F4141DABC1A84E34C1996BE4BEA774B22ECC8F860A557E0B9")
    record("③ 删掉 item/refined_alchemic_oil.png", code, 1,
           "[bgn10r5-textures]" in out, same,
           (code == 1) and ("[bgn10r5-textures]" in out), out, "[bgn10r5-textures]")

    # ④ 语言键：en 的一条改成与 zh 逐字相同
    case_bytes("④ en 值改成与 zh 相同", EN,
               lambda: EN.write_bytes(replace_once(
                   EN, '"item.bettergold.refined_alchemic_oil": "Refined Alchemic Oil"',
                   '"item.bettergold.refined_alchemic_oil": "高精度炼金油"')),
               "[bgn10r5-lang]", 1)

    # ⑤ 生产代码里塞一个 refined_alchemic_oil（模拟"偷偷实现翻倍"）
    def inject():
        t = METAL_EVENTS.read_bytes().decode("utf-8")
        i = t.rfind("}")
        METAL_EVENTS.write_bytes((t[:i]
                                  + "    // TEMP_PERTURB (扰动用，收尾已复原)\n"
                                  + "    public static final String R5_PROBE_ID = \"refined_alchemic_oil\";\n"
                                  + t[i:]).encode("utf-8"))

    case_bytes("⑤ MetalEvents 里塞 refined_alchemic_oil", METAL_EVENTS, inject,
               "[bgn10r5-double-yield]", 1)

    # ⑥ 反向对照：只加注释 + 空白 ⇒ 仍 exit 0
    case_bytes("⑥ 只加注释 / 空白（反向对照，应仍绿）", CROP,
               lambda: CROP.write_bytes(replace_once(
                   CROP, "public class GoldenTorchflowerCropBlock extends GoldCropBlock {",
                   "// TEMP_PERTURB: 只加一行注释与空行\n\n"
                   "public class GoldenTorchflowerCropBlock extends GoldCropBlock {")),
               "", 0)

    LOG.append("\n合计 %d/%d 命中（⑥ 是反向对照：期望 exit 0）\n"
               % (sum(1 for r in RESULTS if r), len(RESULTS)))
    OUT.write_text("\n".join(LOG) + "\n", encoding="utf-8", newline="\n")
    print("written", OUT)
    return 0 if all(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
