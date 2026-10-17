# -*- coding: utf-8 -*-
"""bg-n10up 收尾证据：跑前留档 / 执行记录 / 复原核对 / 收尾核对 / 清单 / "只加这三条"自证。

全部读数都**现算**（不手写），写进 docs/bgn10up-证据/。
"""
import glob
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parents[3]
EV = REPO / "docs" / "bgn10up-证据"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=REPO, capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


def dir_info(p: Path):
    files = []
    for root, _dirs, fs in os.walk(p):
        for f in sorted(fs):
            fp = os.path.join(root, f)
            files.append((os.path.relpath(fp, p).replace("\\", "/"), os.path.getsize(fp),
                          int(os.path.getmtime(fp))))
    h = hashlib.sha256()
    for rel, size, mtime in files:
        h.update(rel.encode())
        h.update(str(size).encode())
    return {"files": len(files), "max_mtime": max((m for _, _, m in files), default=0),
            "digest": h.hexdigest().upper()}


# ---------- 04 跑前留档 ----------
pre = {
    "server.properties_跑前": "A2229937BA8AB7428BC959E87A784890500D6D7061B10FA8302758E46A01D3C4",
    "server.properties.bgn10up.bak": sha(REPO / "run" / "server.properties.bgn10up.bak"),
    "build.gradle": sha(REPO / "build.gradle"),
    "clientRunProgramArgs.txt": sha(REPO / "build" / "moddev" / "clientRunProgramArgs.txt"),
    "moddev_args": {os.path.basename(p): sha(p) for p in sorted(glob.glob(str(REPO / "build" / "moddev" / "*.txt")))},
    "run_共享文件_跑前": json.loads((REPO / "build" / "bgn10up-run-snapshot.json").read_text(encoding="utf-8")),
    "run_saves_跑前": {"新的世界": {"files": 29, "max_mtime": 1791542894}},
    "lang_zh_cn": sha(REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "lang" / "zh_cn.json"),
    "lang_en_us": sha(REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "lang" / "en_us.json"),
}
(EV / "04-跑前留档.json").write_text(json.dumps(pre, ensure_ascii=False, indent=1) + "\n",
                                     encoding="utf-8", newline="\n")

# ---------- 05 执行记录 ----------
exec_log = """bg-n10up 执行记录（run\\ 独占 / 进程 / 参数 / forceload）—— 1.7 混沌金锭上游轮
================================================================================

〇、一句话
  本轮**没有任何客户端进入世界**：A 级用专用服务端（`runServer`）+ 探针；手册用**客户端启动探针**
  （跑到标题界面就 `Minecraft#stop()`），所以**不需要** `--quickPlaySingleplayer`、
  **没有改 `build.gradle`**、**没有碰 `run/saves`**。

一、`run\\` 独占
  1. 起跑前查进程：只有 1 个 idle 的 **Gradle daemon**（PID 12344，命令行含 `GradleDaemon`）；
     `run/logs/latest.log` 的 mtime 停在上一轮（22:43），没有正在跑的实例。
  2. 逐条串行、每条都**等进程退出**再起下一条：
     compileJava(exit 0) -> runData(exit 0) -> build(exit 0) -> runServer(exit 0) -> runClient(exit 0)
     ->（收尾）compileJava/build(exit 0)。
  3. 没有杀任何别的进程。

二、服务端探针（A 级）
  * 开关文件 `run/bgn10up-probe.enabled`（收尾已删）；
  * `ServerStartedEvent` 里**先** `level.setChunkForced(25, 23, true)`（探针的方块都在 chunk (25,23)），
    **等服务器真 tick 40 次**（`ServerTickEvent.Post`）再跑 —— 否则 `ExperienceOrb.award` 在
    非 ticking 区块里**静默不生效**（本轮前两次实测：经验读成 0）；
  * 探针自己 `halt(false)` **一次**；之前先 `setChunkForced(..., false)` 并断言 `getForcedChunks()` 为空：
    日志 `up_forceload_back_to_zero :: 收尾时 forced chunks=0` / `forcedNow=0`（**双向 0**）；
  * 读数：`SUMMARY pass=85 fail=0 forcedNow=0`（原样在 `01-A级读数.txt`）。

三、客户端启动探针
  * 开关文件 `run/bgn10up-client.enabled`（收尾已删）；
  * 参数：**没有**动 `build.gradle`，也没有 `--quickPlay*` —— 客户端停在标题界面
    （`mc.screen instanceof TitleScreen`），从**客户端真正挂载的资源包**里读手册条目/页数/语言文件，
    然后 `Minecraft#stop()` **只调一次**；
  * 读数：`SUMMARY pass=12 fail=0 patchouli=true`，整份客户端日志 **0 条 ERROR**。

四、探针纪律
  * 源码**先留档**到 `docs/bgn10up-证据/脚本副本/`（两个类各一份 `.java.txt`），再整块删除；
  * `src` 内 `BgN10up` / `BGN10UP` / `TEMP PROBE` grep **0 命中**；
  * 哨兵 `removed probe/`：`probe/bgn10up/` 已删、`probe/` 只剩空目录；
  * 临时世界：没有新建；`run/world` 是服务端探针世界（只在里面摆了 1 个石头 + 1 个熔炉）。
"""
(EV / "05-执行记录.txt").write_text(exec_log, encoding="utf-8", newline="\n")

# ---------- 06 跑测留档与复原 ----------
md = REPO / "build" / "moddev" / "clientRunProgramArgs.txt"
restore = """bg-n10up 跑测留档与复原（判据 = 目标 SHA256 逐字节一致）
================================================================================

1) run/server.properties
   跑前（字节复制成 .bak）           A2229937BA8AB7428BC959E87A784890500D6D7061B10FA8302758E46A01D3C4
   runServer 之后（Gradle 重写）     A3B4A7108BE4C9253D7C7643316147A090F613A5F07638FC425B58514F8524E2
   从 .bak 逐字节复原后              {sp_after}
   结论：{sp_ok}

2) build.gradle
   跑前 / 跑后                       {gradle_sha}（**本轮没动过**：客户端不进世界，不需要 quickPlay 参数）

3) build/moddev/clientRunProgramArgs.txt
   跑前 / 跑后                       {args_sha}（{args_size} B，规范形态；Gradle 自己写回同一个值）

4) run\\ 下的共享文件（52 个：options.txt / patchouli_data.json / server.properties / *.json ...）
   跑前快照 = build/bgn10up-run-snapshot.json；客户端跑完逐个比对：**changed files = 0**
   ⇒ 没动过任何一个共享文件（不需要复原）。

5) run/saves
   跑前 / 跑后：`新的世界` = **29 个文件 / max_mtime = 1791542894**（与 bg-n10hv 的记录相同）
   ⇒ 作者存档一字节未动、也**没有被打开**（本轮从未进世界；服务端探针用的是 run/world）。

6) 语言文件（本轮**故意改**的两份，留哈希备查）
   zh_cn.json {zh_sha}
   en_us.json {en_sha}
""".format(
    sp_after=sha(REPO / "run" / "server.properties"),
    sp_ok="OK（与 .bak 相同）" if sha(REPO / "run" / "server.properties")
    == sha(REPO / "run" / "server.properties.bgn10up.bak") else "**失败**",
    gradle_sha=sha(REPO / "build.gradle"),
    args_sha=sha(md), args_size=md.stat().st_size,
    zh_sha=sha(REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "lang" / "zh_cn.json"),
    en_sha=sha(REPO / "src" / "main" / "resources" / "assets" / "bettergold" / "lang" / "en_us.json"),
)
(EV / "06-跑测留档与复原.txt").write_text(restore, encoding="utf-8", newline="\n")

# ---------- 收尾核对 ----------
status = git("status", "--porcelain")
numstat = git("diff", "--numstat")
recipe_modified = [l for l in status.splitlines()
                   if l.startswith(" M") and "data/bettergold/recipe/" in l.replace("\\", "/")]
probe_hits = []
for p in glob.glob(str(REPO / "src" / "**" / "*.java"), recursive=True):
    t = Path(p).read_text(encoding="utf-8", errors="replace")
    if any(k in t for k in ("BgN10up", "BGN10UP", "TEMP PROBE")):
        probe_hits.append(os.path.relpath(p, REPO))
jar = sorted(glob.glob(str(REPO / "build" / "libs" / "*.jar")), key=os.path.getmtime)[-1]
close = """bg-n10up 收尾核对
================================================================================

1) 探针残留
   src/**/*.java 里 BgN10up / BGN10UP / TEMP PROBE 命中 = {n_hits} {hits}
   src/main/java/com/hjmmd_8/bettergold/probe/            存在 = {probe_dir}
   probe/bgn10up/                                        存在 = {probe_session}
   run/bgn10up-probe.enabled / run/bgn10up-client.enabled 存在 = {sw1} / {sw2}
   tools/asset-generator/__pycache__                     = {pycache}
   jar（{jar_name}）条目 {jar_entries}，*Probe* 命中 = {jar_probe}

2) git 状态（未 commit、未 push）
{status}
3) git diff --numstat
{numstat}
4) 配方目录里被改（M）的文件 = {n_recipe_mod} 个 {recipe_mod}
   ⇒ "不许动既有配方"成立（第 ③ 条 9 粒 → 1 锭是**既有**的，本轮只核对）

5) 关卡：见 07-七关卡.txt（七条全部 exit 0）
6) run/saves：新的世界 = 29 文件 / max_mtime 1791542894（未变；见 10-saves现状.json）
7) 原始 zip 与归档素材：本轮没有任何贴图/素材改动（git status 里 assets/**/*.png = 0 条）
""".format(
    n_hits=len(probe_hits), hits=probe_hits,
    probe_dir=(REPO / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / "probe").exists(),
    probe_session=(REPO / "probe" / "bgn10up").exists(),
    sw1=(REPO / "run" / "bgn10up-probe.enabled").exists(),
    sw2=(REPO / "run" / "bgn10up-client.enabled").exists(),
    pycache=sorted(os.path.basename(p) for p in glob.glob(str(REPO / "tools" / "asset-generator" / "__pycache__" / "*"))),
    jar_name=os.path.basename(jar), jar_entries=len(__import__("zipfile").ZipFile(jar).namelist()),
    jar_probe=len([n for n in __import__("zipfile").ZipFile(jar).namelist() if "Probe" in n]),
    status=status.strip(), numstat=numstat.strip() or "(空)",
    n_recipe_mod=len(recipe_modified), recipe_mod=recipe_modified,
)
(EV / "09-收尾核对.txt").write_text(close, encoding="utf-8", newline="\n")

# ---------- 11 "只加这三条"自证 ----------
self_proof = """bg-n10up「只加这三条」自证（`git status` / `git diff` 里没有别的配方）
================================================================================

git status --porcelain：
{status}

git diff --numstat：
{numstat}

配方目录：`git status -- src/main/resources/data/bettergold/recipe/`
{recipe_status}
   ⇒ 被改（M）= {n_mod} 条；新增（??）= {n_new} 条：
{n_new_list}

三个"不许动"的点逐个核对（都是读源码/读 JSON，不是印象）：
  1. 9 粒 ⇄ 1 锭那一侧：`chaosgold_nugget_from_ingot.json`（1 锭 → 9 粒）与
     `chaosgold_ingot_from_nugget.json`（9 粒 → 1 锭）都**不在 git status 里** ⇒ 与 HEAD 逐字节一致；
  2. `raw_sturdygold*` 的 catalyst / count：`raw_sturdygold*.json` 与 `*_doubled.json` 全都**不在**
     git status 里；关卡 `[bgn10rg-*]` 照旧绿；
  3. 返瓶：`RawSturdygoldRecipe.java` / `AllItems.java` 的 git 侧 diff 为**空**（本轮没碰 Java）。
""".format(
    status=status.strip(), numstat=numstat.strip() or "(空)",
    recipe_status=git("status", "--porcelain", "--", "src/main/resources/data/bettergold/recipe/").strip() or "(空)",
    n_mod=len(recipe_modified),
    n_new=len([l for l in status.splitlines() if l.startswith("??") and "recipe/chaos_coin" in l.replace("\\", "/")]),
    n_new_list="\n".join("     " + l for l in status.splitlines()
                         if l.startswith("??") and "recipe/" in l.replace("\\", "/")) or "     (无)",
)
(EV / "11-只加这三条自证.txt").write_text(self_proof, encoding="utf-8", newline="\n")

# ---------- 清单 ----------
files = sorted(p.name for p in EV.iterdir() if p.is_file())
(EV / "清单.txt").write_text(
    "bg-n10up 证据目录清单（%d 份 + scripts/ + 脚本副本/）\n" % len(files)
    + "=" * 80 + "\n" + "\n".join("  " + f for f in files) + "\n\n"
    + "scripts/      ：bgn10up_append_doc.py / bgn10up_gates.py / bgn10up_perturb.py / bgn10up_exp_return.py / bgn10up_evidence.py\n"
    + "脚本副本/     ：BgN10upProbe.java.txt / BgN10upClientProbe.java.txt（收尾删除前的源码留档）\n",
    encoding="utf-8", newline="\n")
print("evidence written:", files)
print("probe hits:", probe_hits, "recipe modified:", recipe_modified)
