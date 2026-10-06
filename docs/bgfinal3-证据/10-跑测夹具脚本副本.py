# -*- coding: utf-8 -*-
"""bgfinal3 跑测夹具：临时改动（**逐字节可复原**）+ 世界准备 + 进程收尾。

由 argv[1] 选动作：
  level-on / level-off          : run/server.properties  level-name=world <-> level-name=bgfinal3probe
  flag-on  / flag-off           : run/bgfinal3-probe.enabled / run/bgfinal3-client-probe.enabled
  args-on  / args-off           : build/moddev/clientRunProgramArgs.txt 末尾追加 --quickPlaySingleplayer
  world-in / world-out          : run/bgfinal3probe <-> run/saves/bgfinal3cprobe
  notrigger-on / notrigger-off  : ModEvents 里那三行触发器（"改前"对照轮）
  hash <path>                   : 打印 SHA256
"""
import hashlib
import os
import shutil
import sys

sys.stdout.reconfigure(errors="replace")
REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
MEV = "src/main/java/com/hjmmd_8/bettergold/event/ModEvents.java"
ARGS = "build/moddev/clientRunProgramArgs.txt"
SERVER_PROPS = "run/server.properties"


def p(rel):
    return os.path.join(REPO, rel.replace("/", os.sep))


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def patch(rel, old, new, count=1):
    path = p(rel)
    raw = open(path, "rb").read()
    if raw.count(old) != count:
        raise SystemExit("SETUP-FAIL: %s 里模式出现 %d 次（期望 %d）" % (rel, raw.count(old), count))
    open(path, "wb").write(raw.replace(old, new))
    print("patched %s (%d -> %d bytes)" % (rel, len(raw), len(raw) + count * (len(new) - len(old))))


# 用一行 ASCII 锚点做"改前"对照：把整块触发（守卫 + 调用）换成一句注释
GUARD_OLD = (b"                if (player instanceof ServerPlayer serverPlayer) {\r\n"
             b"                    CriteriaTriggers.PLACED_BLOCK.trigger(serverPlayer, plantPos, held);\r\n"
             b"                }\r\n")
GUARD_NEW = b"                // bgfinal3 BEFORE-FIX CONTROL: PLACED_BLOCK.trigger removed\r\n"

action = sys.argv[1]

if action == "level-on":
    patch(SERVER_PROPS, b"level-name=world", b"level-name=bgfinal3probe")
elif action == "level-off":
    patch(SERVER_PROPS, b"level-name=bgfinal3probe", b"level-name=world")
elif action == "flag-on":
    for name in ("bgfinal3-probe.enabled", "bgfinal3-client-probe.enabled"):
        open(p("run/" + name), "w").write("bgfinal3\n")
    print("flag files created")
elif action == "flag-on-server":
    # ⚠ 服务端探针的开关与客户端探针**共用同一个 GAMEDIR（run/）**：
    #   客户端跑测时若同时留着 bgfinal3-probe.enabled，那个服务端探针会在**整合服务端**里
    #   一起 armed，并在它的 tick 表末尾 `server.halt(false)` ⇒ 把客户端的世界直接关掉
    #   （本轮真踩：客户端只跑到 tick ~100 就 "Client disconnected with reason: 服务器已关闭"）。
    f = p("run/bgfinal3-probe.enabled")
    open(f, "w").write("bgfinal3\n")
    c = p("run/bgfinal3-client-probe.enabled")
    if os.path.isfile(c):
        os.remove(c)
    print("server flag only")
elif action == "flag-on-client":
    f = p("run/bgfinal3-client-probe.enabled")
    open(f, "w").write("bgfinal3\n")
    s = p("run/bgfinal3-probe.enabled")
    if os.path.isfile(s):
        os.remove(s)
    print("client flag only")
elif action == "flag-off":
    for name in ("bgfinal3-probe.enabled", "bgfinal3-client-probe.enabled"):
        f = p("run/" + name)
        if os.path.isfile(f):
            os.remove(f)
    print("flag files removed")
elif action == "args-on":
    patch(ARGS, b"# User Supplied Program Arguments",
          b"# User Supplied Program Arguments\n--quickPlaySingleplayer bgfinal3cprobe")
elif action == "args-off":
    patch(ARGS, b"# User Supplied Program Arguments\n--quickPlaySingleplayer bgfinal3cprobe",
          b"# User Supplied Program Arguments")
elif action == "world-in":
    src, dst = p("run/bgfinal3probe"), p("run/saves/bgfinal3cprobe")
    if not os.path.isdir(src):
        raise SystemExit("SETUP-FAIL: 没有 %s（先跑一轮 runServer）" % src)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print("copied world -> %s" % dst)
elif action == "world-out":
    for rel in ("run/bgfinal3probe", "run/saves/bgfinal3cprobe"):
        d = p(rel)
        if os.path.isdir(d):
            shutil.rmtree(d)
            print("removed %s" % d)
elif action == "notrigger-on":
    patch(MEV, GUARD_OLD, GUARD_NEW)
elif action == "notrigger-off":
    patch(MEV, GUARD_NEW, GUARD_OLD)
elif action == "hash":
    print(sha(p(sys.argv[2])))
else:
    raise SystemExit("unknown action: %s" % action)
