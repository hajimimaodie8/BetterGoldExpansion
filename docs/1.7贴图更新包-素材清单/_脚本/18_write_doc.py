# -*- coding: utf-8 -*-
"""生成 docs/1.7-贴图更新包翻新.md —— 第五次贴图授权的落档（SHA 表从证据文件读取，避免手抄）。"""
import sys, os
sys.stdout.reconfigure(errors="replace")

BASE = r"E:\mc\mcmod\bettergold-template-1.21.1"
ARCH = os.path.join(BASE, "docs", "1.7贴图更新包-素材清单")
EVID = os.path.join(ARCH, "_证据", "替换记录")
OUT = os.path.join(BASE, "docs", "1.7-贴图更新包翻新.md")

GROUPS = [
    ("block/<族>_lantern.png", "灯笼 · 方块放置样式（16×48 动画条）", "lantern"),
    ("models/armor/<族>_layer_1.png", "盔甲穿戴层 · 靴子区（64×32，改动全在 leg_boot UV 区）", "armor_l1"),
    ("item/<族>_axe.png", "斧 · 物品图标", "axe"),
    ("item/<族>_shovel.png", "锹 · 物品图标", "shovel"),
    ("item/<族>_knife.png", "刀 · 物品图标", "knife"),
    ("block/<族>_chain.png", "链 · 方块/放置样式（「两种样式」之一）", "chain_block"),
    ("item/<族>_chain.png", "链 · 物品图标样式（「两种样式」之二）", "chain_item"),
    ("block/<族>_bars.png", "栏杆", "bars"),
    ("item/<族>_leggings.png", "护腿 · 物品图标样式", "leggings"),
]


def load_tsv(p):
    with open(p, encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        return [dict(zip(hdr, l.rstrip("\n").split("\t"))) for l in f if l.strip()]


def main():
    recs = load_tsv(os.path.join(EVID, "替换记录.tsv"))
    ident = load_tsv(os.path.join(ARCH, "认亲表.tsv"))
    idmap = {r["target"]: r for r in ident}
    before = load_tsv(os.path.join(EVID, "textures_before.tsv")) if False else None

    killed = load_tsv(os.path.join(ARCH, "素材清单.tsv"))
    from collections import Counter
    c = Counter("%sx%s/%s" % (r["width"], r["height"], r["mode"]) for r in killed)

    L = []
    A = L.append
    A("# 1.7 贴图更新包翻新 —— 第五次贴图授权落档\n")
    A("> 作者 2026-10-17 交付 `E:\\mc\\mc资料\\1.7的贴图更新包.zip`（72 张，**文件名全是数字、无名字**），")
    A("> 要求**按像素匹配认出每一张是谁**，再翻新对应贴图。本文件是入库、认亲、替换、验证的完整记录。\n")
    A("## §0 素材与红线\n")
    A("- 来源 zip：`E:\\mc\\mc资料\\1.7的贴图更新包.zip`（46,334 B，72 个 PNG 条目）")
    A("- **硬红线（永久，作者原话「你不要动原文件，你不要改变原来的压缩包哈」）**：**绝不修改 / 重打包 / 改名 / 移动**")
    A("  原始 zip 与 zip 内任何文件；只许**只读**解压到 `docs\\` 归档，归档副本**只增不改**。")
    A("  本轮实现方式：`zipfile.ZipFile(SRC, \"r\")` 全程只读；归档写入前先 `os.path.exists` 判存，存在即 skip。")
    A("- 归档落点：`docs\\1.7贴图更新包-素材清单\\`（72 张原样数字名 + `素材清单.tsv` + `认亲表.tsv/.md` + `_识别证据\\` + `_脚本\\`）\n")
    A("## §1 入库清单\n")
    A("尺寸构成（全部 RGBA）：" + "、".join("`%s` %d 张" % (k, v) for k, v in sorted(c.items())) + "。")
    A("包内**重复 SHA256 = 0**；与原仓库贴图**精确哈希全等 = 0**（说明确实是翻新版而非原图重发）。\n")
    A("## §2 认亲方法（可复算）\n")
    A("1. **精确层**：SHA256 全等 → 分数 1.0。本轮 0 条。")
    A("2. **像素层**：同尺寸前提下，对每个 (zip 文件, 候选目标) 对算")
    A("   **逐像素 RGBA 平均绝对误差 `MAE = mean(|A - B|)`**（含 alpha 通道）。")
    A("3. **指派层**：同尺寸类内用 `scipy.optimize.linear_sum_assignment` 做**全局一对一指派**（最大化 -MAE），")
    A("   每个目标恰好被一张 zip 认领 ⇒ 天然给出「与第二名的差距」`ratio = 2nd_MAE / best_MAE`。")
    A("4. **三条硬校验**（同时满足才算「确定」）：`MAE <= 2.0`、`ratio >= 1.5`、")
    A("   **与目标的 alpha 掩码逐字节相同且不透明像素数相同**（= 同一条美术血脉）。")
    A("5. **候选集**：A = 仓库 `src/main/resources/assets/bettergold/textures/**`（626 个文件）；")
    A("   B = `docs\\新约10-素材清单\\新约10\\**`（上一包 94 张，作语义交叉验证）；")
    A("   C = 原版 jar 内贴图（⚠ 本机**没有** 1.21.1 客户端 jar，用")
    A("   `~/.gradle/caches/forge_gradle/minecraft_repo/versions/1.20.1/client-extra.jar` 的 2431 张，")
    A("   仅用于「排除这不是我们的」）。\n")
    A("**结果：72 张全部判为「确定」，0 疑似，0 认不出。** 每张的 MAE 都 `<= 1.88`，")
    A("对原版的最小 MAE 是 `3.99–45.1`（差 2–40 倍）；类内次优差距 `1.8x–75.5x`。")
    A("**族顺序在 9 个类里完全一致**（flame → sturdy → thorns → echo → indigo → voodoo → thunder → illusion），")
    A("这是第 4 条独立佐证 —— 其中 7 个类的类内差距是 4–75 倍，足以锚定这个顺序。")
    A("逐张认亲表见 `docs\\1.7贴图更新包-素材清单\\认亲表.md`（142 行）。\n")
    A("### §2.1 「两种样式」的实测落点\n")
    A("作者说「斧 / 锹 / 刀 / 链 的**两种样式**」。实测：**只有「链」在本包里真的有两套**，且各自对应不同目标文件 ——\n")
    A("| 样式 | 目标文件 | 8 张该组的 MAE | 对另一个样式目标的 MAE |")
    A("|---|---|---|---|")
    A("| 链 · 方块/放置样式 | `block/<族>_chain.png` | 1.18–1.40 | 47–57（跨类差 **40 倍以上**） |")
    A("| 链 · 物品图标样式 | `item/<族>_chain.png` | 0.47–0.85 | 47–53 |\n")
    A("**斧 / 锹 / 刀 在本包里各只有 1 套（物品图标）**，且全仓 `textures/**` 里也没有它们的第二张贴图")
    A("（无任何 `*_in_hand`；武器 in-hand 只有三叉戟走 3D 模型）。⇒ 已列入「待作者确认」。\n")
    A("### §2.2 「翻新」的实际形态（影响验收口径）\n")
    A("72 张全部 **alpha 掩码逐字节相同、不透明像素数完全相同 ⇒ 剪影/轮廓零改动**。")
    A("改动只发生在**内部少数像素的颜色值**，且只在**同一族调色板内部换档**")
    A("（例：axe `(234,172,63) → (202,101,0)`、`(202,102,0) → (175,75,0)`；")
    A("bars/knife 一律变暗，chain_block/lantern 明暗互换）。\n")
    A("| 类 | 每张改动像素数 | 改动坐标是否 8 族一致 | alpha 变化 |")
    A("|---|---|---|---|")
    A("| axe | 10 | 是 | 0 |")
    A("| shovel | 2 | 是 | 0 |")
    A("| knife | 14 | 是 | 0 |")
    A("| chain（方块） | 16 | 是 | 0 |")
    A("| chain（物品） | 9 | 是 | 0 |")
    A("| bars | 17 | 是 | 0 |")
    A("| leggings | 7 | 是 | 0 |")
    A("| lantern | 18 | 是 | 0 |")
    A("| armor layer_1 | 12 | 是 | 0 |\n")
    A("**840 处改动 100% 落在 `alpha = 255` 的可见像素上，0 处落在透明区**")
    A("（若是重新导出的空改，改动会落在 alpha=0 处）⇒ 是真·可见的**定点阴影修正**，不是重绘。")
    A("⇒ 若作者预期是造型大改，需他确认。\n")
    A("### §2.3 「靴子」的落点验证\n")
    A("armor 组 8 张：与 `models/armor/<族>_layer_1.png` 的 MAE = **0.15–0.23**，")
    A("而与本族 `_layer_2.png` 的 MAE = **48.9–72.4**（均 59.0）⇒ **只该动 layer_1，不该动 layer_2**。")
    A("且**改动 96 个像素 100% 落在 layer_1 的 `leg_boot` UV 区（x 0–15, y 25–26）**，")
    A("头部 / 身体 / 手臂区一个像素没动 ⇒ 与作者原话「盔甲穿戴部分的靴子」完全吻合。\n")
    A("## §3 替换记录（72 张，改前 → 改后 SHA256）\n")
    A("方式：**1:1 字节复制**（`shutil.copyfile`），源 = `docs\\` 归档副本；")
    A("复制前先断言「归档副本 SHA == 原 zip 内条目 SHA」，复制后再断言「目标 SHA == 原 zip 内条目 SHA」。")
    A("**不改文件名大小写、不改路径。**\n")
    FAMILIES = ["flamegold", "sturdygold", "thornsgold", "echogold",
                "indigoseagold", "voodoogold", "thundergold", "illusiongold"]
    bypath = {r["target"]: r for r in recs}
    for pat, title, _k in GROUPS:
        sel = []
        for fam in FAMILIES:
            t = pat.replace("<族>", fam)
            if t in bypath:
                sel.append(bypath[t])
        A("### %s（%d 张）\n" % (title, len(sel)))
        A("| 数字文件名 | 目标 | 改前 SHA256 | 改后 SHA256 | MAE |")
        A("|---|---|---|---|---|")
        for r in sorted(sel, key=lambda x: x["target"]):
            i = idmap.get(r["target"], {})
            A("| `%s` | `%s` | `%s` | `%s` | %s |"
              % (r["zipfile"], r["target"], r["sha_before"], r["sha_after"], i.get("MAE", "?")))
        A("")
    A("合计 **72 张**，`M` 计数 = **72**，其余贴图 `626 - 72 = 554` 张哈希**一个字节未变**。")
    A("完整机读版：`docs\\1.7贴图更新包-素材清单\\_证据\\替换记录\\替换记录.tsv`；")
    A("替换前 / 替换后全树快照：同目录 `textures_before.tsv` / `textures_after.tsv`。\n")
    A("### §3.1 与既有 SHA 锚点的关系\n")
    A("两条既有锚点**都不在**本轮 72 张范围内，实测未受影响：\n")
    A("| 锚点 | SHA256 | 本轮状态 |")
    A("|---|---|---|")
    A("| `item/golden_trident_blank.png` | `73e4df0f098dced43d43f8529a7aa07c702e63e5aacd70d99a25fdfbb1e6f5b6` | 未变 |")
    A("| `trims/color_palettes/indigoseagold.png` | `9c966b7f80c2e2550064a822730a704e8a68aeac9047fa9f1aabfda7eb9e6b6d` | 未变 |\n")
    A("## §4 关卡与扰动\n")
    A("关卡 = `tools\\asset-generator\\validate_bg17_textures.py`（新增，不改既有六个校验器）。")
    A("清单 = `tools\\asset-generator\\bg17tex_manifest.tsv`（626 行，`role` 列区分 authorized/untouched）")
    A("+ `bg17tex_old_sha.tsv`（72 行改前 SHA，用于「不得回退」）。\n")
    A("检查项：")
    A("- ① 72 张授权替换：SHA == 钉住的改后 SHA，且 **!= 改前 SHA**（`[bg17tex-revert]` 反空转）")
    A("- ② 554 张未授权：负向断言，一个字节变红（`[bg17tex-untouched-fail]`）")
    A("- ③ 两条既有锚点不动（`[bg16-authorized-blank-texture]` / `[bgfinal3-indigosea-sha]`）")
    A("  + 色卡「不是白灰阶」负向（`[bgfinal3-indigosea-not-quartz]`）")
    A("- ④ 正向 needle：被替换的 64 张（非盔甲）仍被模型 JSON 引用（`[bg17tex-model-ref]`）")
    A("- ⑤ 正向 needle 跑在**去注释源码**上：`MetalFamily.java` 剥掉 `//` 与 `/* */` 后仍含")
    A("  `ArmorMaterial.Layer` + `ResourceLocation.fromNamespaceAndPath(bettergold.MODID, this.id)`")
    A("  （盔甲层命名约定 `models/armor/<id>_layer_1` 的来源）")
    A("- 反空转：`checked` 必须 `>= 626`，否则 **exit 2**（不是 0）；未捕获异常 → exit 2\n")
    A("扰动矩阵（`docs\\1.7贴图更新包-素材清单\\_脚本\\17_perturb.py`，9 例全 PASS）：\n")
    A("| 用例 | want_exit | got_exit | 结果 |")
    A("|---|---|---|---|")
    A("| P0 基线 | 0 | 0 | PASS |")
    A("| P1 把某张授权贴图覆盖成别的字节 | 1 | 1 | PASS |")
    A("| P2 改一张「没授权」的贴图（动 1 个字节） | 1 | 1 | PASS |")
    A("| P3 只改注释 / 只加空行（`MetalFamily.java` 尾部） | 0 | 0 | PASS |")
    A("| P3b needle 只出现在注释里 → 去注释后必须找不到 | 1 | 1 | PASS |")
    A("| P3c 同一 needle 写进代码 → 必须找得到 | 1 | 1 | PASS |")
    A("| P4 删掉一张授权贴图（前置缺失） | 1 | 1 | PASS |")
    A("| P5 清单文件搬走（基线被破坏） | 2 | 2 | PASS |")
    A("| P9 复归基线仍绿 | 0 | 0 | PASS |\n")
    A("每例都**逐字节复原并复核 SHA256**（P1 `ad8a60c3…`、P2 `c172cf08…`、P3 `87edd699…`、P4 `a9ed1072…`、")
    A("P5 清单 `d0debaed…` 全部复原成功）。`MetalFamily.java` 的扰动采用「写前比对」保护：")
    A("若在扰动窗口内被别人改过则立即中止、不做覆盖式复原。\n")
    A("## §5 待作者确认 / 人眼项\n")
    A("**待作者确认（不硬塞）**：")
    A("1. 斧 / 锹 / 刀 是否还有**第二套样式**？本包只到物品图标那 1 套（3×8 = 24 张）；")
    A("   若他确实画了第二套，本包缺这 24 张。")
    A("2. 「翻新」是否就是这种**定点阴影修正**（剪影零改动、每张只动 2–18 个内部像素）？")
    A("   若他预期是造型大改，则本包与预期不符。")
    A("3. `gold` 与 `chaosgold` 两族的灯笼**不在包内**（他只给 8 个贵金族），是否需要？\n")
    A("**只能作者看的人眼项**：灯笼放置样式 / 斧锹刀链的两种样式 / 栏杆 / 护腿物品样式 / 靴子穿戴层")
    A("—— 好不好看只有作者能判；本轮只保证「换进去的就是他给的那张字节」。\n")
    A("## §6 经验回流\n")
    A("见 `E:\\mc\\mcmod\\mod_experience\\` 的对应节与附录 D「回流日志」。\n")
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("[doc] wrote %s  lines=%d" % (OUT, len(L)))


if __name__ == "__main__":
    main()
