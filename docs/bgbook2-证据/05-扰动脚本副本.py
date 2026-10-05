#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bgbook2-perturb.py -- perturbation matrix for the bg-book §6 append round and the
bg-fix §7 item 8 (pacify) assertions.

Discipline (mcmod_experience §3.4 / §5):
  * every mutation happens on **bytes** of a temporary copy on disk (files are read/written
    with read_bytes/write_bytes, never text mode -> no CRLF<->LF drift);
  * every mutated file is restored afterwards and **verified by SHA256** byte-for-byte;
  * each case must make the validator exit 1 and print the **expected ASCII assertion id**;
  * one reverse control: adding comments that mention every forbidden / counted token must
    stay green (proves the assertions run on comment-stripped text);
  * a baseline before and after the matrix.
"""

import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VALIDATOR = os.path.join(ROOT, "tools", "asset-generator", "validate_metal_data.py")

BOOK_ZH = "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/entries"
BOOK_EN = "src/main/resources/assets/bettergold/papchouli_books"  # placeholder, replaced below
BOOK_EN = "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/en_us/entries"
LANG_ZH = "src/main/resources/assets/bettergold/lang/zh_cn.json"
LANG_EN = "src/main/resources/assets/bettergold/lang/en_us.json"
MEV = "src/main/java/com/hjmmd_8/bettergold/material/MetalEvents.java"
MFAM = "src/main/java/com/hjmmd_8/bettergold/material/MetalFamily.java"
AMET = "src/main/java/com/hjmmd_8/bettergold/material/AllMetals.java"
DOC = "docs/1.6-规格.md"


def path(rel):
    return os.path.join(ROOT, rel.replace("/", os.sep))


def sha(rel):
    return hashlib.sha256(open(path(rel), "rb").read()).hexdigest()


def run_validator():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run([sys.executable, VALIDATOR], cwd=ROOT, capture_output=True, env=env)
    out = (p.stdout + p.stderr).decode("utf-8", errors="replace")
    return p.returncode, out


class Mutator:
    """records the original bytes of every file it touches, and restores them all."""

    def __init__(self):
        self.saved = {}

    def _load(self, rel):
        if rel not in self.saved:
            self.saved[rel] = open(path(rel), "rb").read()
        return self.saved[rel]

    def replace(self, rel, old, new, count=1):
        data = self._load(rel)
        ob, nb = old.encode("utf-8"), new.encode("utf-8")
        assert data.count(ob) >= count, "perturbation text not found (x%d) in %s: %r" % (
            count, rel, old[:60])
        open(path(rel), "wb").write(data.replace(ob, nb, count))

    def replace_all(self, rel, old, new):
        data = self._load(rel)
        ob, nb = old.encode("utf-8"), new.encode("utf-8")
        assert ob in data, "perturbation text not found in %s: %r" % (rel, old[:60])
        open(path(rel), "wb").write(data.replace(ob, nb))

    def move(self, rel, new_rel):
        self._load(rel)
        os.replace(path(rel), path(new_rel))
        self.moved = getattr(self, "moved", [])
        self.moved.append((rel, new_rel))

    def restore(self):
        bad = []
        for rel, data in self.saved.items():
            open(path(rel), "wb").write(data)
            if hashlib.sha256(open(path(rel), "rb").read()).hexdigest() != hashlib.sha256(data).hexdigest():
                bad.append(rel)
        for rel, new_rel in getattr(self, "moved", []):
            os.replace(path(new_rel), path(rel))
            self.moved = []
        return bad


# --------------------------------------------------------------------------------------
# The cases: (id, description, mutator fn, expected assertion id)
# --------------------------------------------------------------------------------------
def c_chapter_pages(m):
    m.replace(BOOK_ZH + "/core_materials.json", '"type": "patchouli:crafting"', '"type": "patchouli:text"')


def c_page_type(m):
    m.replace(BOOK_ZH + "/auxiliary_materials.json", '"type": "patchouli:spotlight"',
               '"type": "patchouli:bogus"')


def c_recipe_cap(m):
    m.replace(BOOK_ZH + "/core_materials.json", '"recipe2": "bettergold:raw_flamegold"',
               '"recipe2": "bettergold:raw_flamegold", "recipe3": "bettergold:raw_thornsgold"')


def c_recipe_refs(m):
    m.replace(BOOK_ZH + "/core_materials.json", '"recipe": "bettergold:blazing_rod"',
               '"recipe": "bettergold:no_such_recipe_xyz"')


def c_item_refs(m):
    m.replace(BOOK_ZH + "/core_materials.json", '"item": "bettergold:alchemy_materials_box"',
               '"item": "bettergold:no_such_item_xyz"')


def c_texts_verbatim(m):
    m.replace(LANG_ZH, "以金块为主基", "以金块为副基")


def c_lang_bilingual(m):
    m.replace(LANG_EN, '"bettergold.handbook.page.aux_2"', '"bettergold.handbook.page.aux_2x"')


def c_chapter_entries(m):
    m.replace(BOOK_ZH + "/golden_knowledge.json", '"icon": "bettergold:sturdygold_ingot"',
               '"icon": "bettergold:sturdygold_nugget"')


def c_entry_count(m):
    m.move(BOOK_ZH + "/metal_tour.json", BOOK_ZH + "/metal_tour_perturbed.json")


def c_pacify_flag(m):
    m.replace(AMET, ".contactPacifyNeutral()", ".contactPacifyNeutralX()")


def c_pacify_step_only(m):
    m.replace(MEV, "                pacifyHostileNeutrals(entity);", "                int unusedPacify = 0;")


def c_pacify_predicate(m):
    m.replace(MEV, "neutral.isAngryAt(player)", "neutral.isAngryAtX(player)")


def c_pacify_no_brain(m):
    m.replace(MEV, "stopBeingAngry();\r\n        return true;",
              "stopBeingAngry();\r\n        entity.getBrain();\r\n        return true;")


def c_doc_angerlevel(m):
    # ⚠ 不能替换成 "AngerLevelX"：needle 是**子串**匹配，"AngerLevel" 仍是它的前缀 ⇒ 假绿
    m.replace_all(DOC, "AngerLevel", "AngerLvl")


def c_doc_page_spread(m):
    m.replace_all(DOC, "1 行 = 1 跨页", "1 行 = 一跨页")


def c_doc_step_touch(m):
    m.replace_all(DOC, "踩踏 / 贴近", "踩踏与贴近")


def c_reverse_comments(m):
    """reverse control: only comments -- every forbidden / counted token mentioned in a comment."""
    m.replace(MEV, "    // ==================== bg-fix §七 第 8 条：幻惑金建材 ⇒ 敌对中立生物瞬间变被动 ====================",
              "    // ==================== bg-fix §七 第 8 条：幻惑金建材 ⇒ 敌对中立生物瞬间变被动 ====================\r\n"
              "    // 反向对照注释：pacifyHostileNeutrals / stopBeingAngry / contactPacifyNeutral / getBrain()\r\n"
              "    // / ATTACK_TARGET / recipe3 / AngerLevel 都只出现在注释里 ⇒ 断言必须仍然全绿")
    m.replace(MFAM, "    /** 本族物品免疫仙人掌", "    /* 反向对照注释 */\r\n    /** 本族物品免疫仙人掌")
    # 两侧**同形**地加一个注释键（zh 与 en 必须仍然逐字相同，否则会误触「双端页列表一致」那条）
    for rel in (BOOK_ZH + "/core_materials.json", BOOK_EN + "/core_materials.json"):
        m.replace(rel, '"type": "patchouli:crafting",',
                  '"//": "recipe3 recipes AngerLevel pacifyHostileNeutrals",\r\n      "type": "patchouli:crafting",')


CASES = [
    ("c01 baseline (before)", None, None),
    ("c02 chapter pages", c_chapter_pages, "bgbook2-chapter-pages"),
    ("c03 page type", c_page_type, "bgbook2-page-type"),
    ("c04 recipe cap", c_recipe_cap, "bgbook2-recipe-cap"),
    ("c05 recipe refs", c_recipe_refs, "bgbook2-recipe-refs"),
    ("c06 item refs", c_item_refs, "bgbook2-item-refs"),
    ("c07 texts verbatim", c_texts_verbatim, "bgbook2-texts-verbatim"),
    ("c08 lang bilingual", c_lang_bilingual, "bgbook2-lang-bilingual"),
    ("c09 chapter entries", c_chapter_entries, "bgbook2-chapter-entries"),
    ("c10 entry count", c_entry_count, "bgbook-entry-count"),
    ("c11 pacify flag", c_pacify_flag, "bgfix-pacify-flag"),
    ("c12 pacify step-only", c_pacify_step_only, "bgfix-pacify-step-only"),
    ("c13 pacify predicate", c_pacify_predicate, "bgfix-pacify-predicate"),
    ("c14 pacify no-brain", c_pacify_no_brain, "bgfix-pacify-no-brain"),
    ("c15 doc AngerLevel", c_doc_angerlevel, "bgbook2-doc"),
    ("c16 doc page spread", c_doc_page_spread, "bgbook2-doc"),
    ("c17 doc step/touch", c_doc_step_touch, "bgfix-pacify-doc"),
    ("c18 REVERSE only-comments (must stay green)", c_reverse_comments, None),
    ("c19 baseline (after)", None, None),
]

WATCHED = [BOOK_ZH + "/core_materials.json", BOOK_ZH + "/auxiliary_materials.json",
           BOOK_ZH + "/golden_knowledge.json", BOOK_ZH + "/metal_tour.json",
           LANG_ZH, LANG_EN, MEV, MFAM, AMET, DOC]


def main():
    before = {rel: sha(rel) for rel in WATCHED}
    mismatches = []
    for case_id, fn, expected in CASES:
        m = Mutator()
        try:
            if fn is not None:
                fn(m)
            rc, out = run_validator()
        finally:
            bad = m.restore()
        if bad:
            mismatches.append("%s: RESTORE FAILED for %s" % (case_id, bad))
            continue
        if expected is None:
            ok = (rc == 0)
            detail = "exit=%d (期望 0)" % rc
        else:
            ok = (rc == 1 and ("[%s]" % expected) in out)
            detail = "exit=%d 期望命中 [%s]" % (rc, expected)
        if not ok:
            mismatches.append("%s: %s" % (case_id, detail))
            print("MISMATCH %-46s %s" % (case_id, detail))
            for line in out.splitlines():
                if "问题:" in line:
                    print("          " + line[:220])
        else:
            print("OK       %-46s %s" % (case_id, detail))
    after = {rel: sha(rel) for rel in WATCHED}
    for rel in WATCHED:
        if before[rel] != after[rel]:
            mismatches.append("SHA256 drift: %s" % rel)
    print("\nwatched files SHA256 identical before/after: %s"
          % all(before[r] == after[r] for r in WATCHED))
    for rel in WATCHED:
        print("  %-92s %s" % (rel, after[rel][:16]))
    print("mismatches = %d" % len(mismatches))
    for x in mismatches:
        print("  " + x)
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
