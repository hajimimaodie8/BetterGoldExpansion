"""bg-n10 轮2/轮3 探针跑测的文件级准备与复原（临时脚本，收尾删）。

用法：
    py -3 bgn10v_run_prep.py save      # 备份 server.properties + 记录 run/saves 清单
    py -3 bgn10v_run_prep.py set <world-name>
    py -3 bgn10v_run_prep.py restore
全部走 bytes，避免中文/编码被 PowerShell 文本管道毁掉。
"""
import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(r"E:\mc\mcmod\bettergold-template-1.21.1")
RUN = ROOT / "run"
PROPS = RUN / "server.properties"
BAK = RUN / "server.properties.bgn10v.bak"
ENABLE = RUN / "bgn10v-probe.enabled"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def cmd_save() -> None:
    if BAK.exists():
        raise SystemExit(f"拒绝覆盖已存在的备份：{BAK}")
    shutil.copyfile(PROPS, BAK)
    print(f"server.properties sha256(before) = {sha(PROPS)}")
    print(f"backup sha256                    = {sha(BAK)}")
    saves = RUN / "saves"
    lines = []
    for d in sorted(saves.iterdir()):
        files = [f for f in d.rglob("*") if f.is_file()]
        total = sum(f.stat().st_size for f in files)
        lines.append(f"{d.name}\tfiles={len(files)}\tbytes={total}")
    (ROOT / "build" / "bgn10v-saves-before.txt").write_bytes(
        ("\n".join(lines) + "\n").encode("utf-8"))
    print("\n".join(lines))
    # 世界目录清单
    for d in sorted(RUN.iterdir()):
        if d.is_dir() and (d / "level.dat").exists():
            print(f"world-dir: {d.name} level.dat={ (d/'level.dat').stat().st_size }")


def cmd_set(name: str) -> None:
    data = BAK.read_bytes()
    old = b"level-name=world"
    new = ("level-name=" + name).encode("ascii")
    if data.count(old) != 1:
        raise SystemExit(f"锚点不唯一：level-name=world 出现 {data.count(old)} 次")
    PROPS.write_bytes(data.replace(old, new))
    print(f"set level-name={name}; sha256(now)={sha(PROPS)}")


def cmd_restore() -> None:
    shutil.copyfile(BAK, PROPS)
    ok = sha(PROPS) == sha(BAK)
    print(f"restored server.properties; sha256={sha(PROPS)} backup={sha(BAK)} match={ok}")
    if not ok:
        raise SystemExit(2)


def cmd_enable() -> None:
    ENABLE.write_bytes(b"")
    print(f"switch file: {ENABLE} exists={ENABLE.exists()}")


def cmd_disable() -> None:
    if ENABLE.exists():
        ENABLE.unlink()
    print(f"switch file: {ENABLE} exists={ENABLE.exists()}")


if __name__ == "__main__":
    action = sys.argv[1]
    if action == "save":
        cmd_save()
    elif action == "set":
        cmd_set(sys.argv[2])
    elif action == "restore":
        cmd_restore()
    elif action == "enable":
        cmd_enable()
    elif action == "disable":
        cmd_disable()
    else:
        raise SystemExit(f"unknown action {action}")
