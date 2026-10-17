# -*- coding: utf-8 -*-
"""轮6 资源落盘：贴图字节复制 + 语言键只追加 + 新增 JSON。

全部 bytes / UTF-8 无 BOM；归档副本只读。
"""
import json
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[1]
RES = REPO / "src" / "main" / "resources"
LANG = RES / "assets" / "bettergold" / "lang"
ARCHIVE = REPO / "docs" / "新约10-素材清单" / "金钱妖"

# ---------- 1) 实体贴图（字节原样复制；归档副本不动） ----------
src_png = ARCHIVE / "money_gremlin.png"
dst_png = RES / "assets" / "bettergold" / "textures" / "entity" / "money_gremlin.png"
dst_png.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(src_png, dst_png)
print("[tex] copied %s -> %s (%d B)" % (src_png.name, dst_png.relative_to(REPO), dst_png.stat().st_size))

# ---------- 2) 生成蛋物品模型 ----------
egg_model = RES / "assets" / "bettergold" / "models" / "item" / "money_gremlin_spawn_egg.json"
egg_model.parent.mkdir(parents=True, exist_ok=True)
egg_model.write_bytes(
    ('{\r\n  "parent": "minecraft:item/template_spawn_egg"\r\n}\r\n').encode("utf-8"))
print("[model] wrote %s" % egg_model.relative_to(REPO))

# ---------- 3) 两个伤害类型（scaling=never ⇒ 显式查表不会被原版难度再乘） ----------
for damage_id, message_id, exhaustion in (
        ("money_gremlin_melee", "bettergold.money_gremlin_melee", "0.1"),
        ("chaos_coin", "bettergold.chaos_coin", "0.1")):
    p = RES / "data" / "bettergold" / "damage_type" / (damage_id + ".json")
    p.parent.mkdir(parents=True, exist_ok=True)
    text = (
        "{\r\n"
        '  "message_id": "%s",\r\n'
        '  "exhaustion": %s,\r\n'
        '  "scaling": "never"\r\n'
        "}\r\n" % (message_id, exhaustion))
    p.write_bytes(text.encode("utf-8"))
    print("[damage_type] wrote %s" % p.relative_to(REPO))

# ---------- 4) 自然生成（黑暗处、主世界；权重/数量是工作值） ----------
biome = RES / "data" / "bettergold" / "neoforge" / "biome_modifier" / "add_money_gremlin.json"
biome.parent.mkdir(parents=True, exist_ok=True)
biome.write_bytes((
    "{\r\n"
    '  "type": "neoforge:add_spawns",\r\n'
    '  "biomes": "#minecraft:is_overworld",\r\n'
    '  "spawners": {\r\n'
    '    "type": "bettergold:money_gremlin",\r\n'
    '    "weight": 5,\r\n'
    '    "minCount": 1,\r\n'
    '    "maxCount": 2\r\n'
    "  }\r\n"
    "}\r\n").encode("utf-8"))
print("[biome_modifier] wrote %s" % biome.relative_to(REPO))

# ---------- 5) 语言键：只追加（不动既有行） ----------
NEW_KEYS = {
    "zh_cn.json": {
        "entity.bettergold.money_gremlin": "金钱妖",
        "item.bettergold.money_gremlin_spawn_egg": "金钱妖刷怪蛋",
        "death.attack.bettergold.money_gremlin_melee": "%1$s 被 %2$s 的金币击倒",
        "death.attack.bettergold.chaos_coin": "%1$s 被 %2$s 的混沌金币击中",
    },
    "en_us.json": {
        "entity.bettergold.money_gremlin": "Money Gremlin",
        "item.bettergold.money_gremlin_spawn_egg": "Money Gremlin Spawn Egg",
        "death.attack.bettergold.money_gremlin_melee": "%1$s was struck down by %2$s",
        "death.attack.bettergold.chaos_coin": "%1$s was hit by a Chaos Coin from %2$s",
    },
}

for filename, entries in NEW_KEYS.items():
    path = LANG / filename
    raw = path.read_bytes().decode("utf-8")
    data = json.loads(raw)
    for key in entries:
        if key in data:
            raise SystemExit("[lang] key already exists: %s in %s" % (key, filename))
    # 找最后一个对象结束的 '}'（文件里只有一层顶层对象）
    end = raw.rstrip().rfind("}")
    if end < 0:
        raise SystemExit("[lang] no closing brace: %s" % filename)
    head = raw[:end].rstrip()
    tail = raw[end:]
    lines = []
    for key, value in entries.items():
        lines.append('  %s: %s' % (json.dumps(key, ensure_ascii=False),
                                   json.dumps(value, ensure_ascii=False)))
    addition = ",\r\n" + ",\r\n".join(lines) + "\r\n"
    out = head + addition + tail
    path.write_bytes(out.encode("utf-8"))
    check = json.loads(path.read_text(encoding="utf-8"))
    assert len(check) == len(data) + len(entries), (len(check), len(data))
    print("[lang] %s: %d -> %d keys" % (filename, len(data), len(check)))
    for key in entries:
        print("        %s = %s" % (key, check[key]))
