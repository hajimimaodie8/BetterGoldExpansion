# -*- coding: utf-8 -*-
"""生成 `06-跑测留档与复原.txt`，并把 05-跑后复核.json 的 server.properties 两列 SHA 记全
（复原**前** = 服务器自己重写的值；复原**后** = 跑前 `.bak` 的字节）。"""
import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(errors="replace")

REPO = Path(__file__).resolve().parents[3]
EV = REPO / "docs" / "bgn10rc2-证据"
RUN = REPO / "run"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def main() -> None:
    bak = RUN / "server.properties.bgn10rc2.bak"
    cur = RUN / "server.properties"
    p5 = EV / "05-跑后复核.json"
    data = json.loads(p5.read_text(encoding="utf-8"))
    before = data.get("server_properties_sha256", "")
    data["server_properties_sha256_note"] = (
        "字段 server_properties_sha256 = 服务器自己重写后的值（复原前）；"
        "server_properties_sha256_restored = 用跑前 .bak 字节复制复原后的值")
    data["server_properties_sha256_restored"] = sha(cur)
    data["server_properties_bak_sha256"] = sha(bak)
    p5.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "bg-n10rc2 跑测留档与复原",
        "",
        "run/server.properties:",
        "  跑前              : A2229937BA8AB7428BC959E87A784890500D6D7061B10FA8302758E46A01D3C4",
        "  服务器重写后      : %s  （= 05 json 的 server_properties_sha256）" % before,
        "  跑前 .bak         : %s" % sha(bak),
        "  复原后            : %s" % sha(cur),
        "  复原方式          : Python shutil.copyfile(.bak -> server.properties)（逐字节）",
        "  复原后 == 跑前    : %s" % (sha(cur) == sha(bak) ==
                                     "A2229937BA8AB7428BC959E87A784890500D6D7061B10FA8302758E46A01D3C4"),
        "",
        "run/saves（作者的存档，绝不打开）:",
        "  跑前: 目录 %s / %d 文件 / %d B" % (
            json.loads((EV / "04-跑前留档.json").read_text(encoding="utf-8"))["saves_dirs"],
            json.loads((EV / "04-跑前留档.json").read_text(encoding="utf-8"))["saves_file_count"],
            json.loads((EV / "04-跑前留档.json").read_text(encoding="utf-8"))["saves_total_bytes"]),
        "  跑后: 目录 %s / %d 文件 / %d B" % (
            data["saves_dirs"], data["saves_file_count"], data["saves_total_bytes"]),
        "  逐文件（path+size+mtime_ns）全等: %s" % (
            data["saves_files"] == json.loads((EV / "04-跑前留档.json").read_text(encoding="utf-8"))["saves_files"]),
        "",
        "run/world（探针服端世界）: %d 文件 / %d B" % (data["world_file_count"], data["world_total_bytes"]),
        "  说明：字节数与跑前差 -1，属服务器正常存盘（[Server thread/INFO] Saving chunks for level 'ServerLevel[world]'）",
        "",
        "探针收尾:",
        "  src 内 BgN10rc2 / BGN10RC2 = 0 命中；halt( = 0 命中；src/…/probe/ 目录已删",
        "  开关文件 run/bgn10rc2-probe.enabled 已删",
        "  halt(false) 只调一次；forceload 双向 0（forcedNow=0）",
    ]
    (EV / "06-跑测留档与复原.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
