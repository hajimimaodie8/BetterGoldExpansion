import pathlib
import re

p = pathlib.Path(r"E:\mc\mcmod\bettergold-template-1.21.1\src\main\java\com\hjmmd_8\bettergold\probe\BgN10vProbe.java")
t = p.read_text(encoding="utf-8")
pat = re.compile(r'Path\.of\(((?:"[^"]*")(?:\s*,\s*\n?\s*"[^"]*")*)\)', re.S)


def rep(m):
    parts = re.findall(r'"([^"]*)"', m.group(1))
    if parts and parts[0] == "src":
        return 'res("' + "/".join(parts) + '")'
    return m.group(0)


t2 = pat.sub(rep, t)
p.write_text(t2, encoding="utf-8", newline="\n")
print('remaining Path.of("src"):', t2.count('Path.of("src"'))
print("res( count:", t2.count('res("'))
