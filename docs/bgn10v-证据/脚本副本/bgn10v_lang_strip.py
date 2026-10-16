"""删除「未注册形态」的死语言键（bg-n10 轮3，临时脚本）。

背景：轮1 后半的 `generate_metal_data.py` 按「全量占位」写了 20 条永远不会被引用的键
（chaosgold 的 raw/模板 + chaosalloy 的 10 种建材 + 两族的粒）——
与立档「没声明的形态不许注册（物品/方块/模型/语言键/tag 全查）」冲突。

本脚本只做「删行」，不走 json.dump（避免整文件格式化 diff）。逐字节前后留 SHA256。
"""
import hashlib
import re
import sys
from pathlib import Path

REPO = Path(r"E:\mc\mcmod\bettergold-template-1.21.1")
LANG = REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "lang"

DEAD = [
    "item.bettergold.raw_chaosgold",
    "item.bettergold.raw_chaosalloy",
    "item.bettergold.chaosgold_upgrade_template",
    "item.bettergold.chaosgold_nugget",
    "item.bettergold.chaosalloy_nugget",
] + [f"block.bettergold.chaosalloy_{b}" for b in (
    "bricks", "bricks_slab", "bricks_stairs", "bricks_wall", "pillar",
    "door", "trapdoor", "bars", "chain", "lantern")] + [
    "item.bettergold.smithing_template.chaosgold_upgrade.applies_to",
    "item.bettergold.smithing_template.chaosgold_upgrade.ingredients",
    "item.bettergold.smithing_template.chaosgold_upgrade.upgrade_description",
    "item.bettergold.smithing_template.chaosgold_upgrade.base_slot_description",
    "item.bettergold.smithing_template.chaosgold_upgrade.additions_slot_description",
]

# 5 条特殊键：轮1 的 ITEM_NAMES 里 raw / nugget 也算「材料链」
DEAD += ["item.bettergold.chaosgold_nugget"] if "item.bettergold.chaosgold_nugget" not in DEAD else []
DEAD = sorted(set(DEAD))


def strip(t: str, key: str) -> tuple[str, int]:
    pat = re.compile(r'^\s*"' + re.escape(key) + r'":.*\n', re.M)
    new, n = pat.subn("", t)
    return new, n


def main() -> None:
    apply = "--apply" in sys.argv
    total = 0
    for name in ("zh_cn.json", "en_us.json"):
        p = LANG / name
        raw_before = p.read_bytes()
        text = raw_before.decode("utf-8")
        hits = []
        for key in DEAD:
            text, n = strip(text, key)
            if n:
                hits.append(key)
        # 修掉可能出现的 "}," 悬空逗号（删到最后一个元素时）
        text = re.sub(r',(\s*\n\})', r'\1', text)
        raw_after = text.encode("utf-8")
        total += len(hits)
        print(f"{name}: 删除 {len(hits)} 条  sha_before={hashlib.sha256(raw_before).hexdigest().upper()[:16]}"
              f"  sha_after={hashlib.sha256(raw_after).hexdigest().upper()[:16]}")
        for k in sorted(set(DEAD) - set(hits)):
            print(f"   [警告] 没找到：{k}")
        if apply:
            p.write_bytes(raw_after)
    print(f"合计命中 {total} 条；apply={apply}")


if __name__ == "__main__":
    main()
