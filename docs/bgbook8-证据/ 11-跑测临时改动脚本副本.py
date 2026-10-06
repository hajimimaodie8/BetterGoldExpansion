# -*- coding: utf-8 -*-
"""逐字节替换工具（A 级跑测前的临时改动；收尾按 SHA256 复原）。

用法：python build\bg8_patch.py <相对路径> <old-hex?> —— 这里只做本轮的三个具体动作，
由 argv[1] 选动作：
  level-on    : run/server.properties  level-name=world        -> level-name=bgbook8probe
  level-off   : 反向
  probe-on    : bettergold.java 加临时注册行
  probe-off   : 反向
"""
import io
import os
import sys

sys.stdout.reconfigure(errors="replace")
REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
action = sys.argv[1]


def patch(rel, old, new, count=1):
    p = os.path.join(REPO, rel.replace("/", os.sep))
    raw = io.open(p, "rb").read()
    if raw.count(old) != count:
        raise SystemExit("SETUP-FAIL: %s 里模式出现 %d 次（期望 %d）" % (rel, raw.count(old), count))
    io.open(p, "wb").write(raw.replace(old, new))
    print("patched %s (%d -> %d bytes)" % (rel, len(raw), len(raw) - count * len(old) + count * len(new)))


if action == "level-on":
    patch("run/server.properties", b"level-name=world", b"level-name=bgbook8probe")
elif action == "level-off":
    patch("run/server.properties", b"level-name=bgbook8probe", b"level-name=world")
elif action == "probe-on":
    patch("src/main/java/com/hjmmd_8/bettergold/bettergold.java",
          b"        NeoForge.EVENT_BUS.register(com.hjmmd_8.bettergold.event.VillageTrades.class);",
          b"        NeoForge.EVENT_BUS.register(com.hjmmd_8.bettergold.event.VillageTrades.class);\n"
          b"        // BG-BOOK-8 PROBE (temporary, removed at teardown)\n"
          b"        com.hjmmd_8.bettergold.probe.bgbook8.BgBook8Probe.armIfEnabled();")
elif action == "probe-off":
    patch("src/main/java/com/hjmmd_8/bettergold/bettergold.java",
          b"        NeoForge.EVENT_BUS.register(com.hjmmd_8.bettergold.event.VillageTrades.class);\n"
          b"        // BG-BOOK-8 PROBE (temporary, removed at teardown)\n"
          b"        com.hjmmd_8.bettergold.probe.bgbook8.BgBook8Probe.armIfEnabled();",
          b"        NeoForge.EVENT_BUS.register(com.hjmmd_8.bettergold.event.VillageTrades.class);")
elif action == "client-on":
    patch("src/main/java/com/hjmmd_8/bettergold/bettergold.java",
          b"        com.hjmmd_8.bettergold.probe.bgbook8.BgBook8Probe.armIfEnabled();",
          b"        com.hjmmd_8.bettergold.probe.bgbook8.BgBook8Probe.armIfEnabled();\n"
          b"        if (net.neoforged.fml.loading.FMLEnvironment.dist"
          b" == net.neoforged.api.distmarker.Dist.CLIENT) {\n"
          b"            com.hjmmd_8.bettergold.probe.bgbook8.BgBook8ClientProbe.armIfEnabled();\n"
          b"        }")
elif action == "client-off":
    patch("src/main/java/com/hjmmd_8/bettergold/bettergold.java",
          b"        com.hjmmd_8.bettergold.probe.bgbook8.BgBook8Probe.armIfEnabled();\n"
          b"        if (net.neoforged.fml.loading.FMLEnvironment.dist"
          b" == net.neoforged.api.distmarker.Dist.CLIENT) {\n"
          b"            com.hjmmd_8.bettergold.probe.bgbook8.BgBook8ClientProbe.armIfEnabled();\n"
          b"        }",
          b"        com.hjmmd_8.bettergold.probe.bgbook8.BgBook8Probe.armIfEnabled();")
elif action == "args-on":
    patch("build/moddev/clientRunProgramArgs.txt",
          b"# User Supplied Program Arguments",
          b"# User Supplied Program Arguments\n"
          b"--quickPlayPath logs/quickplay/bgbook8cp.json\n"
          b"--quickPlaySingleplayer bgbook8cprobe")
elif action == "args-off":
    patch("build/moddev/clientRunProgramArgs.txt",
          b"# User Supplied Program Arguments\n"
          b"--quickPlayPath logs/quickplay/bgbook8cp.json\n"
          b"--quickPlaySingleplayer bgbook8cprobe",
          b"# User Supplied Program Arguments")
else:
    raise SystemExit("unknown action: %s" % action)
