# -*- coding: utf-8 -*-
"""修前 / 修后同视角并排图（阶段 B）。

把 `修前\\` 与 `修后\\` 里同名 PNG 左右拼起来，顶部一条标题带写明两张图各自的世界 / 种子 /
结构坐标 / 读数，底部一条图例说明「左 = 修前 NBT，右 = 修后 NBT」。

用法：
  py -3 docs\\金之牢狱-生成预览-证据\\gp_compare.py
输出（docs\\金之牢狱-生成预览\\对比\\）：
  00-对比-整体俯视图.png / 03-对比-分层俯视-y41.png / 07-对比-连通示意图.png / 08-对比-剖面A.png
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]
PREV = ROOT / 'docs' / '金之牢狱-生成预览'
OUT = PREV / '对比'
FONT = r'C:\Windows\Fonts\msyh.ttc'
FONT_B = r'C:\Windows\Fonts\msyhbd.ttc'

PAIRS = [
    ('00-整体俯视图.png', '00-对比-整体俯视图.png', '整体俯视（全部件投影 + 件框 + 箱/笼/蟾）'),
    ('03-分层俯视-y41.png', '03-对比-分层俯视-y41.png', '分层俯视 y=41（行走面：门洞 / 走廊 / 四面道）'),
    ('07-连通示意图.png', '07-对比-连通示意图.png', '连通示意（件框 + 父口→子口箭头 + 宝藏房/出入口）'),
    ('08-剖面A-x600.png', '08-对比-剖面A.png', '剖面 x=600（层高 / 门洞 / 屋顶 / 埋深）'),
]
HEAD = 108
FOOT = 42
GAP = 16


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def main():
    before, after = PREV / '修前', PREV / '修后'
    if not before.is_dir() or not after.is_dir():
        print('缺 修前/ 或 修后/ 目录')
        return 2
    tag = {}
    for k, f in (('before', 'gp_world_check_before.json'), ('after', 'gp_world_check.json')):
        p = ROOT / 'docs' / '金之牢狱-生成预览-证据' / f
        if p.exists():
            tag[k] = json.loads(p.read_text(encoding='utf-8'))
    label = {}
    for side in ('before', 'after'):
        d = tag.get(side) or {}
        label[side] = ('世界 %s / 种子 %s / 结构 %s · 件内空气 %s%% · 行走层 %s%%'
                       % (d.get('world', '?'), d.get('seed', '?'), d.get('structurePos', '?'),
                          (d.get('airInside') or {}).get('airPct', '?'),
                          (d.get('airInside') or {}).get('walkAirPct', '?')))
    OUT.mkdir(parents=True, exist_ok=True)
    for src, dst, title in PAIRS:
        a, b = before / src, after / src
        if not a.exists() or not b.exists():
            print('跳过（缺图）%s' % src)
            continue
        ia, ib = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
        h = max(ia.height, ib.height)
        W = ia.width + ib.width + GAP * 3
        canvas = Image.new('RGB', (W, h + HEAD + FOOT), (255, 255, 255))
        d = ImageDraw.Draw(canvas)
        d.rectangle([0, 0, W, HEAD], fill=(28, 30, 36))
        d.text((GAP, 8), '金之牢狱 · 修前 vs 修后 同视角对比 —— ' + title,
               font=font(17, True), fill=(250, 250, 250))
        d.text((GAP, 36), '左：修前（HEAD 782c1f3 的旧 NBT，模板不含空气）  |  '
                          '右：修后（模板写满空气）  |  同种子 / 同一座结构',
               font=font(12), fill=(200, 206, 214))
        d.text((GAP, 56), '修前 ' + label['before'], font=font(11), fill=(240, 200, 120))
        d.text((GAP, 74), '修后 ' + label['after'], font=font(11), fill=(150, 220, 150))
        d.text((GAP, 92), '每图自带标题 / 图例 / 罗盘 / 每 8 格坐标刻度；左右两图同尺寸同原点，'
                          '可直接逐格对照。', font=font(11), fill=(150, 156, 166))
        x0 = GAP
        canvas.paste(ia, (x0, HEAD))
        x1 = GAP * 2 + ia.width
        canvas.paste(ib, (x1, HEAD))
        d.line([(x0 + ia.width + GAP // 2, HEAD), (x0 + ia.width + GAP // 2, HEAD + h)],
               fill=(180, 180, 186), width=2)
        for x, t in ((x0, '修前'), (x1, '修后')):
            d.rectangle([x, HEAD + h + 6, x + 46, HEAD + h + 26], outline=(120, 120, 128))
            d.text((x + 6, HEAD + h + 8), t, font=font(13, True), fill=(30, 30, 34))
            d.text((x + 56, HEAD + h + 8), '同视角 · 同坐标 · 每格 5~6 px',
                   font=font(12), fill=(90, 90, 98))
        canvas.save(OUT / dst, 'PNG')
        print('[png]', dst, canvas.size)
    return 0


if __name__ == '__main__':
    sys.exit(main())
