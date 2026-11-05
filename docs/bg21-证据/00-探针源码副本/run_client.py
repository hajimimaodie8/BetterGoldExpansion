#!/usr/bin/env python3
"""bg21 A-level client runner (temporary; whole probe/bg21 is deleted at closeout).

Usage: python probe/bg21/run_client.py before|after

What it does, in order:
  1. snapshot run/saves (author save: name/file count/newest mtime) BEFORE
  2. fresh copy run/world -> run/saves/bg21probe (delete session.lock only in the COPY)
  3. write run/logs/quickplay/bg21.json (id = bg21probe, NEVER the author's world)
  4. patch build.gradle client() with --quickPlayPath / --quickPlaySingleplayer (bytes)
  5. write run/bg21-phase.txt + run/bg21-client-probe.enabled
  6. run gradlew runClient (serial; no server running)
  7. restore build.gradle byte-exact + verify SHA256
  8. print the [bg21-c] lines from run/logs/latest.log
  9. delete the probe world (listing archived to stdout first)
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GAMEDIR = REPO / "run"
SAVES = GAMEDIR / "saves"
PROBE_WORLD = SAVES / "bg21probe"
SOURCE_WORLD = GAMEDIR / "world"
GRADLE = REPO / "gradlew.bat"
BUILD_GRADLE = REPO / "build.gradle"
QP = GAMEDIR / "logs" / "quickplay" / "bg21.json"
PHASE = GAMEDIR / "bg21-phase.txt"
SWITCH = GAMEDIR / "bg21-client-probe.enabled"
LOG = GAMEDIR / "logs" / "latest.log"

ANCHOR = b"        client {\n            client()\n"
INSERT = (b"            programArguments.addAll '--quickPlayPath', 'run/logs/quickplay/bg21.json',"
          b" '--quickPlaySingleplayer', 'bg21probe'\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper() if path.is_file() else "<missing>"


def saves_snapshot():
    out = []
    if SAVES.is_dir():
        for d in sorted(SAVES.iterdir()):
            if not d.is_dir():
                continue
            files = [p for p in d.rglob("*") if p.is_file()]
            newest = max((int(p.stat().st_mtime) for p in files), default=0)
            out.append("%s files=%d newest=%d" % (d.name, len(files), newest))
    return out


def copy_world():
    if PROBE_WORLD.exists():
        shutil.rmtree(PROBE_WORLD, ignore_errors=True)
    shutil.copytree(SOURCE_WORLD, PROBE_WORLD)
    lock = PROBE_WORLD / "session.lock"
    if lock.exists():
        lock.unlink()
        print("[run] removed session.lock from the COPY only: %s" % lock)
    files = [p for p in PROBE_WORLD.rglob("*") if p.is_file()]
    print("[run] probe world copied: %s files=%d" % (PROBE_WORLD, len(files)))


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("before", "after"):
        print("usage: run_client.py before|after")
        return 2
    phase = sys.argv[1]

    before_saves = saves_snapshot()
    print("[run] run/saves BEFORE = %s" % before_saves)
    print("[run] source world exists = %s" % SOURCE_WORLD.is_dir())
    base_sha = sha(BUILD_GRADLE)
    print("[run] build.gradle SHA BEFORE = %s" % base_sha)
    gb_bytes = BUILD_GRADLE.read_bytes()
    print("[run] clientRunProgramArgs.txt SHA = %s (NOT touched)"
          % sha(REPO / "build" / "moddev" / "clientRunProgramArgs.txt"))

    try:
        copy_world()
        QP.parent.mkdir(parents=True, exist_ok=True)
        QP.write_text(json.dumps([{"type": "singleplayer", "id": "bg21probe",
                                   "name": "bg21probe", "gamemode": "creative"}],
                                 ensure_ascii=True), encoding="utf-8")
        print("[run] quickplay json = %s" % QP.read_text(encoding="utf-8"))

        if ANCHOR not in gb_bytes:
            print("[run] ERROR build.gradle anchor not found (CRLF?)")
            return 2
        if gb_bytes.count(ANCHOR) != 1:
            print("[run] ERROR anchor not unique: %d" % gb_bytes.count(ANCHOR))
            return 2
        BUILD_GRADLE.write_bytes(gb_bytes.replace(ANCHOR, ANCHOR + INSERT))
        print("[run] build.gradle SHA PATCHED = %s" % sha(BUILD_GRADLE))

        PHASE.write_text(phase + "\n", encoding="utf-8")
        SWITCH.write_text("bg21\n", encoding="utf-8")
        for f in (LOG,):
            if f.exists():
                pass

        out = REPO / "build" / ("bg21-client-%s.out" % phase)
        err = REPO / "build" / ("bg21-client-%s.err" % phase)
        t0 = time.time()
        with out.open("wb") as fo, err.open("wb") as fe:
            proc = subprocess.run([str(GRADLE), "runClient"], cwd=str(REPO),
                                  stdout=fo, stderr=fe, timeout=1500)
        print("[run] gradlew runClient exit=%d elapsed=%.1fs" % (proc.returncode, time.time() - t0))
    finally:
        BUILD_GRADLE.write_bytes(gb_bytes)
        print("[run] build.gradle SHA RESTORED = %s (baseline=%s, equal=%s)"
              % (sha(BUILD_GRADLE), base_sha, sha(BUILD_GRADLE) == base_sha))

    # probe lines (log4j writes UTF-8)
    if LOG.is_file():
        lines = LOG.read_text(encoding="utf-8", errors="replace").splitlines()
        probe = [ln for ln in lines if "[bg21-c]" in ln]
        print("[run] latest.log lines=%d probe-lines=%d" % (len(lines), len(probe)))
        for ln in probe:
            # keep the message part after the logger name, ASCII only safe
            i = ln.find("[bg21-c]")
            print("LOG " + ln[i:])
    else:
        print("[run] no latest.log")

    after_saves = saves_snapshot()
    print("[run] run/saves AFTER (before probe-world deletion) = %s" % after_saves)

    if PROBE_WORLD.exists():
        files = [p for p in PROBE_WORLD.rglob("*") if p.is_file()]
        print("[run] probe world to delete: files=%d listing=%s"
              % (len(files), sorted(p.name for p in files)[:8]))
        shutil.rmtree(PROBE_WORLD)
        print("[run] probe world deleted")
    print("[run] run/saves AFTER DELETION = %s" % saves_snapshot())
    return 0


if __name__ == "__main__":
    sys.exit(main())
