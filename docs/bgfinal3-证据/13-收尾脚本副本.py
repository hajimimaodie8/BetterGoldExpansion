# -*- coding: utf-8 -*-
"""bgfinal3 收尾：逐字节复原临时改动 + 删除本会话自己造的东西 + 打印 SHA256 自证。

只删/只复原**本会话自己造的**：`src/main/java/.../probe/bgfinal3/`、`probe/bgfinal3/`、
两个开关文件、两个探针世界（`run/bgfinal3probe`、`run/saves/bgfinal3cprobe`）。
**绝不递归删整个 `probe/`**、**绝不碰作者存档** `run/saves/新的世界`。
"""
import hashlib
import os
import shutil
import sys

sys.stdout.reconfigure(errors="replace")
REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"

TARGETS = {
    "run/server.properties": "a2229937ba8ab7428bc959e87a784890500d6d7061b10fa8302758e46a01d3c4",
    "build/moddev/clientRunProgramArgs.txt":
        "a365a5edf7abc44c576e5dd3f725a54d46658fcddc1e3a0257bec7c0ab2e4bdb",
    "src/main/java/com/hjmmd_8/bettergold/event/ModEvents.java":
        "904ca900ea6d042fb8e788ccc7298f95b0fa798774380d55dd6ea3d8fe933dd7",
    "src/main/resources/assets/bettergold/lang/zh_cn.json":
        "40d884dca2426283dcdd2e76b099fd43fee9c06896930902b85b777032effef9",
    "src/main/resources/assets/bettergold/lang/en_us.json":
        "82eb344578b9f29ad90760081388ca17b1b32b8000a85ec883051d28f04d80d5",
    "tools/asset-generator/bgappend-requirements-snapshot/bg-book-8.md":
        "7b3ac419be90d927d1dbc0980bbda5a56ed5a81b660d11e698f7394ea7117501",
    "src/main/resources/assets/bettergold/textures/trims/color_palettes/indigoseagold.png":
        "9c966b7f80c2e2550064a822730a704e8a68aeac9047fa9f1aabfda7eb9e6b6d",
    "src/main/resources/data/bettergold/advancement/agriculture/plant_gold_crop.json":
        "5ac2e90eea3fb520773f0e5d364c687664438a08fbb2f2245b7af28ef7305f6d",
    "tools/asset-generator/generate_advancements.py":
        "7aa4ebcb93289dd620f271fd825ca7edf4f10fbe2ad762502c75589b801a1558",
    "tools/asset-generator/validate_trim_assets.py":
        "2445b43b2b39f6f896cb176a4bb3961ba317aaf0a427902cb8d53e791890dce7",
}


def path(rel):
    return os.path.join(REPO, rel.replace("/", os.sep))


def sha(rel):
    with open(path(rel), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def rm(rel, is_dir=False):
    t = path(rel)
    if not os.path.exists(t):
        return "absent"
    if is_dir or os.path.isdir(t):
        shutil.rmtree(t)
        return "removed-dir"
    os.remove(t)
    return "removed-file"


# ---- 1. 先复原两个"会被服务器/客户端改写"的文件 ----
sp = path("run/server.properties")
if os.path.isfile(sp):
    raw = open(sp, "rb").read()
    raw2 = raw.replace(b"level-name=bgfinal3probe", b"level-name=world")
    if raw2 != raw:
        open(sp, "wb").write(raw2)
        print("[restore] run/server.properties: level-name 改回 world")

args = path("build/moddev/clientRunProgramArgs.txt")
if os.path.isfile(args):
    raw = open(args, "rb").read()
    lines = [ln for ln in raw.split(b"\n") if not ln.strip().startswith(b"--quickPlaySingleplayer")]
    raw2 = b"\n".join(lines)
    if raw2 != raw:
        open(args, "wb").write(raw2)
        print("[restore] clientRunProgramArgs.txt: 去掉 --quickPlaySingleplayer")

# ---- 2. 删掉本会话自己造的东西 ----
for rel, is_dir in (("src/main/java/com/hjmmd_8/bettergold/probe/bgfinal3", True),
                    ("probe/bgfinal3", True),
                    ("run/bgfinal3-probe.enabled", False),
                    ("run/bgfinal3-client-probe.enabled", False),
                    ("run/bgfinal3probe", True),
                    ("run/saves/bgfinal3cprobe", True)):
    print("[clean] %-62s %s" % (rel, rm(rel, is_dir)))

# ---- 3. 自证 ----
print("\n== SHA256 自证（目标值 == 实际值）==")
bad = 0
for rel, want in sorted(TARGETS.items()):
    if not os.path.isfile(path(rel)):
        print("  MISSING  %s" % rel)
        bad += 1
        continue
    got = sha(rel)
    ok = got == want
    bad += 0 if ok else 1
    print("  %-8s %s" % ("SAME" if ok else "DIFF!!", rel))
    if not ok:
        print("           got  %s\n           want %s" % (got, want))
print("  不一致文件数 = %d" % bad)

print("\n== 残留检查 ==")
for rel in ("run/bgfinal3-probe.enabled", "run/bgfinal3-client-probe.enabled",
            "run/bgfinal3probe", "run/saves/bgfinal3cprobe",
            "src/main/java/com/hjmmd_8/bettergold/probe/bgfinal3", "probe/bgfinal3"):
    print("  %-62s exists=%s" % (rel, os.path.exists(path(rel))))
print("  作者存档 run/saves/新的世界 exists=%s" % os.path.exists(path("run/saves/新的世界")))
