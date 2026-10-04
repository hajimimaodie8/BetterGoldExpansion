#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bg-book perturbation matrix (throwaway harness, lives in build/ which is gitignored).

Contract (mcmod_experience 3.4): every NEW or MODIFIED assertion of this round must be
proven able to go red.  For each case we mutate ONE source file byte-for-byte on disk,
run tools/asset-generator/validate_metal_data.py, and require:
  * the expected stable ASCII assertion id to appear in the output, and
  * exit code != 0  (except the reverse control, which must stay exit 0).
Afterwards the file is restored byte-for-byte and its SHA256 is re-checked -- a silently
altered file would invalidate the whole round (that already happened once in bg-16:
read_text/write_text turned CRLF into LF).

Run:  python build\bgbook-perturb.py
"""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VALIDATOR = REPO / "tools" / "asset-generator" / "validate_metal_data.py"
OUT = REPO / "build" / "bgbook-perturb-result.txt"
RAW_LOG = REPO / "build" / "bgbook-perturb-raw.txt"

TOML = "src/main/resources/META-INF/neoforge.mods.toml"
GRADLE = "build.gradle"
PROPS = "gradle.properties"
ALLITEMS = "src/main/java/com/hjmmd_8/bettergold/registry/AllItems.java"
CTS = "src/main/java/com/hjmmd_8/bettergold/material/CreativeTabSections.java"
MODULE = "src/main/java/com/hjmmd_8/bettergold/patchouli/HandbookModule.java"
COMPAT = "src/main/java/com/hjmmd_8/bettergold/patchouli/PatchouliCompat.java"
BOOK = "src/main/resources/data/bettergold/patchouli_books/alchemy_handbook/book.json"
CAT = "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/categories/alchemy_start.json"
TOOLS = "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/entries/tools_per_family.json"
MERCHANT = "src/main/resources/assets/bettergold/patchouli_books/alchemy_handbook/zh_cn/entries/merchant.json"
STRAY = "src/main/resources/data/bettergold/patchouli_books/alchemy_handbook/zh_cn/entries/merchant.json"
ICON = "src/main/resources/assets/bettergold/textures/item/alchemy_student_handbook.png"
MODEL = "src/main/resources/assets/bettergold/models/item/alchemy_student_handbook.json"
EN = "src/main/resources/assets/bettergold/lang/en_us.json"
DOC = "docs/1.6-规格.md"

# (case, [edit, ...], expected assertion id or None for "must stay green")
#   edit = (path, old_bytes, new_bytes[, "all" | "create"])
#     old_bytes None -> delete the file
#     flag "create"  -> write new_bytes to the path (old_bytes must be None)
CASES = [
    ("C1 toml dep type optional->required", [
        (TOML, b'modId="patchouli"\n    type="optional"', b'modId="patchouli"\n    type="required"')],
     "bgbook-dep-optional"),
    ("C2 toml versionRange gets an upper bound", [
        (TOML, b'versionRange="[1.21.1-93,)"', b'versionRange="[1.21.1-93,1.21.1-93]"')],
     "bgbook-dep-versionrange"),
    ("C3 toml ordering AFTER removed", [
        (TOML, b'modId="patchouli"\n    type="optional"\n    versionRange="[1.21.1-93,)"\n    ordering="AFTER"',
         b'modId="patchouli"\n    type="optional"\n    versionRange="[1.21.1-93,)"\n    ordering="NONE"')],
     "bgbook-dep-ordering"),
    ("C4 gradle adds localRuntime for patchouli", [
        (GRADLE, b'    compileOnly "maven.modrinth:patchouli:${patchouli_version}"',
         b'    compileOnly "maven.modrinth:patchouli:${patchouli_version}"\n'
         b'    localRuntime "maven.modrinth:patchouli:${patchouli_version}"')],
     "bgbook-gradle-no-localruntime"),
    ("C5 gradle compileOnly line removed", [
        (GRADLE, b'    compileOnly "maven.modrinth:patchouli:${patchouli_version}"', b'')],
     "bgbook-gradle-compile-only"),
    ("C6 gradle.properties version key renamed", [
        (PROPS, b"patchouli_version=1.21.1-93-neoforge", b"patchouli_ver=1.21.1-93-neoforge")],
     "bgbook-gradle-version"),
    ("C7 PatchouliCompat: guard replaced (API touched first)", [
        (COMPAT, b"if (!HandbookModule.isLoaded()) {", b"if (player == null) {")],
     "bgbook-isolation-guard"),
    ("C8 HandbookModule: wrong modid in isLoaded", [
        (MODULE, b'isLoaded("patchouli")', b'isLoaded("patchouli_x")')],
     "bgbook-item-guarded"),
    ("C9 AllItems: direct registration (guard bypassed)", [
        (ALLITEMS, b"HandbookModule.register(ITEMS)",
         b'ITEMS.register("alchemy_student_handbook", () -> null)')],
     "bgbook-item-guarded"),
    ("C10 CreativeTabSections: handbook slot predicate renamed", [
        (CTS, b"CreativeTabSections::isHandbook", b"CreativeTabSections::isNotHandbook")],
     "bgbook-creative-first"),
    ("C11 book.json custom_book_item typo", [
        (BOOK, b'"custom_book_item": "bettergold:alchemy_student_handbook"',
         b'"custom_book_item": "bettergold:typo_handbook"')],
     "bgbook-book-custom-item"),
    ("C12 book.json use_resource_pack -> false", [
        (BOOK, b'"use_resource_pack": true', b'"use_resource_pack": false')],
     "bgbook-book-resource-pack"),
    ("C13 book.json i18n -> false", [
        (BOOK, b'"i18n": true', b'"i18n": false')],
     "bgbook-book-i18n"),
    ("C14 contents copied back into data/ (the real 1.20 bug)", [
        (STRAY, None, b'{"name": "stray", "category": "bettergold:alchemy_start", "pages": []}', "create")],
     "bgbook-book-split"),
    ("C15 category icon swapped", [
        (CAT, b'"icon": "bettergold:raw_sturdygold"', b'"icon": "bettergold:sturdygold_ingot"')],
     "bgbook-categories"),
    ("C16 page gains a recipe3 key (Patchouli cap)", [
        (TOOLS, b'"recipe2": "bettergold:smithing_flamegold_axe"',
         b'"recipe2": "bettergold:smithing_flamegold_axe",\n      '
         b'"recipe3": "bettergold:smithing_flamegold_hoe"')],
     "bgbook-page-recipe-cap"),
    ("C17 a ninth metal is added to the validator scan table", [
        (str(VALIDATOR.relative_to(REPO)).replace("\\", "/"),
         b'"thornsgold", "echogold"]', b'"thornsgold", "echogold", "fakegold"]')],
     "bgbook-pages-per-family"),
    ("C18 page references a non-existent recipe", [
        (TOOLS, b'"recipe": "bettergold:smithing_flamegold_sword"',
         b'"recipe": "bettergold:smithing_flamegold_sword2"')],
     "bgbook-recipe-refs"),
    ("C19 en_us loses a handbook entry key", [
        (EN, b'  "bettergold.handbook.entry.merchant": "The Gold Exchange Merchant",\n', b"")],
     "bgbook-lang-keys"),
    ("C20 icon PNG byte flipped", [(ICON, None, None)], "bgbook-icon"),
    ("C21 model parent changed to handheld", [
        (MODEL, b'"parent": "minecraft:item/generated"', b'"parent": "minecraft:item/handheld"')],
     "bgbook-model"),
    ("C22 assets zh_cn entry deleted (bilingual parity)", [(MERCHANT, None, None)],
     "bgbook-book-bilingual"),
    ("C23 doc loses the page-cap wording", [
        (DOC, "Patchouli 的结构上限".encode("utf-8"), "Patchouli capability cap".encode("utf-8"), "all")],
     "bgbook-doc-page-cap"),
    ("C24 REVERSE CONTROL: comments only (must stay green)", [
        (GRADLE, b"dependencies {",
         b'// PERTURB comment: localRuntime "maven.modrinth:patchouli:x" must not matter\n'
         b"dependencies {"),
        (TOML, b'modId="patchouli"',
         b'# PERTURB comment: type="required" versionRange="[1.21.1-93,9]" must not matter\n    modId="patchouli"'),
        (COMPAT, b"public final class PatchouliCompat {",
         b"// PERTURB comment: PatchouliAPI PatchouliSounds isLoaded() recipe3 must not matter\n"
         b"public final class PatchouliCompat {")],
     None),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(name, edits, expected):
    backups = {}
    deleted = {}
    created = []
    try:
        for edit in edits:
            rel, old, new = edit[0], edit[1], edit[2]
            flag = edit[3] if len(edit) > 3 else None
            p = REPO / rel
            if flag == "create":
                created.append(rel)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(new)
                continue
            if rel not in backups:
                backups[rel] = p.read_bytes()
            if old is None:  # delete
                deleted[rel] = p.read_bytes()
                p.unlink()
                continue
            raw = p.read_bytes()
            if old not in raw:
                return name, "SETUP-FAIL", "pattern not found in %s (perturbation did not apply)" % rel, -1
            if flag != "all" and raw.count(old) != 1:
                return name, "SETUP-FAIL", "pattern occurs %d times in %s" % (raw.count(old), rel), -1
            p.write_bytes(raw.replace(old, new))
        rc = subprocess.run([sys.executable, str(VALIDATOR)], cwd=str(REPO),
                            stdout=open(RAW_LOG, "wb"), stderr=subprocess.STDOUT).returncode
        text = RAW_LOG.read_bytes().decode("utf-8", "replace")
        if expected is None:
            ok = rc == 0
            detail = "exit=%d (must be 0)" % rc
        else:
            hit = expected in text
            ok = hit and rc != 0
            detail = "exit=%d expected-id-hit=%s" % (rc, hit)
        return name, "OK" if ok else "MISMATCH", detail, rc
    finally:
        for rel, raw in backups.items():
            p = REPO / rel
            p.write_bytes(raw)
            if sha(p) != hashlib.sha256(raw).hexdigest():
                return name, "RESTORE-FAIL", "sha256 mismatch after restore: %s" % rel, -1
        for rel, raw in deleted.items():
            p = REPO / rel
            p.write_bytes(raw)
            if sha(p) != hashlib.sha256(raw).hexdigest():
                return name, "RESTORE-FAIL", "sha256 mismatch after restore: %s" % rel, -1
        for rel in created:
            p = REPO / rel
            if p.exists():
                p.unlink()
            # clean up the (possibly newly created) directory chain down to the book root
            d = p.parent
            stop = (REPO / "src/main/resources/data/bettergold/patchouli_books/alchemy_handbook").resolve()
            while d.resolve() != stop and str(d.resolve()).startswith(str(stop)) and d.is_dir():
                if any(d.iterdir()):
                    break
                d.rmdir()
                d = d.parent


lines = []
mismatches = 0

rc = subprocess.run([sys.executable, str(VALIDATOR)], cwd=str(REPO),
                    stdout=open(RAW_LOG, "wb"), stderr=subprocess.STDOUT).returncode
lines.append("BASELINE-1 exit=%d (expect 0) -> %s" % (rc, "OK" if rc == 0 else "MISMATCH"))
if rc != 0:
    mismatches += 1

for name, edits, expected in CASES:
    n, status, detail, _rc = run_case(name, edits, expected)
    if status != "OK":
        mismatches += 1
    lines.append("%-58s %-11s %s" % (n, status, detail))

rc = subprocess.run([sys.executable, str(VALIDATOR)], cwd=str(REPO),
                    stdout=open(RAW_LOG, "wb"), stderr=subprocess.STDOUT).returncode
lines.append("BASELINE-2 exit=%d (expect 0) -> %s" % (rc, "OK" if rc == 0 else "MISMATCH"))
if rc != 0:
    mismatches += 1

lines.append("")
lines.append("cases=%d mismatches=%d" % (len(CASES) + 2, mismatches))
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines))
sys.exit(1 if mismatches else 0)
