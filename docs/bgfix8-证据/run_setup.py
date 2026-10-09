# -*- coding: utf-8 -*-
"""bgfix8：跑测前的临时改动（server.properties 的 level-name + 两个探针开关），全部可逐字节复原。

用法：
  python probe/bgfix8/run_setup.py before-server   # 备份/改 level-name + 开服务端探针开关
  python probe/bgfix8/run_setup.py after-server    # 用 .bak 逐字节复原 server.properties
  python probe/bgfix8/run_setup.py before-client    # 只放客户端探针开关（**先确保服务端开关已删**）
  python probe/bgfix8/run_setup.py clean            # 删掉两个开关文件并复核 server.properties 哈希
"""
import hashlib
import os
import shutil
import sys

sys.stdout.reconfigure(errors="replace")

REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
RUN = os.path.join(REPO, "run")
SP = os.path.join(RUN, "server.properties")
BAK = os.path.join(REPO, "build", "bgfix8-baseline", "server.properties.bak")
S_FLAG = os.path.join(RUN, "bgfix8s-probe.enabled")
C_FLAG = os.path.join(RUN, "bgfix8c-probe.enabled")

# 跑前基线（本机实测）：A2229937BA8AB7428BC959E87A784890500D6D7061B10FA8302758E46A01D3C4
BASE_SHA = "A2229937BA8AB7428BC959E87A784890500D6D7061B10FA8302758E46A01D3C4"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def cmd(what):
    if what == "before-server":
        os.makedirs(os.path.dirname(BAK), exist_ok=True)
        if not os.path.isfile(BAK):
            shutil.copyfile(SP, BAK)
            print("BACKUP  server.properties -> %s  sha=%s" % (BAK, sha(BAK)))
        else:
            print("BACKUP  already exists sha=%s" % sha(BAK))
        raw = open(SP, "rb").read()
        assert raw[:3] != b"\xef\xbb\xbf"
        old = b"level-name=world"
        assert raw.count(old) == 1, "level-name 行不唯一：%d" % raw.count(old)
        new = raw.replace(old, b"level-name=bgfix8probe")
        open(SP, "wb").write(new)
        open(S_FLAG, "w").write("bgfix8 server probe\n")
        print("CHANGED level-name=world -> bgfix8probe  (CRLF=%d BOM=%s)"
              % (new.count(b"\r\n"), new[:3] == b"\xef\xbb\xbf"))
        print("FLAG    %s = %s" % (S_FLAG, os.path.isfile(S_FLAG)))
    elif what == "after-server":
        shutil.copyfile(BAK, SP)          # ★ 一律用"跑前 .bak 字节复制"复原
        print("RESTORED server.properties from .bak  sha=%s  matches-baseline=%s"
              % (sha(SP), sha(SP) == BASE_SHA))
        if os.path.isfile(S_FLAG):
            os.remove(S_FLAG)
        print("REMOVED server flag, exists=%s" % os.path.isfile(S_FLAG))
    elif what == "before-client":
        assert not os.path.isfile(S_FLAG), "服务端探针开关还在 ⇒ 客户端那一轮会被它 halt（先删）"
        open(C_FLAG, "w").write("bgfix8 client probe\n")
        print("FLAG    client=%s / server=%s" % (os.path.isfile(C_FLAG), os.path.isfile(S_FLAG)))
    elif what == "clean":
        for p in (S_FLAG, C_FLAG):
            if os.path.isfile(p):
                os.remove(p)
        print("FLAGS   server=%s client=%s" % (os.path.isfile(S_FLAG), os.path.isfile(C_FLAG)))
        print("server.properties sha=%s  matches-baseline=%s" % (sha(SP), sha(SP) == BASE_SHA))
    else:
        raise SystemExit("unknown: " + what)


cmd(sys.argv[1])
