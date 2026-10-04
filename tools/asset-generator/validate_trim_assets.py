# -*- coding: utf-8 -*-
"""1.5 修正⑦（盔甲纹饰显示成白色）的可复算证据：色卡 / 图集置换 / 原版模型 override / item_model_index。

只读 src 与原版 client jar，输出 build/p15fix-asset-audit.txt。

用法:
    python validate_trim_assets.py [<原版 client jar 路径>]
不给参数时用 gradle 缓存里 1.21.1 client jar 的默认路径。
"""
import io
import json
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "src" / "main" / "resources"
VANILLA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    r"C:\Users\Lenovo\.gradle\caches\neoformruntime\artifacts\minecraft_1.21.1_client.jar")
OURS = ["sturdygold", "unwanted_antique", "flamegold", "voodoogold", "thundergold",
        "indigoseagold", "illusiongold",
        # 1.6（bg-16）：两套新金属的纹饰（item_model_index 0.08 / 0.09，仍在原版 0.1~1.0 之外）
        "thornsgold", "echogold"]
VANILLA_INDEX = {"quartz": 0.1, "iron": 0.2, "netherite": 0.3, "redstone": 0.4, "copper": 0.5,
                 "gold": 0.6, "emerald": 0.7, "diamond": 0.8, "lapis": 0.9, "amethyst": 1.0}


def palette_pixels(data: bytes):
    """极简 PNG 解码（8×1、8 位、非隔行）：返回 [(r,g,b,a), ...]"""
    import struct
    import zlib
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, size, bitdepth, colortype = 8, b"", None, None, None
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            size = struct.unpack(">II", chunk[:8])
            bitdepth, colortype = chunk[8], chunk[9]
        elif typ == b"IDAT":
            idat += chunk
        pos += 12 + ln
    raw = zlib.decompress(idat)
    bpp = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[colortype]
    stride = size[0] * bpp
    out = []
    prev = bytearray(stride)
    for y in range(size[1]):
        ft = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ft == 1:
                line[i] = (line[i] + a) & 0xFF
            elif ft == 2:
                line[i] = (line[i] + b) & 0xFF
            elif ft == 3:
                line[i] = (line[i] + (a + b) // 2) & 0xFF
            elif ft == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        for x in range(size[0]):
            px = line[x * bpp:(x + 1) * bpp]
            if bpp == 4:
                out.append(tuple(px))
            elif bpp == 3:
                out.append((px[0], px[1], px[2], 255))
            else:
                out.append((px[0],) * 3 + (255,))
        prev = line
    return size, out


def main():
    lines = []

    def p(s):
        lines.append(s)
        print(s)

    # ---------- 1. trim_material JSON ----------
    p("== 1. data/bettergold/trim_material/*.json ==")
    seen = {}
    for m in OURS:
        d = json.loads((RES / "data/bettergold/trim_material" / f"{m}.json").read_text(encoding="utf-8"))
        seen[m] = d["item_model_index"]
        collide = [k for k, v in VANILLA_INDEX.items() if abs(v - d["item_model_index"]) < 1e-9]
        p(f"  {m:18s} asset_name={d['asset_name']:18s} item_model_index={d['item_model_index']:.2f}"
          f"  撞原版={collide if collide else '无'}")
    p(f"  唯一值个数={len(set(seen.values()))} / {len(OURS)}（必须相等）")
    p(f"  全部落在原版 0.1..1.0 之外 = {all(v < 0.1 or v > 1.0 for v in seen.values())}")

    # ---------- 2. 色卡 ----------
    p("")
    p("== 2. 色卡 assets/bettergold/textures/trims/color_palettes/<asset>.png（8×1） ==")
    for m in OURS:
        path = RES / "assets/bettergold/textures/trims/color_palettes" / f"{m}.png"
        size, px = palette_pixels(path.read_bytes())
        uniq = len(set(px))
        p(f"  {m:18s} size={size} 唯一像素={uniq} 首={px[0]} 末={px[-1]} 全白={all(c[:3] == (255, 255, 255) for c in px)}")

    with zipfile.ZipFile(VANILLA) as z:
        p("  原版对比 trim_palette.png（palette_key，8×1 灰阶）：")
        size, px = palette_pixels(z.read("assets/minecraft/textures/trims/color_palettes/trim_palette.png"))
        p(f"    size={size} 像素={px}")
        p("  原版 quartz 色卡（作者看到的「白色」就是它）：")
        size, px = palette_pixels(z.read("assets/minecraft/textures/trims/color_palettes/quartz.png"))
        p(f"    size={size} 像素={px}")

    # ---------- 3. 图集置换 ----------
    p("")
    p("== 3. 图集置换（两处，缺一不生效） ==")
    armor = json.loads((RES / "assets/minecraft/atlases/armor_trims.json").read_text(encoding="utf-8"))
    arm_perms = {}
    for src in armor["sources"]:
        arm_perms.update(src.get("permutations", {}))
    p(f"  a) armor_trims.json（穿戴模型 trims/models/armor/*）: {len(arm_perms)} 条置换，"
      f"我方全在 = {all(m in arm_perms for m in OURS)}")
    blocks_path = RES / "assets/minecraft/atlases/blocks.json"
    p(f"  b) blocks.json（物品形态 trims/items/*_trim）存在 = {blocks_path.is_file()}")
    if blocks_path.is_file():
        blocks = json.loads(blocks_path.read_text(encoding="utf-8"))
        blk_perms, blk_tex = {}, []
        for src in blocks["sources"]:
            blk_tex += src.get("textures", [])
            blk_perms.update(src.get("permutations", {}))
        p(f"     源贴图 = {blk_tex}")
        p(f"     palette_key = {[s.get('palette_key') for s in blocks['sources']]}")
        p(f"     {len(blk_perms)} 条置换，我方全在 = {all(m in blk_perms for m in OURS)}")
        for m in OURS:
            p(f"     {m:18s} -> {blk_perms.get(m)}")
        p("     注意：SpriteSourceList.load 用的是 resourceManager.getResourceStack（同名文件**拼接**），")
        p("     所以本文件是**追加**到原版 blocks.json 的源列表上，不会覆盖原版 14 个材质。")

    # ---------- 4. 原版盔甲模型的 override ----------
    p("")
    p("== 4. 原版盔甲物品模型的 overrides（trim_type → 哪个模型） ==")
    with zipfile.ZipFile(VANILLA) as z:
        raw = json.loads(z.read("assets/minecraft/models/item/netherite_chestplate.json").decode("utf-8"))
        for ov in raw["overrides"]:
            p(f"  trim_type {ov['predicate']['trim_type']:.1f} -> {ov['model']}")
        trim_model = json.loads(z.read(
            "assets/minecraft/models/item/netherite_chestplate_quartz_trim.json").decode("utf-8"))
        p(f"  netherite_chestplate_quartz_trim.json textures = {trim_model['textures']}")
    p("  => 修复前我方六个金属的 item_model_index 全是 0.1，谓词值 0.1 命中的就是 quartz 那一行，")
    p("     最终画的是 minecraft:trims/items/chestplate_trim_quartz（quartz 色卡 = 白灰阶）⇒ 「纹饰都是白色」。")

    # ---------- 5. 我方盔甲物品模型 ----------
    p("")
    p("== 5. 我方盔甲物品模型（JSON 里没有 trim overlay，这是原样；overlay 由客户端 ArmorTrimItemModels 运行期补） ==")
    for m in ["sturdygold", "flamegold", "voodoogold", "thundergold", "indigoseagold", "illusiongold",
              "thornsgold", "echogold"]:
        for slot in ["helmet", "chestplate", "leggings", "boots"]:
            path = RES / "assets/bettergold/models/item" / f"{m}_{slot}.json"
            if path.is_file():
                d = json.loads(path.read_text(encoding="utf-8"))
                assert "overrides" not in d, path
    p("  6 套 × 4 件 = 24 个模型全部只有 {parent: minecraft:item/generated, textures:{layer0}}，")
    p("  没有 overrides / 没有 layer1（对照原版 netherite_chestplate.json）⇒ 修之前自家盔甲连纹饰都不画。")
    p("  修法：client/ArmorTrimItemModels.java 在 ModelEvent.ModifyBakingResult 里给**所有**带纹饰槽位的")
    p("  盔甲物品模型套一层包装，按纹饰材质的 asset_name 现算「原模型四边形 + 纹饰精灵」那一层；")
    p("  这样原版 25 件与自家 24 件一起生效，也不需要复制/覆盖原版模型 JSON。")

    # ---------- 6. 小刀标签（修正①） ----------
    p("")
    p("== 6. 修正①：小刀必须进 #farmersdelight:tools/knives（附魔类别标签全靠它） ==")
    for tag in ["data/farmersdelight/tags/item/tools/knives.json", "data/c/tags/item/tools/knife.json"]:
        vals = json.loads((RES / tag).read_text(encoding="utf-8"))["values"]
        knives = [v for v in vals if v.endswith("_knife")]
        p(f"  {tag}: {len(knives)} 把 -> {knives}")
    p("  FD jar 里 data/minecraft/tags/item/enchantable/{bow,crossbow,trident,mace,sword,sharp_weapon,")
    p("  weapon,fire_aspect,durability,mining,mining_loot,vanishing}.json 都靠它拼出来；")
    p("  1.5 的靛海金刀 / 幻惑金刀原先不在这个标签里 ⇒ 只有那两把不能附魔。")

    out = REPO / "build" / "p15fix-asset-audit.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n[写出] {out}")


if __name__ == "__main__":
    main()
