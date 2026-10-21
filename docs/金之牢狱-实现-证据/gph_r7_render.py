# -*- coding: utf-8 -*-
"""第七轮预览渲染：① 整体俯视 ② 分层俯视 ③ 连通示意 ④ 剖面（空腔修前/修后同视角）。
另加 ⑤ 空腔三层平面（地板 / 净空 / 天花板），给作者一眼看清"洞厅 + 井口"。

数据源：
  --dir   探针 dump（meta.json + blocks_<i>.tsv）
  --piece 取第几座（默认按件数最多的一座）
  修前的 exit.nbt 从 git HEAD 读（build/exit_before.nbt，由外部脚本落盘）

用法：
  python gph_r7_render.py --dir docs\\金之牢狱-实现-证据\\gph_r7a --out docs\\金之牢狱-生成预览\\第六轮
"""
import argparse
import json
import math
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'docs', '金之牢狱-实现-证据'))
import nbt  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

BASE = (18, 18, 22)
FG = (238, 232, 210)
DIM = (150, 150, 162)
TICK = (90, 90, 100)
ACC = (120, 200, 255)

COLORS = {
    'minecraft:air': (24, 24, 28),
    'bettergold:gold_bricks': (196, 154, 44),
    'bettergold:gold_pillar': (152, 112, 24),
    'bettergold:gold_bricks_stairs': (168, 130, 32),
    'bettergold:gold_bricks_wall': (140, 104, 20),
    'bettergold:gold_bricks_slab': (176, 138, 36),
    'bettergold:gold_bars': (226, 190, 90),
    'bettergold:gold_chain': (236, 206, 120),
    'bettergold:gold_trapdoor': (206, 166, 60),
    'bettergold:gold_infused_dirt': (110, 78, 34),
    'bettergold:gold_infused_farmland': (86, 58, 24),
    'bettergold:golden_wheat_crop': (214, 196, 84),
    'bettergold:golden_carrot_crop': (232, 148, 40),
    'bettergold:golden_eggplant_crop': (140, 70, 150),
    'bettergold:golden_rose_bush': (200, 92, 92),
    'bettergold:golden_toad_figurine': (246, 214, 60),
    'minecraft:gold_block': (246, 208, 52),
    'minecraft:raw_gold_block': (198, 164, 62),
    'minecraft:nether_gold_ore': (166, 66, 44),
    'minecraft:ancient_debris': (92, 66, 62),
    'minecraft:chest': (150, 106, 52),
    'minecraft:spawner': (58, 76, 96),
    'minecraft:yellow_stained_glass': (232, 232, 120),
    'minecraft:jigsaw': (240, 60, 200),
    'minecraft:gold_bars': (226, 190, 90),
}
NATURAL = {
    'minecraft:basalt': (70, 70, 78), 'minecraft:blackstone': (46, 44, 52),
    'minecraft:magma_block': (180, 80, 40), 'minecraft:netherrack': (110, 58, 58),
    'minecraft:soul_sand': (92, 70, 58), 'minecraft:soul_soil': (78, 60, 50),
    'minecraft:gravel': (120, 112, 108), 'minecraft:glowstone': (240, 210, 120),
    'minecraft:lava': (250, 120, 20), 'minecraft:bedrock': (40, 40, 46),
    'minecraft:crimson_nylium': (140, 40, 60), 'minecraft:warped_nylium': (40, 110, 100),
    'minecraft:nether_wart_block': (130, 30, 40), 'minecraft:crimson_stem': (90, 40, 50),
    'minecraft:brown_mushroom': (150, 120, 90), 'minecraft:red_mushroom': (200, 60, 60),
}
UNKNOWN = (255, 0, 80)
FONT = r'C:\Windows\Fonts\msyh.ttc'


def font(sz):
    try:
        return ImageFont.truetype(FONT, sz)
    except Exception:
        return ImageFont.load_default()


def col(nm):
    return COLORS.get(nm) or NATURAL.get(nm) or UNKNOWN


def load_blocks(path):
    """(x,y,z) -> name"""
    out = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            a = line.rstrip('\n').split(',')
            if len(a) < 4:
                continue
            out[(int(a[0]), int(a[1]), int(a[2]))] = a[3]
    return out


def ticks(d, x0, z0, ox, oy, s, nx, nz, step=16):
    """坐标刻度：每 step 格一条淡线 + 绝对世界坐标标签。"""
    for i in range(0, nx + 1, step):
        px = ox + i * s
        d.line([px, oy, px, oy + nz * s], fill=TICK)
        d.text((px + 1, oy - 13), str(x0 + i), font=font(9), fill=DIM)
    for j in range(0, nz + 1, step):
        py = oy + j * s
        d.line([ox, py, ox + nx * s, py], fill=TICK)
        d.text((ox - 30, py - 5), str(z0 + j), font=font(9), fill=DIM)


def compass(d, x, y):
    d.polygon([(x, y - 14), (x - 5, y), (x + 5, y)], fill=ACC)
    d.text((x - 4, y + 2), 'N', font=font(11), fill=ACC)
    d.text((x - 4, y + 18), 'S', font=font(11), fill=DIM)
    d.text((x - 22, y + 2), 'W', font=font(11), fill=DIM)
    d.text((x + 12, y + 2), 'E', font=font(11), fill=DIM)


def legend(d, x, y, items, title='图例'):
    d.text((x, y), title, font=font(12), fill=FG)
    yy = y + 18
    for nm, c, cnt in items:
        d.rectangle([x, yy, x + 10, yy + 10], fill=c, outline=(60, 60, 70))
        d.text((x + 16, yy - 2), '%-30s %d' % (nm, cnt), font=font(10), fill=DIM)
        yy += 15
    return yy


def render_overall(meta, blocks, path):
    ps = meta['pieces']
    xs = [p['bbox'][0] for p in ps] + [p['bbox'][3] for p in ps]
    zs = [p['bbox'][2] for p in ps] + [p['bbox'][5] for p in ps]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    S = 4
    nx, nz = x1 - x0 + 1, z1 - z0 + 1
    PAD_L, PAD_T, PAD_R, PAD_B = 62, 74, 250, 54
    w, h = PAD_L + nx * S + PAD_R, PAD_T + nz * S + PAD_B
    img = Image.new('RGB', (w, h), BASE)
    d = ImageDraw.Draw(img)
    d.text((10, 8), '金之牢狱 · 整体俯视（金结构的最高方块；自然地形压暗）', font=font(20), fill=FG)
    d.text((10, 38), 'seed %s · %s · %s · %d 件 · 每格 %dpx · 世界坐标刻度 · 金块大方块 = 出入口空腔的天花板'
           % (meta.get('seed', '?'), meta.get('biome'), meta.get('structure'), len(ps), S),
           font=font(11), fill=DIM)
    # 每列取「金结构的最高方块」（自然地形只当暗底，否则地下地牢看不见）
    top, nat = {}, {}
    for (x, y, z), nm in blocks.items():
        k = (x, z)
        if k not in nat or y > nat[k][0]:
            nat[k] = (y, nm)
        if nm.startswith('bettergold:') or nm in COLORS:
            if k not in top or y > top[k][0]:
                top[k] = (y, nm)
    cnt = {}
    for i in range(nx):
        for j in range(nz):
            v = top.get((x0 + i, z0 + j))
            c = (10, 10, 12)
            if not v and (x0 + i, z0 + j) in nat:
                r, g, b = NATURAL.get(nat[(x0 + i, z0 + j)][1], (70, 62, 66))
                c = (r // 3 + 12, g // 3 + 10, b // 3 + 10)
            if v:
                if v[1] in NATURAL or v[1].startswith('minecraft:') and v[1] not in COLORS:
                    r, g, b = NATURAL.get(v[1], (70, 62, 66))
                    c = (r // 3 + 12, g // 3 + 10, b // 3 + 10)      # 自然地形压暗
                else:
                    c = col(v[1])
                    cnt[v[1]] = cnt.get(v[1], 0) + 1
            px, py = PAD_L + i * S, PAD_T + j * S
            d.rectangle([px, py, px + S - 1, py + S - 1], fill=c)
    ticks(d, x0, z0, PAD_L, PAD_T, S, nx, nz, 16)
    # 件轮廓 + 编号
    for p in ps:
        b = p['bbox']
        px0, py0 = PAD_L + (b[0] - x0) * S, PAD_T + (b[2] - z0) * S
        px1, py1 = PAD_L + (b[3] - x0) * S + S, PAD_T + (b[5] - z0) * S + S
        d.rectangle([px0, py0, px1, py1], outline=(255, 255, 255))
        d.text((px0 + 2, py0 + 1), str(p['i']), font=font(10), fill=(255, 255, 255))
    compass(d, PAD_L + nx * S // 2, PAD_T + nz * S + 20)
    items = [(nm, col(nm), c) for nm, c in sorted(cnt.items(), key=lambda kv: -kv[1])[:10]]
    legend(d, w - PAD_R + 12, PAD_T, items, '图例（金结构方块计数）')
    d.text((w - PAD_R + 12, PAD_T + 18 + 15 * len(items) + 8),
           '金块大方块 = 出入口空腔的天花板', font=font(10), fill=DIM)
    img.save(path)
    return path


def render_layers(meta, blocks, path):
    ps = meta['pieces']
    xs = [p['bbox'][0] for p in ps] + [p['bbox'][3] for p in ps]
    zs = [p['bbox'][2] for p in ps] + [p['bbox'][5] for p in ps]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    ex = (meta.get('exits') or [{}])[0]
    rim = ex.get('topY')
    ymin = min(p['bbox'][1] for p in ps)
    layers = [ymin + 2, ymin + 5]
    if rim is not None:
        layers += [rim - 3, rim, rim + 4, rim + 9, rim + 14, rim + 17]
    else:
        layers += [ymin + 10, ymin + 14, ymin + 18, ymin + 22, ymin + 26, ymin + 30]
    S = 4
    nx, nz = x1 - x0 + 1, z1 - z0 + 1
    PW, PH = nx * S + 44, nz * S + 40
    cols = 4
    rows = (len(layers) + cols - 1) // cols
    PAD = 14
    w = PAD + cols * (PW + PAD)
    h = 76 + rows * (PH + PAD + 18)
    img = Image.new('RGB', (w, h), BASE)
    d = ImageDraw.Draw(img)
    d.text((10, 8), '金之牢狱 · 分层俯视（第 2 层起是出入口空腔的剖面层）', font=font(20), fill=FG)
    d.text((10, 40), 'seed %s · %s · 每格 %dpx · 天空色块 = 该层方块；空白 = 空气'
           % (meta.get('seed', '?'), meta.get('biome'), S), font=font(11), fill=DIM)
    for k, ly in enumerate(layers):
        cx = PAD + (k % cols) * (PW + PAD)
        cy = 76 + (k // cols) * (PH + PAD + 18)
        d.text((cx, cy), 'y = %d%s' % (ly, '（井口环顶）' if rim is not None and ly == rim else ''),
               font=font(11), fill=FG)
        d.rectangle([cx + 30, cy + 16, cx + 30 + nx * S, cy + 16 + nz * S], outline=(50, 50, 58))
        for i in range(nx):
            for j in range(nz):
                nm = blocks.get((x0 + i, ly, z0 + j))
                if nm is None or nm == 'minecraft:air':
                    continue
                px, py = cx + 30 + i * S, cy + 16 + j * S
                d.rectangle([px, py, px + S - 1, py + S - 1], fill=col(nm))
        ticks(d, x0, z0, cx + 30, cy + 16, S, nx, nz, 32)
        d.text((cx + 30, cy + 16 + nz * S + 4), 'x→ %d..%d  z↓ %d..%d' % (x0, x1, z0, z1),
               font=font(9), fill=DIM)
    img.save(path)
    return path


def render_connect(meta, path):
    ps = meta['pieces']
    xs = [p['bbox'][0] for p in ps] + [p['bbox'][3] for p in ps]
    zs = [p['bbox'][2] for p in ps] + [p['bbox'][5] for p in ps]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    S = max(4, min(9, int(900 / max(1, max(x1 - x0, z1 - z0)))))
    nx, nz = x1 - x0 + 1, z1 - z0 + 1
    PAD_L, PAD_T, PAD_R, PAD_B = 62, 78, 240, 60
    w, h = PAD_L + nx * S + PAD_R, PAD_T + nz * S + PAD_B
    img = Image.new('RGB', (w, h), BASE)
    d = ImageDraw.Draw(img)
    d.text((10, 8), '金之牢狱 · 连通示意（件 = 盒，颜色 = 连接图深度）', font=font(20), fill=FG)
    d.text((10, 40), 'seed %s · %s · %d 件 / 口 %s / 配对 %s / 落单口 %d'
           % (meta.get('seed', '?'), meta.get('biome'), len(ps), meta.get('ports'),
              meta.get('paired'), len(meta.get('orphans') or [])), font=font(11), fill=DIM)
    ticks(d, x0, z0, PAD_L, PAD_T, S, nx, nz, 16)
    depths = meta.get('depths') or [p['i'] for p in ps]
    dmax = max(depths) if depths else 1
    def dcol(k):
        t = k / max(1, dmax)
        return (int(80 + 170 * t), int(200 - 120 * t), int(120 + 60 * (1 - t)))
    # 相邻件的边（bbox 贴合 = 有接线；落单口另标红）
    for a in ps:
        for b in ps:
            if b['i'] <= a['i']:
                continue
            A, B = a['bbox'], b['bbox']
            gapx = max(A[0] - B[3], B[0] - A[3])
            gapz = max(A[2] - B[5], B[2] - A[5])
            oy = min(A[4], B[4]) - max(A[1], B[1])
            ox = min(A[3], B[3]) - max(A[0], B[0])
            oz = min(A[5], B[5]) - max(A[2], B[2])
            if (gapx <= 1 and ox > 0 and oz > 0 and oy > 0) or (gapz <= 1 and oz > 0 and ox > 0 and oy > 0):
                ca = ((A[0] + A[3]) // 2, (A[2] + A[5]) // 2)
                cb = ((B[0] + B[3]) // 2, (B[2] + B[5]) // 2)
                d.line([PAD_L + (ca[0] - x0) * S, PAD_T + (ca[1] - z0) * S,
                        PAD_L + (cb[0] - x0) * S, PAD_T + (cb[1] - z0) * S], fill=(90, 110, 130), width=2)
    for p in ps:
        b = p['bbox']
        k = depths[p['i']] if p['i'] < len(depths) else 0
        px0, py0 = PAD_L + (b[0] - x0) * S, PAD_T + (b[2] - z0) * S
        px1, py1 = PAD_L + (b[3] - x0) * S + S, PAD_T + (b[5] - z0) * S + S
        d.rectangle([px0, py0, px1, py1], fill=None, outline=dcol(k), width=2)
        d.text((px0 + 2, py0 + 1), '%d %s' % (p['i'], p['tpl'][:10]), font=font(9),
               fill=(255, 255, 255))
    for o in (meta.get('orphans') or []):
        px = PAD_L + (o['pos'][0] - x0) * S
        py = PAD_T + (o['pos'][2] - z0) * S
        d.ellipse([px - 5, py - 5, px + 5, py + 5], fill=(255, 60, 60))
        d.text((px + 7, py - 6), '落单口 #%d' % o['piece'], font=font(10), fill=(255, 90, 90))
    compass(d, PAD_L + nx * S // 2, PAD_T + nz * S + 22)
    items = [('深度 0（宝藏房）', dcol(0), ''), ('深度 %d（最远）' % dmax, dcol(dmax), ''),
             ('落单口', (255, 60, 60), '')]
    yy = PAD_T
    d.text((w - PAD_R + 12, yy), '图例', font=font(12), fill=FG)
    for nm, c, _ in items:
        d.rectangle([w - PAD_R + 12, yy + 18, w - PAD_R + 26, yy + 32], fill=c)
        d.text((w - PAD_R + 32, yy + 16), nm, font=font(10), fill=DIM)
        yy += 26
    d.text((w - PAD_R + 12, yy + 8), '白框 = 件（bbox 水平投影）', font=font(10), fill=DIM)
    d.text((w - PAD_R + 12, yy + 24), '灰线 = 两件 bbox 贴合（接线）', font=font(10), fill=DIM)
    img.save(path)
    return path


def read_nbt_piece(path):
    _, root = nbt.parse_auto(open(path, 'rb').read())
    pal = root['palette']
    g = {}
    for b in root['blocks']:
        x, y, z = b['pos']
        nm = pal[b['state']]['Name']
        if nm != 'minecraft:air':
            g[(x, y, z)] = nm
    return tuple(root['size']), g


def section(g, x0, x1, y0, y1, z, S):
    w, h = (x1 - x0 + 1) * S, (y1 - y0 + 1) * S
    img = Image.new('RGB', (w, h), BASE)
    d = ImageDraw.Draw(img)
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            nm = g.get((x, y, z))
            px, py = (x - x0) * S, (y1 - y) * S
            d.rectangle([px, py, px + S - 1, py + S - 1],
                        fill=col(nm) if nm else (26, 26, 30), outline=(34, 34, 40))
    return img, d


def render_section(path_new, path_before, path):
    """修前 / 修后 **同一条 y 轴、同一比例** 的剖面（z=2，穿过井筒与空腔）。"""
    size_n, gn = read_nbt_piece(path_new)
    size_o, go = read_nbt_piece(path_before)
    S = 8
    zc = 2
    rim = 43
    ymax = max(size_n[1], size_o[1]) - 1
    gap = 60
    left_w = size_o[0] * S
    right_w = size_n[0] * S
    PAD_L, PAD_T = 78, 104
    W = PAD_L + left_w + gap + right_w + 340
    H = PAD_T + (ymax + 1) * S + 110
    img = Image.new('RGB', (W, H), BASE)
    d = ImageDraw.Draw(img)
    d.text((10, 8), '金之牢狱 · 出入口剖面（z=%d，修前/修后同一 y 轴）' % zc, font=font(20), fill=FG)
    d.text((10, 40), '左 = 修前 5x44x5（%d 格）；右 = 修后 11x62x11（%d 格）—— 同一 y 轴、同一比例'
           % (len(go), len(gn)), font=font(11), fill=DIM)

    def draw_panel(g, size, ox):
        for x in range(size[0]):
            for y in range(size[1]):
                nm = g.get((x, y, zc))
                px = ox + x * S
                py = PAD_T + (ymax - y) * S
                d.rectangle([px, py, px + S - 1, py + S - 1],
                            fill=col(nm) if nm else (26, 26, 30), outline=(34, 34, 40))

    draw_panel(go, size_o, PAD_L)
    draw_panel(gn, size_n, PAD_L + left_w + gap)
    oy = PAD_T + (ymax - rim) * S
    # 修前：环顶以上到件顶 = 下界天花板岩体（A 级读数，不是模板内容）
    for k in range(rim + 1, ymax + 1):
        yy = PAD_T + (ymax - k) * S
        d.line([PAD_L, yy + S // 2, PAD_L + left_w - 1, yy + S // 2], fill=(78, 46, 46))
    d.text((PAD_L + left_w + gap + right_w + 10, PAD_T + 176),
           '修前：环顶以上\n是下界天花板岩体\n（实测 86..122 实心）', font=font(10), fill=(235, 140, 140))
    # 环顶线（两个面板共用）
    d.line([PAD_L - 10, oy, PAD_L + left_w + gap + right_w + 10, oy], fill=(255, 90, 90), width=2)
    d.text((PAD_L - 70, oy - 6), '环顶 y=%d' % rim, font=font(11), fill=(255, 120, 120))
    ox2 = PAD_L + left_w + gap
    for (y, txt) in ((61, '天花板 y=61（封闭）'), (39, '地板 y=39'), (50, '净空 9x9 / 21 层（y 40..60）')):
        yy = PAD_T + (ymax - y) * S
        d.text((ox2 + right_w + 10, yy - 6), txt, font=font(10), fill=(120, 255, 180))
    d.text((PAD_L, PAD_T - 24), '修前（左）', font=font(13), fill=(255, 200, 120))
    d.text((ox2, PAD_T - 24), '修后（右）', font=font(13), fill=(120, 255, 180))
    for y in range(0, ymax + 1, 8):
        yy = PAD_T + (ymax - y) * S
        d.text((PAD_L - 44, yy - 5), str(y), font=font(9), fill=DIM)
        d.line([PAD_L - 8, yy, PAD_L - 3, yy], fill=TICK)
    d.text((10, H - 50), '红 = 井口环顶；绿标 = 空腔；每格 %dpx；y 刻度 = 件内坐标（x 右、y 上）' % S,
           font=font(10), fill=DIM)
    d.text((10, H - 32),
           '对比要点：修前井口上方没有空腔（真生成里是岩体，airFromY 比环顶高 9~17 格）；'
           '修后井口在 9x9x21 的封闭洞厅里（环顶上下都是空腔空气）', font=font(10), fill=(205, 205, 215))
    img.save(path)
    return path


def render_cavity_plan(path_pieces, path, tag='exit'):
    data = json.load(open(path_pieces, encoding='utf-8'))
    p = data['pieces'][tag] if 'pieces' in data else data[tag]
    g = {}
    for k, v in p['blocks'].items():
        x, y, z = [int(t) for t in k.split(',')]
        if v[0] != 'minecraft:air':
            g[(x, y, z)] = v[0]
    S = 14
    layers = [(39, '地板 y=39（3x3 井口留空）'), (44, '净空 y=44（井口在 NW 角，井沿 4 层）'),
              (61, '天花板 y=61（封闭）')]
    W = max(26 + 11 * S + 40, 520)
    H = 80 + len(layers) * (11 * S + 52)
    img = Image.new('RGB', (W, H), BASE)
    d = ImageDraw.Draw(img)
    d.text((10, 8), '金之牢狱 · 井口空腔（exit 模板三层平面，每格 %dpx）' % S, font=font(20), fill=FG)
    d.text((10, 40), '11x11 外壳 / 9x9 净空 / 地板 39 / 天花板 61 / 井口环顶 y=43；只填空格，门楼与井筒原样',
           font=font(11), fill=DIM)
    for i, (y, cap) in enumerate(layers):
        ox, oy = 30, 76 + i * (11 * S + 52)
        d.text((ox, oy), cap + '  （N 上 / E 右）', font=font(12), fill=FG)
        for x in range(11):
            for z in range(11):
                nm = g.get((x, y, z))
                px, py = ox + 26 + x * S, oy + 18 + z * S
                d.rectangle([px, py, px + S - 1, py + S - 1],
                            fill=col(nm) if nm else (24, 24, 28), outline=(40, 40, 46))
                if nm is None and x in (1, 2, 3) and z in (1, 2, 3):
                    d.rectangle([px, py, px + S - 1, py + S - 1], outline=(120, 200, 255))
        d.text((ox + 26, oy + 18 + 11 * S + 4), 'x 0..10 / z 0..10；蓝框 = 3x3 井筒通道',
               font=font(9), fill=DIM)
    img.save(path)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--idx', type=int, default=-1)
    ap.add_argument('--pieces', default='docs/金之牢狱-实现-证据/pieces_stage2.json')
    ap.add_argument('--before', default='build/exit_before.nbt')
    ap.add_argument('--new', default='src/main/resources/data/bettergold/structure/golden_prison/exit.nbt')
    a = ap.parse_args()
    d = a.dir if os.path.isabs(a.dir) else os.path.join(ROOT, a.dir)
    out = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out)
    os.makedirs(out, exist_ok=True)
    metas = json.load(open(os.path.join(d, 'meta.json'), encoding='utf-8'))
    idx = a.idx if a.idx >= 0 else max(range(len(metas)), key=lambda i: len(metas[i]['pieces']))
    meta = dict(metas[idx])
    seed = ''
    sp = os.path.join(d, 'seeds.json')
    if os.path.exists(sp):
        seed = json.load(open(sp, encoding='utf-8')).get('seed')
    meta['seed'] = seed
    blocks = load_blocks(os.path.join(d, 'blocks_%d.tsv' % idx))
    print('render: #%d %s %s pieces=%d blocks=%d' % (idx, meta['biome'], meta['structure'],
                                                     len(meta['pieces']), len(blocks)))
    for fn in [
        lambda: render_overall(meta, blocks, os.path.join(out, '01_整体俯视.png')),
        lambda: render_layers(meta, blocks, os.path.join(out, '02_分层俯视.png')),
        lambda: render_connect(meta, os.path.join(out, '03_连通示意.png')),
        lambda: render_section(os.path.join(ROOT, a.new), os.path.join(ROOT, a.before),
                               os.path.join(out, '04_剖面-空腔修前修后.png')),
        lambda: render_cavity_plan(os.path.join(ROOT, a.pieces),
                                   os.path.join(out, '05_空腔三层平面.png')),
    ]:
        try:
            print('  ->', fn())
        except Exception as e:
            print('  NG %s' % e)
    return 0


if __name__ == '__main__':
    sys.exit(main())
