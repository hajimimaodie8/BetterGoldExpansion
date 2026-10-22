# -*- coding: utf-8 -*-
"""第八轮 ⑤：给 validate_metal_data.py 追加 `[bgsnd-*]` 段（金钱妖音效 + 字幕）。

只做两件事（bytes 级）：
  1) 在 `_EXIT_PROBLEM_LISTS = (` 之前插入整段检查代码；
  2) 把 `_bgsnd_problems` 加进那个元组（否则新段不参与 exit code）。
"""
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'tools\asset-generator\validate_metal_data.py'
raw = open(P, 'rb').read()
txt = raw.decode('utf-8')
if '_bgsnd_problems' in txt:
    print('already patched')
    sys.exit(0)

BLOCK = r'''
# ======================================================================================
# 第八轮（2026-10-22）⑤：**金钱妖音效 + 声音字幕**（作者 zip → ogg）
#   作者原话：「补充一下金钱妖的音效（因为人家是浮空的所以不需要什么走路音效，所以之前用的
#   僵尸音效请给它毙掉）」「这些声音发生的时候，如果开了声音字幕，最好在声音字幕那里显示」
#   「E:\mc\mc资料\金钱妖声音.zip 这个地方是金钱妖的声音，还有就是金桥」。
#   本段只查**静态可查**的六件事（A 级探针另外跑，见 docs\金之牢狱-实现记录.md §15）：
#     ① sounds.json 的每个 event 都有非空 subtitle（没有 subtitle ⇒ 开字幕也不显示任何文字）；
#     ② 每个 event 的 sounds[].name 都能对上一个**真实存在且是 OggS** 的 .ogg 文件；
#     ③ AllSounds 注册的 3 个事件名与 sounds.json 的键集**双向相等**；
#     ④ MoneyGremlin 里**僵尸音效全部消失**（去注释后 grep `ZOMBIE_` = 0）+ 三个 get*Sound 都指向 AllSounds；
#     ⑤ 浮空 ⇒ `playStepSound` 覆写成空实现（源码口径：Entity#playStepSound 是 protected，见 AllSounds 注释）；
#     ⑥ zh_cn / en_us 两条字幕键都存在且非空，并且两条语言文件的**键集一致**。
#   「金桥」：zip 里没有名字含 桥/bridge 的文件 ⇒ 本仓不接（作者未给素材，不做猜测）。
# ======================================================================================
_bgsnd_problems: list = []
_bgsnd_checked = 0
_SND_ROOT = Path(__file__).resolve().parent.parent.parent      # 仓库根（tools/asset-generator 往上三层）


def _bgsnd_bad(tag: str, msg: str) -> None:
    _bgsnd_problems.append("[" + tag + "] " + msg)


def _bgsnd_src(rel: str) -> str:
    """读源码并**去掉注释**（正向 needle 必须跑在去注释源码上）。"""
    p = _SND_ROOT / "src" / "main" / "java" / "com" / "hjmmd_8" / "bettergold" / rel
    if not p.exists():
        _bgsnd_bad("bgsnd-src", "缺源码 " + rel)
        return ""
    s = p.read_text(encoding="utf-8")
    out = []
    i, n = 0, len(s)
    while i < n:
        if s.startswith("//", i):
            j = s.find("\n", i)
            i = n if j < 0 else j
            continue
        if s.startswith("/*", i):
            j = s.find("*/", i)
            i = n if j < 0 else j + 2
            continue
        out.append(s[i])
        i += 1
    return "".join(out)


_SND_ASSETS = _SND_ROOT / "src" / "main" / "resources" / "assets" / "bettergold"
_SND_JSON = _SND_ASSETS / "sounds.json"
_SND_EVENTS = ("money_gremlin_ambient", "money_gremlin_hurt", "money_gremlin_death")
_bgsnd_checked += 1
if not _SND_JSON.exists():
    _bgsnd_bad("bgsnd-json", "缺 assets/bettergold/sounds.json")
    _snd_obj = {}
else:
    try:
        _snd_obj = json.loads(_SND_JSON.read_text(encoding="utf-8"))
    except Exception as e:                                  # noqa: BLE001
        _bgsnd_bad("bgsnd-json", "sounds.json 解析失败：" + str(e))
        _snd_obj = {}
if sorted(_snd_obj) != sorted(_SND_EVENTS):
    _bgsnd_bad("bgsnd-json", "sounds.json 的事件集 " + str(sorted(_snd_obj))
               + " != " + str(sorted(_SND_EVENTS)))
_bgsnd_checked += 1
for _ev in _SND_EVENTS:
    _e = _snd_obj.get(_ev) or {}
    _bgsnd_checked += 1
    _sub = _e.get("subtitle")
    if not isinstance(_sub, str) or not _sub.strip():
        _bgsnd_bad("bgsnd-subtitle", _ev + " 缺 subtitle（开声音字幕后什么都不显示）")
    elif _sub != "subtitles.bettergold." + _ev:
        _bgsnd_bad("bgsnd-subtitle", _ev + " 的 subtitle=" + repr(_sub)
                   + " != subtitles.bettergold." + _ev)
    _bgsnd_checked += 1
    _sounds = _e.get("sounds") or []
    if not _sounds:
        _bgsnd_bad("bgsnd-sound", _ev + " 的 sounds 为空")
    for _s in _sounds:
        _bgsnd_checked += 1
        _name = _s.get("name") if isinstance(_s, dict) else None
        if _name != "bettergold:" + _ev:
            _bgsnd_bad("bgsnd-sound", _ev + " 的 sounds[].name=" + repr(_name)
                       + " != bettergold:" + _ev)
            continue
        _ogg = _SND_ASSETS / "sounds" / (_ev + ".ogg")
        _bgsnd_checked += 1
        if not _ogg.exists():
            _bgsnd_bad("bgsnd-ogg", "缺音频文件 " + str(_ogg.relative_to(_SND_ROOT)))
            continue
        _head = _ogg.read_bytes()[:4]
        if _head != b"OggS":
            _bgsnd_bad("bgsnd-ogg", _ev + ".ogg 不是 Ogg 容器（头 " + repr(_head) + "）")
        if _ogg.stat().st_size < 4096:
            _bgsnd_bad("bgsnd-ogg", _ev + ".ogg 只有 " + str(_ogg.stat().st_size) + " B（像是空文件）")

# ③ AllSounds 注册 ↔ sounds.json 键集
_ALLSND = _bgsnd_src("registry/AllSounds.java")
_bgsnd_checked += 1
for _ev in _SND_EVENTS:
    _bgsnd_checked += 1
    if 'register("' + _ev + '")' not in _ALLSND:
        _bgsnd_bad("bgsnd-register", "AllSounds 没有注册 " + _ev)
_bgsnd_checked += 1
if "DeferredRegister.create(Registries.SOUND_EVENT, bettergold.MODID)" not in _ALLSND:
    _bgsnd_bad("bgsnd-register", "AllSounds 的 DeferredRegister 不是 SOUND_EVENT / bettergold 命名空间")
_bgsnd_checked += 1
if "SoundEvent.createVariableRangeEvent" not in _ALLSND:
    _bgsnd_bad("bgsnd-register", "AllSounds 没有用可变范围事件（生物音效必须可变范围）")
_BGMAIN = _bgsnd_src("bettergold.java")
_bgsnd_checked += 1
if "AllSounds.SOUNDS.register(modEventBus)" not in _BGMAIN:
    _bgsnd_bad("bgsnd-register", "bettergold#register 没有挂 AllSounds.SOUNDS")

# ④ 僵尸音效全部毙掉 + 三个 get*Sound 指向新事件
_GREMLIN = _bgsnd_src("entity/MoneyGremlin.java")
_bgsnd_checked += 1
if "ZOMBIE_" in _GREMLIN:
    _bgsnd_bad("bgsnd-zombie", "MoneyGremlin 去注释源码里还有 ZOMBIE_*（僵尸音效没毙掉）")
for _m, _ev in (("getAmbientSound", "MONEY_GREMLIN_AMBIENT"),
                ("getHurtSound", "MONEY_GREMLIN_HURT"),
                ("getDeathSound", "MONEY_GREMLIN_DEATH")):
    _bgsnd_checked += 1
    _i = _GREMLIN.find("protected SoundEvent " + _m)
    if _i < 0:
        _bgsnd_bad("bgsnd-entity", "MoneyGremlin 缺 " + _m)
    elif ("AllSounds." + _ev) not in _GREMLIN[_i:_i + 260]:
        _bgsnd_bad("bgsnd-entity", _m + " 没有返回 AllSounds." + _ev)

# ⑤ 浮空 ⇒ playStepSound 空实现
_bgsnd_checked += 1
_i = _GREMLIN.find("protected void playStepSound")
if _i < 0:
    _bgsnd_bad("bgsnd-step", "MoneyGremlin 没有覆写 playStepSound（浮空却还会踩踏发声）")
else:
    _bgsnd_checked += 1
    if "playSound(" in _GREMLIN[_i:_i + 400]:
        _bgsnd_bad("bgsnd-step", "playStepSound 覆写里还在 playSound（走路音效没去掉）")

# ⑥ 字幕键：中英各一条、非空、键集一致
_snd_lang = {}
for _lc in ("zh_cn", "en_us"):
    _lp = _SND_ASSETS / "lang" / (_lc + ".json")
    _bgsnd_checked += 1
    if not _lp.exists():
        _bgsnd_bad("bgsnd-lang", "缺语言文件 " + _lc + ".json")
        _snd_lang[_lc] = {}
        continue
    _snd_lang[_lc] = json.loads(_lp.read_text(encoding="utf-8"))
_bgsnd_checked += 1
if set(_snd_lang.get("zh_cn", {})) != set(_snd_lang.get("en_us", {})):
    _bgsnd_bad("bgsnd-lang", "zh_cn / en_us 键集不一致：zh 独有 "
               + str(sorted(set(_snd_lang.get("zh_cn", {})) - set(_snd_lang.get("en_us", {})))[:4]))
for _ev in _SND_EVENTS:
    _k = "subtitles.bettergold." + _ev
    for _lc in ("zh_cn", "en_us"):
        _bgsnd_checked += 1
        _v = _snd_lang.get(_lc, {}).get(_k)
        if not isinstance(_v, str) or not _v.strip():
            _bgsnd_bad("bgsnd-lang", _lc + " 缺非空字幕 " + _k)

if _bgsnd_checked < 30:
    _bgsnd_bad("bgsnd-anti-vacuum", "只检查了 " + str(_bgsnd_checked) + " 项（明显过少）")
print("[bgsnd-summary] 金钱妖音效 / 字幕：检查 " + str(_bgsnd_checked)
      + " 项，问题 " + str(len(_bgsnd_problems)) + " 条"
      + ("" if not _bgsnd_problems else "：" + str(_bgsnd_problems[:4])))
if not _bgsnd_problems:
    print("[bgsnd-ok] 3 个 sound event（ambient/hurt/death）都有 subtitle + 真实 OggS 文件；"
          "僵尸音效 0 处残留；playStepSound 空实现；中英字幕键集一致；"
          "「金桥」zip 未提供 ⇒ 未接入")

'''

_anchor = '_EXIT_PROBLEM_LISTS = ('
if _anchor not in txt:
    print('anchor not found')
    sys.exit(1)
txt = txt.replace(_anchor, BLOCK.lstrip('\n') + '\n' + _anchor, 1)
txt = txt.replace('_bgn10err_problems, bgn10fix2_problems)',
                  '_bgn10err_problems, bgn10fix2_problems, _bgsnd_problems)', 1)
if '_bgsnd_problems)' not in txt:
    print('tuple patch failed')
    sys.exit(1)
open(P, 'wb').write(txt.encode('utf-8'))
print('patched', P)
