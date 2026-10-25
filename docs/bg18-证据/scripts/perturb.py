# -*- coding: utf-8 -*-
"""bg18 扰动矩阵（最小集，但每条都「能红」+ 逐字节复原 + SHA256 自证）。

用例：
  P1  手册正文改一个字（zh）            => [bg18-verbatim] 红
  P2a 把熔炉页与工作台页换回旧顺序      => [bgbig-spread] / [bgbig-pages] 红
  P2b 把一个 `%%` 改回 `%`              => [bg18-percent] 红
  P2c getSerializer 改回恒返回金锭序列化器 => [bg18-cowrie-mold] 红
  P3  删掉 `victim == caster`           => [bg18-echo-roar] 红
  P4  九宫格第 2 行第 1 列换成金锭      => [bg18-grid] 红
  Z   只在生成器里加一行注释           => 仍 exit 0（反向对照）

跑法： py -3 probe\\bg18\\perturb.py
"""
import hashlib
import io
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VAL = os.path.join(ROOT, "tools", "asset-generator", "validate_metal_data.py")
ZH = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "lang", "zh_cn.json")
GEN = os.path.join(ROOT, "tools", "asset-generator", "generate_handbook_data.py")
REC = os.path.join(ROOT, "src", "main", "resources", "data", "bettergold", "recipe")
MOLD = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "recipe",
                    "GoldenCowrieMoldRecipe.java")
EV = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "material",
                  "MetalEvents.java")
RS = os.path.join(ROOT, "src", "main", "java", "com", "hjmmd_8", "bettergold", "recipe",
                  "RawSturdygoldRecipe.java")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest().upper()


def run_val():
    p = subprocess.run([sys.executable, VAL], capture_output=True)
    out = p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")
    return p.returncode, out


def case(name, path, old, new, expect_tag):
    before = open(path, "rb").read()
    before_sha = hashlib.sha256(before).hexdigest().upper()
    text = before.decode("utf-8")
    if text.count(old) != 1:
        print("[%s] 变更未生效（old 出现 %d 次）—— 用例坏了" % (name, text.count(old)))
        return False
    open(path, "wb").write(text.replace(old, new).encode("utf-8"))
    code, out = run_val()
    hit = expect_tag in out and code == 1
    open(path, "wb").write(before)                     # 逐字节复原
    restored = hashlib.sha256(open(path, "rb").read()).hexdigest().upper()
    ok = hit and restored == before_sha
    print("[%s] val_exit=%d hit_expected=%s restored_sha_match=%s %s"
          % (name, code, hit, restored == before_sha, "PASS" if ok else "FAIL"))
    return ok


def main():
    good = []
    good.append(case("P1-verbatim", ZH,
                     "想要让你获取“贵金”的效率更高吗",
                     "想要让你获取“贵金”的效率更高吗？", "[bg18-verbatim]"))
    good.append(case("P2b-percent", ZH, "还有50%%的几率施加力量失衡", "还有50%的几率施加力量失衡",
                     "[bg18-percent]"))
    good.append(case("P2c-serializer", MOLD,
                     "return this.variant == 1", "return false && this.variant == 1",
                     "[bg18-cowrie-mold]"))
    good.append(case("P3-caster-skip", EV, "if (victim == caster) {", "if (false) {",
                     "[bg18-echo-roar]"))
    good.append(case("P4-grid-cell", RS,
                     "Ingredient.of(Items.NETHERITE_SCRAP),\n                    Ingredient.of(Items.GOLD_INGOT),",
                     "Ingredient.of(Items.GOLD_INGOT),\n                    Ingredient.of(Items.GOLD_INGOT),",
                     "[bg18-grid]"))
    # P2a：把第 1 页右（文案）与熔炉页换位（模拟"拆回旧顺序"）
    p2a = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "patchouli_books",
                       "alchemy_handbook", "zh_cn", "entries", "prison_chaosgold_main.json")
    before = open(p2a, "rb").read()
    before_sha = hashlib.sha256(before).hexdigest().upper()
    data = json.loads(before.decode("utf-8"))
    pages = data["pages"]
    pages[1], pages[2] = pages[2], pages[1]
    open(p2a, "w", encoding="utf-8", newline="\n").write(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    code, out = run_val()
    hit = ("[bgbig-spread]" in out) and code == 1
    open(p2a, "wb").write(before)
    restored = hashlib.sha256(open(p2a, "rb").read()).hexdigest().upper()
    print("[P2a-spread] val_exit=%d hit_expected=%s restored_sha_match=%s %s"
          % (code, hit, restored == before_sha, "PASS" if hit and restored == before_sha else "FAIL"))
    good.append(hit and restored == before_sha)
    # Z：只改生成器注释 ⇒ 仍 exit 0
    before = open(GEN, "rb").read()
    before_sha = hashlib.sha256(before).hexdigest().upper()
    text = before.decode("utf-8")
    open(GEN, "wb").write(text.replace(
        "# --------------------------------------------------------------------------------------\n# ★★ 1.7 `bg18`",
        "# ---- (perturb Z: comment only) --------------------------------------------------------\n"
        "# --------------------------------------------------------------------------------------\n# ★★ 1.7 `bg18`", 1).encode("utf-8"))
    code, out = run_val()
    open(GEN, "wb").write(before)
    restored = hashlib.sha256(open(GEN, "rb").read()).hexdigest().upper()
    print("[Z-comment-only] val_exit=%d (expect 0) restored_sha_match=%s"
          % (code, restored == before_sha))
    good.append(code == 0 and restored == before_sha)
    print("用例 %d / 命中 %d" % (len(good), sum(1 for g in good if g)))
    return 0 if all(good) else 1


if __name__ == "__main__":
    sys.exit(main())
