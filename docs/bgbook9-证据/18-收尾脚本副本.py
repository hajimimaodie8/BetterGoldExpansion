# -*- coding: utf-8 -*-
"""bg-book §九：收尾（删探针 / 复原临时改动 / 逐字节核对 / 收集证据）。

⚠ 顺序（父代理口令）：
   ① **先把探针源码复制到证据目录**，再删（上一轮教训：删了才发现不可恢复）；
   ② 只删自己的子目录 `probe/bgbook9/`（**绝不递归删整个 `probe/`**）；
   ③ 临时改动逐字节复原 + SHA256 相中；
   ④ `run/saves` 与跑前 manifest 逐行比对（**作者存档 `新的世界` 一个字节都不许变**）。

Run: python build\\bgbook9-teardown.py
"""
import hashlib
import io
import os
import shutil
import sys

sys.stdout.reconfigure(errors="replace")
REPO = r"E:\mc\mcmod\bettergold-template-1.21.1"
EVID = os.path.join(REPO, "docs", "bgbook9-证据")
BUILD = os.path.join(REPO, "build")
PROBE_DIR = os.path.join(REPO, "src", "main", "java", "com", "hjmmd_8", "bettergold", "probe", "bgbook9")

# 目标哈希（跑测前记录）
TARGET = {
    "build.gradle": "2aac7860e5b1f03128d42637b9f002c7a44f37e269ee6b7bc9dfbe41ad478c2f",
    "src/main/java/com/hjmmd_8/bettergold/bettergold.java":
        "e2c293da27e15943ba6221a5deb54d941a91e8cebea7f4175cb6a3c72fd3fc9b",
    "run/server.properties": "a2229937ba8ab7428bc959e87a784890500d6d7061b10fa8302758e46a01d3c4",
    "build/moddev/clientRunProgramArgs.txt": "a365a5edf7abc44c576e5dd3f725a54d46658fcddc1e3a0257bec7c0ab2e4bdb",
}
REPORT = []


def sh(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


def say(msg):
    print(msg)
    REPORT.append(msg)


def main():
    os.makedirs(EVID, exist_ok=True)

    # ---------- ① 探针源码先落证据 ----------
    if os.path.isdir(PROBE_DIR):
        for fn in sorted(os.listdir(PROBE_DIR)):
            src = os.path.join(PROBE_DIR, fn)
            dst = os.path.join(EVID, "11-探针源码副本-%s.txt" % fn.replace(".java", ""))
            shutil.copyfile(src, dst)
            say("probe source archived: %s -> %s (%d bytes)" % (fn, os.path.basename(dst), os.path.getsize(dst)))

    # ---------- ② 只删自己的子目录 ----------
    if os.path.isdir(PROBE_DIR):
        shutil.rmtree(PROBE_DIR)
        say("removed probe dir: %s" % PROBE_DIR)
    parent = os.path.dirname(PROBE_DIR)
    if os.path.isdir(parent):
        left = os.listdir(parent)
        say("probe/ 目录剩余内容（只应看不出别人被删）: %r" % (left,))
        if not left:
            os.rmdir(parent)
            say("probe/ 已空 ⇒ 一并删除（只删这一层）")
    for fn in ("bgbook9-probe.enabled", "bgbook9-client-probe.enabled"):
        p = os.path.join(REPO, "run", fn)
        if os.path.exists(p):
            os.remove(p)
            say("switch file removed: run/%s" % fn)

    # ---------- ③ 临时改动复原（逐字节）----------
    for rel, want in TARGET.items():
        p = os.path.join(REPO, rel.replace("/", os.sep))
        if not os.path.isfile(p):
            say("RESTORE-MISSING %s" % rel)
            continue
        got = sh(p)
        say("%-52s want=%s got=%s %s"
            % (rel, want[:16], got[:16], "OK" if got == want else "**MISMATCH**"))

    # ---------- ④ 删自己的探针世界 / 存档副本 ----------
    for rel in ("run/bgbook9probe", "run/saves/bgbook9cprobe"):
        p = os.path.join(REPO, rel.replace("/", os.sep))
        if os.path.isdir(p):
            shutil.rmtree(p)
            say("removed probe world: %s" % rel)
        else:
            say("probe world already absent: %s" % rel)

    # ---------- ⑤ run/saves 与跑前 manifest 逐行比对 ----------
    pre = os.path.join(BUILD, "bgbook9-pre-manifest.txt")
    if os.path.isfile(pre):
        lines = io.open(pre, encoding="utf-8").read().split("\n")
        i = lines.index("== dir run/saves ==")
        want = {}
        for ln in lines[i + 1:]:
            if ln.startswith("== "):
                break
            if not ln.strip():
                continue
            h, size, rel = ln.split("  ", 2)
            want[rel] = (h, size)
        now = {}
        root = os.path.join(REPO, "run", "saves")
        for dp, dn, fns in os.walk(root):
            dn.sort()
            for fn in sorted(fns):
                fp = os.path.join(dp, fn)
                r = os.path.relpath(fp, root).replace(os.sep, "/")
                now[r] = (sh(fp), str(os.path.getsize(fp)))
        only_pre = sorted(set(want) - set(now))
        only_now = sorted(set(now) - set(want))
        diff = sorted(k for k in set(want) & set(now) if want[k] != now[k])
        say("run/saves 跑前 %d 个文件 / 现在 %d 个；仅在跑前=%r 仅在现在=%r 内容不同=%r"
            % (len(want), len(now), only_pre, only_now, diff))

    # ---------- ⑥ 证据文件收集 ----------
    copies = [
        ("bgbook9-perturb-result.txt", "01-关卡扰动实测.txt"),
        ("bgbook9-run1-bg9p.txt", "03-A级-runServer-不就地转换与礼物盒抽样.txt"),
        ("bgbook9-perturb.py", "05-扰动脚本副本.py"),
        ("bgbook9-inject-lang.py", "06-语言键注入脚本副本.py"),
        ("bgbook9-make-snapshot.py", "07-快照搬运脚本副本.py"),
        ("bgbook9-fixture.py", "09-跑测临时改动脚本副本.py"),
        ("bgbook9-manifest.py", "10-逐文件SHA256-manifest脚本.py"),
        ("bgbook9-revert-fix1.py", "15-回退改写脚本副本.py"),
        ("bgbook9-pre-manifest.txt", "13-扰动前manifest.txt"),
        ("bgbook9-le.py", "16-行尾与哈希实测脚本副本.py"),
    ]
    for src, dst in copies:
        sp = os.path.join(BUILD, src)
        if os.path.isfile(sp):
            shutil.copyfile(sp, os.path.join(EVID, dst))
            say("evidence copied: %s -> %s" % (src, dst))
        else:
            say("evidence MISSING: %s" % src)

    io.open(os.path.join(EVID, "08-收尾清理与逐字节复原.txt"), "w",
            encoding="utf-8", newline="\n").write("\n".join(REPORT) + "\n")
    print("---- teardown report written ----")


if __name__ == "__main__":
    main()
