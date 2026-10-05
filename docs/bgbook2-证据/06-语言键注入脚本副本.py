#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgbook2_add_lang.py -- ONE-SHOT, anchored, byte-level appender for the bg-book §6
append-round language keys.

Why a script and not hand editing:
  * the 22 verbatim Chinese texts live in the requirement document (read-only).  Parsing
    them out of its §6.1 / §6.2 / §6.3 tables removes every transcription error, and the
    validator re-parses the SAME document as the expected value, so `[bgbook2-texts-verbatim]`
    is not "the script's own expectation table compared against itself".
  * the two lang files are SHARED with another in-flight session (bg-ach's 101 advancement
    keys), so the edit must be: re-read now -> find ONE unique anchor -> append only ->
    prove nothing else changed.

Guarantees (all asserted, abort on violation):
  1. anchor: the file's single top-level closing brace (`\\n}` at end of file); the script
     never rewrites the rest of the file, only inserts before that brace and adds the one
     comma the previous last key needs.
  2. no key it writes already exists (idempotent / re-run = abort, never duplicate).
  3. every pre-existing key keeps its exact value (before-dict must be a subset of after-dict).
  4. bytes: UTF-8, no BOM, line ending of the file detected and preserved.
  5. both lang files must parse as JSON before and after.
"""

import hashlib
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(os.path.dirname(ROOT), "mod_experience", "开工需求",
                   "20261004-1733_bg-book_patchouli-handbook.md")
LANG_DIR = os.path.join(ROOT, "src", "main", "resources", "assets", "bettergold", "lang")

PAGE = "bettergold.handbook.page."
ENTRY = "bettergold.handbook.entry."

# suffix -> en_us value (faithful English translation; the Chinese side is the author's verbatim text)
EN = {
    "auxiliary_materials": "Auxiliary Materials of Noble Gold",
    "core_materials": "Core Materials of Noble Gold",
    "golden_knowledge": "Knowledge of Noble Gold",
    "aux_1": "Take gold blocks as the main base, then pair them with the nobility of diamonds, the high energy of redstone, the sharpness of quartz, the mystery of amethyst and the stability of netherite; add one certain core material as the medium and \"noble gold\" can be smelted right here. Our little crafting table can never hold that many materials though, so... let us combine these three crystals first.",
    "aux_2": "Since we are \"smelting\" gold after all, the temperature has to be handled well. This bottle of fuel made from blaze powder and magma cream is the aid that heats the raw materials.",
    "core_1": "To smelt \"noble gold\" you still need one core material as the medium. Different core materials give the \"noble gold\" different colours and different abilities.",
    "core_1_right": "Core materials can be obtained by killing certain mobs, mining certain things, or even crafting them yourself, but the more common way is trading with the gold exchange merchant for an alchemy materials box. He will not sell such a gift box to beginners though, so it seems we will have to get on his good side.",
    "core_2": "Using fire as its carrier, the blazing rod is indeed fairly easy to get: just gather some blaze rods in a nether fortress and mix in a little gunpowder. The \"noble gold\" smelted with it is called \"Flamegold\".",
    "core_3": "Using gold as its carrier, the golden cowrie is deeply loved by the piglins - piglin brutes especially love showing them off inside bastion remnants. So we can slaughter the whole piglin kind to get them, and if you cannot win you can also barter with the piglins, a much more peaceful way. The \"noble gold\" smelted with it is called \"Sturdygold\".",
    "core_4": "Using wood as its carrier, the glittering vine may take quite some luck: just mine leaves and vines with any golden tool for a small chance to drop one. That means it is an item you can only own after you already have \"noble gold\" tools. The \"noble gold\" smelted with it is called \"Thornsgold\".",
    "core_5": "Using the sculk element as its carrier, the bundled echo shard is rather hard to obtain: just collect some echo shards in an ancient city and bind them with sculk veins to craft it. The \"noble gold\" smelted with it is called \"Echogold\".",
    "core_6": "Using water as its carrier, the indigo ocean heart has a short process but still needs a lot of luck: just wrap a heart of the sea with lapis blocks to craft it. The \"noble gold\" smelted with it is called \"Indigoseagold\".",
    "core_7": "Using poison as its carrier, the voodoo feather obviously comes from witches. After killing a witch and taking the feather you will find that it is... a second-hand mass product?! And after you get your first one you can duplicate it with crying obsidian, a fermented spider eye and a feather. The \"noble gold\" smelted with it is called \"Voodoogold\".",
    "core_8": "Using lightning as its carrier, the amethyst energy dust is also fairly easy: just take a whole amethyst cluster with Silk Touch, add redstone dust, and grind the two together on a grindstone. The \"noble gold\" smelted with it is called \"Thundergold\".",
    "core_9": "Using illusion as its carrier, the chorus cherry branch rose after the ender dragon perished: just add some cherry saplings with a chorus flower and a ghast tear to craft it. The \"noble gold\" smelted with it is called \"Illusiongold\".",
    "knowledge_1_left": "Once you have gathered the auxiliary materials of \"noble gold\" and chosen your favourite core material, you can turn them into raw material and throw it into a furnace or a blast furnace. The \"noble gold\" you finally refine can serve as very hard building blocks with unique abilities: ingot blocks, bricks, pillars, stairs, slabs, brick walls, bars, doors, trapdoors, chains and lanterns.",
    "knowledge_1_right": "Of course \"noble gold\" can also be used to make powerful weapons and armour, but first you have to craft the ingot of some \"noble gold\" and the smithing template made from its matching core material, then combine them with golden gear and the matching \"noble gold\" ingot.",
    "knowledge_2_left": "Building blocks made of Flamegold give the target 6 seconds of fire damage when stepped on, stood next to, broken or right-clicked.",
    "knowledge_2_right": "Building blocks made of Sturdygold are one of the few with no special effect. If you are not after some kind of defence but only after looks, Sturdygold building blocks are definitely your first choice.",
    "knowledge_3_left": "Building blocks made of Thornsgold deal 1 point of cactus damage to the target when stepped on, stood next to, broken or right-clicked, but unlike a real cactus they will not destroy dropped items.",
    "knowledge_3_right": "Building blocks made of Echogold deal 3 points of warden sonic boom damage to targets in a 3x3x3 area and knock the target back when stepped on, stood next to, broken or right-clicked.",
    "knowledge_4_left": "Building blocks made of Indigoseagold are also among the few with no special effect on most mobs, but they will damage water-fearing creatures such as endermen, blazes, snow golems and striders when those step on or stand next to this metal's building blocks.",
    "knowledge_4_right": "Building blocks made of Voodoogold give the target Poison I for 6 seconds when stepped on, stood next to, broken or right-clicked.",
    "knowledge_5_left": "Building blocks made of Thundergold give the target Weakness I for 6 seconds when stepped on, stood next to, broken or right-clicked.",
    "knowledge_5_right": "Building blocks made of Illusiongold give the player, friendly mobs and some neutral mobs Regeneration I for 6 seconds when stepped on, stood next to, broken or right-clicked, and neutral mobs that are in a hostile state towards players instantly become passive when they step on or stand next to it.",
}


def strip_md(cell):
    cell = cell.strip()
    cell = re.sub(r"\*\*(.+?)\*\*", r"\1", cell)
    return cell.strip()


def parse_doc():
    """Return (ordered [(key_suffix, zh_text)], [entry_title_zh per chapter])."""
    with io.open(DOC, encoding="utf-8") as fh:
        lines = fh.read().split("\n")

    def section_rows(start_marker):
        out, active = [], False
        for line in lines:
            if line.startswith(start_marker):
                active = True
                continue
            if active and line.startswith("### "):
                break
            if active and line.startswith("|") and not re.match(r"^\|\s*-+", line) \
                    and "|---" not in line and "页" not in line.split("|")[1]:
                out.append(line)
        return out

    def cells(line):
        return [c for c in line.split("|")][1:-1]

    texts = []          # (suffix, zh)

    # ---- 6.1: | 页 | 左侧文案 | 右侧挂什么 | ----
    rows61 = section_rows("### 6.1")
    assert len(rows61) == 2, "6.1 rows = %d" % len(rows61)
    for i, line in enumerate(rows61, start=1):
        texts.append(("aux_%d" % i, strip_md(cells(line)[1])))

    # ---- 6.2: | 页 | 左上角图标 | 左侧文案 | 右侧挂什么 | ----
    rows62 = section_rows("### 6.2")
    assert len(rows62) == 9, "6.2 rows = %d" % len(rows62)
    for i, line in enumerate(rows62, start=1):
        c = cells(line)
        texts.append(("core_%d" % i, strip_md(c[2])))
        if i == 1:
            right = c[3]
            right = right.split("<br>")[-1]                    # drop "**中上角：炼金珍材盒**；"
            right = re.sub(r"^\s*\*\*右侧正文\*\*：", "", right)
            texts.append(("core_1_right", strip_md(right)))

    # ---- 6.3: | 页 | 左（含左上角图标 + 逐字文案） | 右（...） | ----
    rows63 = section_rows("### 6.3")
    assert len(rows63) == 5, "6.3 rows = %d" % len(rows63)
    for i, line in enumerate(rows63, start=1):
        c = cells(line)
        for side, col in (("left", 1), ("right", 2)):
            body = c[col].split("<br>")[-1]
            texts.append(("knowledge_%d_%s" % (i, side), strip_md(body)))

    assert len(texts) == 22, "extracted %d texts, expected 22" % len(texts)
    for suffix, zh in texts:
        assert "**" not in zh and "<br>" not in zh, (suffix, zh)
        assert len(zh) >= 12, (suffix, zh)
    # the verbatim rules the author spelled out
    assert texts[2][1].startswith("要想炼制"), texts[2]
    assert texts[0][1].startswith("以金块为主基"), texts[0]
    return texts


def lang_path(name):
    return os.path.join(LANG_DIR, name)


def read_lang(name):
    raw = open(lang_path(name), "rb").read()
    assert not raw.startswith(b"\xef\xbb\xbf"), "%s has a BOM" % name
    eol = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8")
    data = json.loads(text)
    return raw, text, data, eol


def insert_keys(name, pairs):
    raw, text, data, eol = read_lang(name)
    before_sha = hashlib.sha256(raw).hexdigest()
    before_lines = text.count("\n")

    for key, _val in pairs:
        assert key not in data, "%s: key already present: %s" % (name, key)

    stripped = text.rstrip("\r\n")
    assert stripped.endswith("}"), "%s: does not end with }" % name
    head = stripped[:-1].rstrip()
    tail = text[len(stripped) + 1:]                    # whatever followed the final '}'
    body = ("," + eol).join(json.dumps(k, ensure_ascii=False) + ": "
                            + json.dumps(v, ensure_ascii=False) for k, v in pairs)
    body = eol.join("  " + ln for ln in body.split(eol))
    new_text = head + "," + eol + body + eol + "}" + tail

    after = json.loads(new_text)
    for key, val in data.items():
        assert after[key] == val, "%s: clobbered key %s" % (name, key)
    assert len(after) == len(data) + len(pairs), "%s: key count %d -> %d" % (
        name, len(data), len(after))

    open(lang_path(name), "wb").write(new_text.encode("utf-8"))
    after_sha = hashlib.sha256(open(lang_path(name), "rb").read()).hexdigest()
    print("%s: %d keys -> %d keys, %d LF -> %d LF, sha %s -> %s"
          % (name, len(data), len(after), before_lines, new_text.count("\n"),
             before_sha[:16], after_sha[:16]))


def main():
    texts = parse_doc()
    titles = {}
    with io.open(DOC, encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"### 6\.\d 章节 \d ·(.+)$", line.strip())
            if m:
                # drop the "（章节封面：**…**）" tail -- the cover is the entry's icon, not its name
                title = strip_md(m.group(1).split("（")[0])
                titles[len(titles) + 1] = title
    assert len(titles) == 3, titles
    entry_keys = [("auxiliary_materials", titles[1]),
                  ("core_materials", titles[2]),
                  ("golden_knowledge", titles[3])]

    zh_pairs = [(ENTRY + k, v) for k, v in entry_keys]
    zh_pairs += [(PAGE + suffix, zh) for suffix, zh in texts]

    en_pairs = [(ENTRY + k, EN[k]) for k, _ in entry_keys]
    en_pairs += [(PAGE + suffix, EN[suffix]) for suffix, _zh in texts]
    for key, val in en_pairs:
        assert val, key

    print("chapter titles: %s" % [v for _k, v in entry_keys])
    if "--dry" in sys.argv:
        dump = os.path.join(ROOT, "build", "bgbook2-extracted-texts.txt")
        with io.open(dump, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("entries: %s\n" % "\n         ".join(v for _k, v in entry_keys))
            fh.write("--- DRY RUN: parsed %d verbatim texts from the requirement doc ---\n"
                     % len(texts))
            for suffix, zh in texts:
                fh.write("%-22s %s\n" % (suffix, zh))
        print("wrote %s (%d texts)" % (dump, len(texts)))
        return 0
    insert_keys("zh_cn.json", zh_pairs)
    insert_keys("en_us.json", en_pairs)


if __name__ == "__main__":
    sys.exit(main())
