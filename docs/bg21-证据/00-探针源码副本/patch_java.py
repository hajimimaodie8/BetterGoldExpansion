#!/usr/bin/env python3
"""bg21 byte-level patch of CreativeTabSections.java (CRLF file) - temporary helper.

Every anchor is asserted to appear exactly once; the file is read/written as bytes
(never decoded with a lossy codec). Prints SHA256 before/after.
"""

import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
JAVA = REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "material" / "CreativeTabSections.java"

DOC_ANCHOR = "     * 「物品一个都不能丢」优先于顺序；真出现这种情况，自检里的逐元素比对会暴露出来。</p>\r\n"

DOC_INSERT = (
    "     *\r\n"
    "     * <p><b>最后一步是「紧邻钉」</b>：{@link #ADJACENCY_PINS} 的 5 条按声明顺序在<b>已经排好的列表</b>\r\n"
    "     * 上做「取出 → 插到锚点旁」，其余物品的相对次序原样保留（作者 2026-11-05 的 5 条顺序微调）。\r\n"
    "     * 锚点不在本分区时这一条什么都不做，所以同一张表可以同时喂 4 个分区。</p>\r\n"
)

BLOCK = (
    "\r\n"
    "    // ==================== 顺序微调：5 条「紧邻钉」（作者 2026-11-05） ====================\r\n"
    "\r\n"
    "    /**\r\n"
    "     * 一条「紧邻钉」：把物品 {@code item} 钉到 {@code anchor} 的<b>紧前面 / 紧后面</b>。\r\n"
    "     *\r\n"
    "     * <p>为什么需要它（而不只是改 {@link #MATERIAL_PREFIX_ORDER}）：本轮 5 条要求里有 3 条的\r\n"
    "     * <b>锚点在另一个段里</b> ——\r\n"
    "     * <ul>\r\n"
    "     *   <li>{@code chaos_coin_string} 要贴到 {@code chaos_coin}（金属段的混沌金核心材料）前面；</li>\r\n"
    "     *   <li>{@code money_gremlin_spawn_egg} 要贴到 {@code chaos_coin_string} 前面；</li>\r\n"
    "     *   <li>{@code sturdygold_anvil} 要贴到 {@code golden_creeper_figurine}（其他建筑方块的杂项表）前面。</li>\r\n"
    "     * </ul>\r\n"
    "     * 段 / 分区归属、注册、id、语言键一个都没动 —— 这里只在**已经排好的列表**上做「取出 → 插到锚点旁」，\r\n"
    "     * 其余物品的相对顺序原样保留（A 级读数用「去掉这 5 件后逐项相等」证明）。</p>\r\n"
    "     *\r\n"
    "     * <p>⚠ <b>声明顺序 = 应用顺序</b>：若 B 的锚点正是 A 自己，A 必须写在 B 前面\r\n"
    "     * （本表里 {@code money_gremlin_spawn_egg} 的锚点是 {@code chaos_coin_string}）。\r\n"
    "     * 关卡 {@code [bg21-creative-pins]} 静态守着这条链序。</p>\r\n"
    "     *\r\n"
    "     * <p>锚点 / 物品不在同一分区时什么都不做（不在这个分区的列表里就找不到，直接跳过）——\r\n"
    "     * 所以同一张表可以同时喂 4 个分区，且<b>永远不会把物品挪出它自己的分区</b>。</p>\r\n"
    "     */\r\n"
    "    public record Pin(String item, String anchor, boolean after) {\r\n"
    "    }\r\n"
    "\r\n"
    "    /**\r\n"
    "     * 创造页顺序的 5 条紧邻关系（作者 2026-11-05 原话，逐条对应；顺序 = 应用顺序）：\r\n"
    "     * <ol>\r\n"
    "     *   <li>「混沌金币串」往后放 ⇒ 放到「混沌金币」的<b>前面</b>；</li>\r\n"
    "     *   <li>「金钱妖刷怪蛋」移到「混沌金币串」的<b>前面</b>；</li>\r\n"
    "     *   <li>「高精度炼金油」放到「炼金燃油」的<b>后面</b>；</li>\r\n"
    "     *   <li>「金骨粉」放到「金质盾牌胚底」的<b>后面</b>；</li>\r\n"
    "     *   <li>「万坚金砧」移到「金雕苦力怕」的<b>前面</b>。</li>\r\n"
    "     * </ol>\r\n"
    "     */\r\n"
    "    public static final List<Pin> ADJACENCY_PINS = List.of(\r\n"
    "            new Pin(\"chaos_coin_string\", \"chaos_coin\", false),\r\n"
    "            new Pin(\"money_gremlin_spawn_egg\", \"chaos_coin_string\", false),\r\n"
    "            new Pin(\"refined_alchemic_oil\", \"alchemic_fuel\", true),\r\n"
    "            new Pin(\"golden_bone_meal\", \"golden_shield_blank\", true),\r\n"
    "            new Pin(\"sturdygold_anvil\", \"golden_creeper_figurine\", false));\r\n"
    "\r\n"
    "    /** 按 {@link #ADJACENCY_PINS} 的顺序把物品逐个「取出 → 插到锚点旁」；锚点不在本分区就原样放回（绝不丢物品） */\r\n"
    "    private static List<ItemStack> applyPins(List<ItemStack> base) {\r\n"
    "        List<ItemStack> out = new ArrayList<>(base);\r\n"
    "        for (Pin pin : ADJACENCY_PINS) {\r\n"
    "            int itemIndex = indexOfPath(out, pin.item());\r\n"
    "            if (itemIndex < 0) {\r\n"
    "                continue;\r\n"
    "            }\r\n"
    "            ItemStack moved = out.remove(itemIndex);\r\n"
    "            int anchorIndex = indexOfPath(out, pin.anchor());\r\n"
    "            if (anchorIndex < 0) {\r\n"
    "                out.add(Math.min(itemIndex, out.size()), moved);\r\n"
    "                continue;\r\n"
    "            }\r\n"
    "            out.add(pin.after() ? anchorIndex + 1 : anchorIndex, moved);\r\n"
    "        }\r\n"
    "        return out;\r\n"
    "    }\r\n"
    "\r\n"
    "    /** 列表里某个注册名（path 部分）的下标；没有返回 -1 */\r\n"
    "    private static int indexOfPath(List<ItemStack> list, String path) {\r\n"
    "        for (int i = 0; i < list.size(); i++) {\r\n"
    "            if (path.equals(pathOf(list.get(i)))) {\r\n"
    "                return i;\r\n"
    "            }\r\n"
    "        }\r\n"
    "        return -1;\r\n"
    "    }\r\n"
)

RETURN_OLD = "        return out;\r\n    }\r\n\r\n    /** 由物品 id / 路径判定的小工具 */"
RETURN_NEW = ("        return applyPins(out);\r\n    }\r\n" + BLOCK +
              "\r\n    /** 由物品 id / 路径判定的小工具 */")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest().upper()


def main() -> int:
    raw = JAVA.read_bytes()
    print("SHA BEFORE = %s (%d B)" % (sha(raw), len(raw)))
    if b"ADJACENCY_PINS" in raw:
        print("ERROR: already patched")
        return 2
    for name, anchor in (("doc", DOC_ANCHOR.encode("utf-8")), ("return", RETURN_OLD.encode("utf-8"))):
        n = raw.count(anchor)
        print("anchor %-6s occurrences=%d" % (name, n))
        if n != 1:
            print("ERROR: anchor %s not unique" % name)
            return 2
    out = raw.replace(DOC_ANCHOR.encode("utf-8"), (DOC_ANCHOR + DOC_INSERT).encode("utf-8"))
    out = out.replace(RETURN_OLD.encode("utf-8"), RETURN_NEW.encode("utf-8"))
    JAVA.write_bytes(out)
    print("SHA AFTER  = %s (%d B, +%d B)" % (sha(out), len(out), len(out) - len(raw)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
