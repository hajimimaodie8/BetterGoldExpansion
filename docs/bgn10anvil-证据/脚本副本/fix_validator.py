import sys
sys.stdout.reconfigure(errors="replace")

P = r"E:\mc\mcmod\bettergold-template-1.21.1\tools\asset-generator\validate_metal_data.py"
s = open(P, "rb").read().decode("utf-8")
orig = s


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, "anchor count %d != %d for %r" % (n, count, old[:120])
    s = s.replace(old, new)


# 1) variable name typo: definition had a leading underscore (already renamed)

# 2) r8 geometry check: JSON-parsed numeric compare instead of whitespace-sensitive substring
OLD = '''    _m = _r8_model.read_text(encoding="utf-8")
    # 几何必须逐字等于原版 assets/minecraft/models/block/template_anvil.json 的四个 element
    for _seg in ('"from": [ 2, 0, 2 ]', '"to": [ 14, 4, 14 ]',
                 '"from": [ 4, 4, 3 ]', '"to": [ 12, 5, 13 ]',
                 '"from": [ 6, 5, 4 ]', '"to": [ 10, 10, 12 ]',
                 '"from": [ 3, 10, 0 ]', '"to": [ 13, 16, 16 ]'):
        if _seg not in _m:
            _bgn10r8_bad("bgn10r8-assets", "模型几何不是原版 template_anvil 逐字复制（缺 " + _seg + "）")'''
NEW = '''    _m = _r8_model.read_text(encoding="utf-8")
    # 几何必须等于原版 assets/minecraft/models/block/template_anvil.json 的四个 element。
    # ⚠ 旧口径（bg-n10 轮8）原文留档：原来用 substring 找 '"from": [ 2, 0, 2 ]'（依赖手写空格格式）。
    #   bg-n10anvil 轮用 json.dumps 重排了格式 ⇒ 改成解析 JSON 比数值（判定更硬，不是放宽）。
    try:
        _mj = json.loads(_m)
    except Exception:
        _mj = {"elements": []}
    _geom = [(list(_e.get("from", [])), list(_e.get("to", []))) for _e in _mj.get("elements", [])]
    for _f, _t in (([2, 0, 2], [14, 4, 14]), ([4, 4, 3], [12, 5, 13]),
                   ([6, 5, 4], [10, 10, 12]), ([3, 10, 0], [13, 16, 16])):
        if (_f, _t) not in _geom:
            _bgn10r8_bad("bgn10r8-assets", "模型几何不是原版 template_anvil 逐字复制（缺 "
                         + str(_f) + " -> " + str(_t) + "）")'''
rep(OLD, NEW)

assert s != orig
open(P, "wb").write(s.encode("utf-8"))
print("patched", len(s.encode("utf-8")), "B")
