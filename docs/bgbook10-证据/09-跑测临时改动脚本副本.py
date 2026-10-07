# -*- coding: utf-8 -*-
"""bg-book §十：A 级跑测的**临时改动**夹具（逐字节替换；收尾按 SHA256 复原）。

动作（锚点一律用**纯 ASCII**，避免把中文写进字节字面量）：
  probe-on / probe-off   : bettergold.java 注册两个探针（带 §十 PROBE 标记）
  level-on / level-off   : run/server.properties 的 level-name（造探针世界用）
  args-on  / args-off    : build.gradle 的 runs.client.programArguments
                           （**不碰** Gradle 生成的 build/moddev/clientRunProgramArgs.txt ——
                            那是有竞态的生成产物，见 docs/1.6-规格.md §20.1.5）

Run: python build\\bgbook10-fixture.py <action>
"""
import hashlib
import io
import os
import sys

sys.stdout.reconfigure(errors="replace")
REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"

PROBE_ANCHOR = b"        NeoForge.EVENT_BUS.register(com.hjmmd_8.bettergold.event.VillageTrades.class);"
PROBE_BLOCK = PROBE_ANCHOR + (
    b"\n        // BG-BOOK-10 PROBE (temporary, removed at teardown)\n"
    b"        com.hjmmd_8.bettergold.probe.bgbook10.BgBook10Probe.armIfEnabled();\n"
    b"        if (net.neoforged.fml.loading.FMLEnvironment.dist\n"
    b"                == net.neoforged.api.distmarker.Dist.CLIENT) {\n"
    b"            com.hjmmd_8.bettergold.probe.bgbook10.BgBook10ClientProbe.armIfEnabled();\n"
    b"        }"
)

ARGS_ANCHOR = b"        client {\n            client()\n"
ARGS_BLOCK = ARGS_ANCHOR + (
    b"            // BG-BOOK-10 PROBE (temporary, removed at teardown)\n"
    b"            programArguments.addAll '--quickPlaySingleplayer', 'bgbook10probe'\n"
)


def patch(rel, old, new, count=1):
    p = os.path.join(REPO, rel.replace("/", os.sep))
    raw = io.open(p, "rb").read()
    n = raw.count(old)
    if n != count:
        raise SystemExit("SETUP-FAIL: %s 里模式出现 %d 次（期望 %d）" % (rel, n, count))
    out = raw.replace(old, new)
    io.open(p, "wb").write(out)
    print("patched %-22s %d -> %d bytes  sha256=%s"
          % (rel, len(raw), len(out), hashlib.sha256(out).hexdigest()))


def main():
    action = sys.argv[1]
    if action == "probe-on":
        patch("src/main/java/com/hjmmd_8/bettergold/bettergold.java", PROBE_ANCHOR, PROBE_BLOCK)
    elif action == "probe-off":
        patch("src/main/java/com/hjmmd_8/bettergold/bettergold.java", PROBE_BLOCK, PROBE_ANCHOR)
    elif action == "level-on":
        patch("run/server.properties", b"level-name=world", b"level-name=bgbook10probe")
    elif action == "level-off":
        patch("run/server.properties", b"level-name=bgbook10probe", b"level-name=world")
    elif action == "args-on":
        patch("build.gradle", ARGS_ANCHOR, ARGS_BLOCK)
    elif action == "args-off":
        patch("build.gradle", ARGS_BLOCK, ARGS_ANCHOR)
    else:
        raise SystemExit("unknown action: %s" % action)


if __name__ == "__main__":
    main()
