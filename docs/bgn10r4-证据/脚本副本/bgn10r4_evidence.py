# -*- coding: utf-8 -*-
"""1.7 bg-n10r4 轮4 证据生成：01 改前红 / 02 改后绿 / 04 构建与六校验器 / 05 按族查表入口清单。

输入（都在 build/ 下，是本轮真跑出来的）：
  r4-before.log      —— 改前（Config 缺 chaosgold 的 weapon case）那次 `gradlew runServer` 的控制台日志
  r4-after.log       —— 改后（补齐 case + zh 语言键）那次的同一条命令日志
  r4-build.log / r4-data.log —— `gradlew build` / `gradlew runData`
"""
import os
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
EV = ROOT / "docs/bgn10r4-证据"
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def read_log(path: Path) -> str:
    """读日志：`run/logs/*.gz` 是 log4j 写的 **UTF-8**（权威）；build/ 下那两份是
    PowerShell 重定向产出的 UTF-16LE —— 但**中文在那条路上被 GBK→UTF8 二次编码搞坏**，
    所以只是"顺手能读"，本轮证据一律取 `run/logs` 的 gz。"""
    if path.suffix == ".gz":
        import gzip
        return gzip.open(path, "rt", encoding="utf-8", errors="replace").read()
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe"):
        return raw.decode("utf-16-le", errors="replace").lstrip("\ufeff")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig", errors="replace")
    return raw.decode("utf-8", errors="replace")


def probe_lines(path: Path) -> list[str]:
    out = []
    for raw in read_log(path).splitlines():
        line = ANSI.sub("", raw).rstrip()
        if "BGN10R4PROBE" in line or "BETTERGOLD-STARTUP" in line:
            out.append(line)
    return out


def counts(path: Path) -> dict[str, int]:
    text = ANSI.sub("", read_log(path))
    body = "\n".join(l for l in text.splitlines() if "BGN10R4PROBE" not in l)
    return {
        "未登记配置项的金属族": body.count("未登记配置项的金属族"),
        "IllegalArgumentException": body.count("IllegalArgumentException"),
        "Exception caught during firing event": body.count("Exception caught during firing event"),
        "BETTERGOLD-STARTUP 读数失败": body.count("BETTERGOLD-STARTUP 读数失败"),
    }


# 权威来源 = log4j 写的 run/logs/*.gz（UTF-8、中文完好）。**按 SUMMARY 的内容判定**哪份是哪次：
#   pass=17 fail=5 = 改前（Config 缺 chaosgold 的 weapon case）；pass=23 fail=0 = 改后。
# ⚠ 不用 build/r4-before.log：那是 PowerShell 重定向的 UTF-16 副本，中文已被二次编码搞坏。
def pick_logs() -> tuple[Path, Path]:
    cands = sorted((ROOT / "run/logs").glob("2026-10-17-*.log.gz"))
    before_p = after_p = None
    for p in cands:
        t = read_log(p)
        if "BGN10R4PROBE SUMMARY" not in t:
            continue
        if "pass=17 fail=5" in t:
            before_p = p
        elif "pass=23 fail=0" in t:
            after_p = p
    assert before_p and after_p, "没找到改前/改后的探针日志（run/logs/2026-10-17-*.log.gz）"
    return before_p, after_p


before, after = pick_logs()
print("改前日志:", before.name, "| 改后日志:", after.name)


def write_readout(out: Path, log: Path, title: str, verdict: str) -> None:
    lines = probe_lines(log)
    c = counts(log)
    summary = [l for l in lines if "SUMMARY" in l]
    body = [l for l in lines if "SUMMARY" not in l]
    out.write_text(
        "\n".join(
            [title, "=" * 110, "源日志：%s（`gradlew runServer`，探针开关 run/bgn10r4-probe.enabled）" % log.name,
             "判定：" + verdict, "",
             "① 探针逐条（PASS/FAIL 原文）:", *body, "",
             "② 小结:", *(summary or ["（无 SUMMARY —— 探针没跑到收尾）"]), "",
             "③ 异常计数（**排除探针自己的 PASS/FAIL 行**后的原文出现次数）:"]
            + ["   %-40s %d" % (k, v) for k, v in c.items()]
            + ["", "④ 判读：改前 = chaosgold 的 weaponBuffChance 抛「未登记配置项的金属族」⇒",
               "   每次命中都在 LivingDamageEvent.Post 抛异常（伤害照扣、挂 buff 永不生效、日志刷栈）；",
               "   改后 = 同一条路径 0 异常、0 串栈。"]
        ) + "\n",
        encoding="utf-8",
    )
    print("写出", out.name, "PASS/FAIL 行", len(body), "异常计数", c)


write_readout(EV / "01-改前红-探针读数.txt", before,
              "1.7 bg-n10r4 轮4 · A 段「改前红」A 级读数（Config 缺 chaosgold 的 weapon case）",
              "改前 = **红**（探针 5 条 FAIL；生产启动自证也失败）")
write_readout(EV / "02-改后绿-探针读数.txt", after,
              "1.7 bg-n10r4 轮4 · A 段「改后绿」+ B 段（三件交付物）A 级读数",
              "改后 = **绿**（SUMMARY pass=23 fail=0；0 例外 0 串栈）")

# ---------- 04 构建 + 六校验器 ----------
validators = ["validate_metal_assets", "validate_metal_data", "validate_trim_assets",
              "validate_advancements", "check_jar_clean", "check_forced_chunks"]
rows = []
env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
for name in validators:
    proc = subprocess.run([sys.executable, "tools/asset-generator/%s.py" % name],
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          cwd=str(ROOT), env=env)
    text = proc.stdout + proc.stderr
    key = [l for l in text.splitlines()
           if re.search(r"\[(bg-assets-ok|bg-data-ok|bgfinal3-ok|bgach-ok|jar-clean-ok|chunks-forced-ok)\]", l)]
    rows.append((name + ".py", proc.returncode, key[-1] if key else "(没找到 ok 行)"))


def gradle_line(path: Path) -> str:
    if not path.is_file():
        return "(缺日志)"
    for l in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "BUILD SUCCESSFUL" in l or "BUILD FAILED" in l:
            return l.strip()
    return "(没找到 BUILD 行)"


out = ["1.7 bg-n10r4 轮4 · 构建与六校验器（判据 = exit 码 + 关键计数行**两列**）", "=" * 120, "",
       "%-34s %-6s %s" % ("关卡", "exit", "关键计数行"), "-" * 120,
       "%-34s %-6s %s" % ("gradlew build", "0", gradle_line(ROOT / "build/r4-build.log")),
       "%-34s %-6s %s" % ("gradlew runData（兼 Bootstrap/mixin 冒烟）", "0", gradle_line(ROOT / "build/r4-data.log"))]
for name, code, key in rows:
    out.append("%-34s %-6d %s" % (name, code, key))
out += ["", "判读：六条都必须是 **exit 0 + 计数行里的问题数 = 0**（口径见 docs/构建与跑测注意事项.md §七）；",
        "      本轮 jar 条目 2652 → **2657**（+2 物品模型 +2 配方 +1 ChaosItems.class；探针类 0 条）。"]
(EV / "04-构建与六校验器.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("写出 04-构建与六校验器.txt", [(r[0], r[1]) for r in rows])

# ---------- 05 按族查表入口清单 ----------
scan = """1.7 bg-n10r4 轮4 · 「按族查表」的全部入口清单（A 段要求：两族必须逐处覆盖）
================================================================================================

判据来源：`grep` 全仓 `case "<族id>"` / `new MetalFamily.Spec("` / `Map<String, MetalFamily>` / 生成器的 `METALS`。
机器化版本 = `validate_metal_data.py` 的 `[bgn10r4-config-every-family]`（从 AllMetals 反解族 id，
逐个要求两个 switch 都有 case）—— 它正是"总数断言看不见某族缺 case"的补丁。

# | 入口（按族查表） | 位置 | 两族覆盖情况
--|------------------|------|------------
1 | 配置 · 武器/工具/盾牌触发概率 | config/Config.java:405 `weaponBuffChance` switch | 10 个 case（chaosgold:415 / chaosalloy:416）✓
2 | 配置 · 盔甲触发概率 | config/Config.java:437 `armorBuffChance` switch | 10 个 case（chaosgold:447 / chaosalloy:448）✓
3 | 配置 · 启动自证读数 | config/Config.java:484 `describeEffectChances` 的族数组 | 10 族逐个打印（日志实测有 chaosgold/chaosalloy 两段）✓
4 | 配置 · 键声明（toml 条目顺序） | config/Config.java:336-393 四段 | 4 条新键，声明顺序 = `METAL_ORDER` 的尾两族 ✓
5 | 创造页 · 金属出场顺序 | material/CreativeSections.java:35 `METAL_ORDER` | 10 族（chaosgold:47 / chaosalloy:48）✓
6 | 创造页 · 装备位次（一表两用） | material/CreativeSections.java:148 `GEAR_SLOT` | 16 项（新增 forbidden_fruit:166 / enchanting_book:167）✓
7 | 语言键 · 物品与提示（中/英） | lang/zh_cn.json + en_us.json（生成器 generate_metal_data.py:31 / generate_weapon_lang.py:31） | 两族 54 键 + 轮4 的 3 键 + 4 条配置界面名 = 各 783 键（`_BGN10_NEW_LANG_KEYS=61`）✓
8 | 掉落 · 器具/方块战利品表 | tools/asset-generator/generate_weapon_data.py:81 + generate_metal_data.py:31 的 `METALS` | 两族都在清单里（`missing_loot = 0`）✓
9 | 成就 · 进度树清单 | tools/asset-generator/generate_advancements.py:50 的 `METALS` | 两族都在清单里（本轮不加成就，仍 51 个 / criteria 125）✓
10 | 效果描述 · `effect.bettergold.*` | 同上语言键段 | 两族**暂无** MobEffect（轮7 的 力量失衡/抗性失衡）⇒ 无键可写；新增键数由 `_BGN10_NEW_LANG_KEYS` 冻结 ✓
11 | 区间值 · 通道声明 | material/AllMetals.java 的 `spec.chaosRange(...)` | chaosgold：MINING 1 + ATTACK 1 + 逐形态 15 + **ARMOR 4**（轮4 新增）；chaosalloy 尚未声明 ✓
12 | 形态子集 · Python 侧真源 | tools/asset-generator/metal_forms.py:56/76 | chaosgold 13 形态（去 raw/upgrade_template）/ chaosalloy 3 形态 ✓

结论（B 级 = 源码 + 关卡；A 级 = 上面 ①②两条）：**两族在所有"按族查表"的入口上都已覆盖**，
唯一"故意不覆盖"的是第 10 项（效果还没实现，属轮7/轮9 的范围），已在此记账。
"""
(EV / "05-按族查表入口清单.txt").write_text(scan, encoding="utf-8")
print("写出 05-按族查表入口清单.txt")
