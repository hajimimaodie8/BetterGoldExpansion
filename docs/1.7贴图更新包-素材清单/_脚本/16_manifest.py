# -*- coding: utf-8 -*-
"""生成 bg17tex 关卡的权益清单（tools/asset-generator/bg17tex_manifest.tsv）。

清单三栏：path <TAB> sha256 <TAB> role
  role = authorized  -> 本轮回第五次授权替换的 72 张，钉"改后 SHA"，并要求"不得等于改前 SHA"
         untouched   -> 其余 554 张，钉"必须保持的 SHA"（负向断言）
  anchors 两张既有锚点另在关卡里用稳定 ASCII id 单独命名。
"""
import sys, os, hashlib
sys.stdout.reconfigure(errors="replace")

BASE = r"E:\mc\mcmod\bettergold-template-1.21.1"
TEX = os.path.join(BASE, "src", "main", "resources", "assets", "bettergold", "textures")
ZIPDIR = os.path.join(BASE, "docs", "1.7贴图更新包-素材清单")
OUTDIR = os.path.join(BASE, "tools", "asset-generator")
EVID = os.path.join(ZIPDIR, "_证据", "替换记录")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def main():
    rows = []
    with open(os.path.join(ZIPDIR, "认亲表.tsv"), encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            rows.append(dict(zip(hdr, line.rstrip("\n").split("\t"))))
    auth = {r["target"]: r["file"] for r in rows if r["verdict"] == "确定"}

    cur = {}
    for dp, dn, fn in os.walk(TEX):
        for f in fn:
            p = os.path.join(dp, f)
            cur[os.path.relpath(p, TEX).replace("\\", "/")] = sha(p)

    lines = ["path\tsha256\trole\torigin_zipfile"]
    nauth = 0
    for k in sorted(cur):
        if k in auth:
            lines.append("%s\t%s\tauthorized\t%s" % (k, cur[k], auth[k]))
            nauth += 1
        else:
            lines.append("%s\t%s\tuntouched\t-" % (k, cur[k]))
    p = os.path.join(OUTDIR, "bg17tex_manifest.tsv")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("[manifest] total=%d authorized=%d untouched=%d -> %s"
          % (len(cur), nauth, len(cur) - nauth, p))

    # 改前 SHA 清单（供关卡"不得回退"用）
    with open(os.path.join(EVID, "替换记录.tsv"), encoding="utf-8") as f:
        h = f.readline().rstrip("\n").split("\t")
        recs = [dict(zip(h, l.rstrip("\n").split("\t"))) for l in f]
    p2 = os.path.join(OUTDIR, "bg17tex_old_sha.tsv")
    with open(p2, "w", encoding="utf-8", newline="\n") as f:
        f.write("path\told_sha256\n")
        for r in sorted(recs, key=lambda r: r["target"]):
            f.write("%s\t%s\n" % (r["target"], r["sha_before"]))
    print("[manifest] old_sha=%d -> %s" % (len(recs), p2))


if __name__ == "__main__":
    main()
