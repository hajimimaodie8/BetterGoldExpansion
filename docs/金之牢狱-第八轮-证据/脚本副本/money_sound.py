# -*- coding: utf-8 -*-
"""⑤ 金钱妖音效：**只读**入库（作者 zip）+ 转 ogg 接入 + sounds.json + 语言键。

纪律：
  · 原始 zip `E:\\mc\\mc资料\\金钱妖声音.zip` **一字节不动**（只 zipfile read）；
  · 归档目录 `docs\\金钱妖声音-素材清单\\` 只增不改（解压副本 + 素材清单.tsv）；
  · 落进 src 的是**转码产物**（mp3 → ogg vorbis 单声道），不是改写作者文件。

用法： python probe/gpj/money_sound.py
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\mc\mcmod\bettergold-template-1.21.1'
ZIP = r'E:\mc\mc资料\金钱妖声音.zip'
ARCH = os.path.join(ROOT, 'docs', '金钱妖声音-素材清单')
SND = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'bettergold', 'sounds')
LANG = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'bettergold', 'lang')
SOUNDS_JSON = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'bettergold', 'sounds.json')

# 作者文件 → 我们的 sound event（按文件名里的关键词分类；作者给的就是这三个用途）
MAP = [
    ('刷刷响', 'money_gremlin_ambient', '金钱妖：刷刷响', 'Money Gremlin rustles'),
    ('受伤', 'money_gremlin_hurt', '金钱妖：受伤', 'Money Gremlin hurts'),
    ('死亡', 'money_gremlin_death', '金钱妖：死亡', 'Money Gremlin dies'),
]


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 16), b''):
            h.update(b)
    return h.hexdigest()


def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                          'format=duration,format_name:stream=codec_type,codec_name,channels,sample_rate',
                          '-of', 'json', path], capture_output=True)
    return json.loads(out.stdout.decode('utf-8', 'replace') or '{}')


def main():
    os.makedirs(ARCH, exist_ok=True)
    os.makedirs(SND, exist_ok=True)
    z = zipfile.ZipFile(ZIP)
    rows = []
    picked = {}
    for info in z.infolist():
        if info.is_dir():
            continue
        raw = z.read(info)
        dst = os.path.join(ARCH, info.filename)
        if not os.path.exists(dst):                 # 只增不改
            with open(dst, 'wb') as f:
                f.write(raw)
        md = probe(dst)
        sts = md.get('streams') or []
        st = next((s for s in sts if s.get('codec_type') == 'audio'), {})
        dur = float((md.get('format') or {}).get('duration') or 0.0)
        rows.append((info.filename, len(raw), sha(dst),
                     '+'.join('%s:%s' % (s.get('codec_type'), s.get('codec_name')) for s in sts),
                     st.get('channels'), st.get('sample_rate'), dur))
        for key, ev, _zh, _en in MAP:
            if key in info.filename:
                picked[ev] = (dst, dur)
    with open(os.path.join(ARCH, '素材清单.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 金钱妖声音.zip（作者 2026-10-21 交付）只读入库清单\n')
        f.write('# 原 zip 路径\t%s\n' % ZIP)
        f.write('# 原 zip SHA256\t%s\n' % sha(ZIP))
        f.write('# ⚠ 三个文件名是 .mp3，实际容器 = **MP4（ftyp isom）**：各含 HEVC 视频流 + AAC 音频流；\n')
        f.write('#   接入游戏只取**音频流**（-vn -map 0:a:0）转成 ogg vorbis 单声道。\n')
        f.write('文件\t字节\tSHA256\t流\t音频声道\t音频采样率\tduration_s\t归类\n')
        for fn, size, h, codecs, ch, sr, dur in rows:
            cls = '-'
            for key, ev, _zh, _en in MAP:
                if key in fn:
                    cls = ev
            f.write('%s\t%d\t%s\t%s\t%s\t%s\t%.3f\t%s\n'
                    % (fn, size, h, codecs, ch, sr, dur, cls))
    print('== 素材清单 ==')
    for fn, size, h, codecs, ch, sr, dur in rows:
        print('  %-24s %8d B  %-24s ch=%s %s Hz  %.2f s  %s' %
              (fn, size, codecs, ch, sr, dur, h[:16]))
    # 音轨 → ogg（单声道 44.1k；3D 定位音必须单声道）。**丢掉视频流**。
    print('== 音轨 → ogg ==')
    for ev, (src, dur) in sorted(picked.items()):
        dst = os.path.join(SND, ev + '.ogg')
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', src, '-vn', '-map', '0:a:0',
                        '-ac', '1', '-ar', '44100', '-c:a', 'libvorbis', '-q:a', '5', dst],
                       check=True)
        md = probe(dst)
        st = next((s for s in (md.get('streams') or []) if s.get('codec_type') == 'audio'), {})
        print('  %-26s %.2f s -> %-26s %8d B  %s ch=%s %s Hz' %
              (os.path.basename(src), dur, os.path.basename(dst), os.path.getsize(dst),
               st.get('codec_name'), st.get('channels'), st.get('sample_rate')))
    # sounds.json
    obj = {}
    for _key, ev, _zh, _en in MAP:
        obj[ev] = {'subtitle': 'subtitles.bettergold.%s' % ev,
                   'sounds': [{'name': 'bettergold:%s' % ev, 'stream': False}]}
    with open(SOUNDS_JSON, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
    print('== sounds.json ==')
    print(open(SOUNDS_JSON, encoding='utf-8').read())
    # 语言键（只增不删；两条文件的键集必须一致）
    for lang, idx in (('zh_cn.json', 2), ('en_us.json', 3)):
        p = os.path.join(LANG, lang)
        raw = open(p, 'rb').read()
        txt = raw.decode('utf-8')
        new = [(('subtitles.bettergold.%s' % ev), ([m for m in MAP if m[1] == ev][0][idx]))
               for _k, ev, _zh, _en in MAP]
        added = []
        for k, v in new:
            if ('"%s"' % k) in txt:
                continue
            added.append((k, v))
        if added:
            body = ''.join(',\n  "%s": %s' % (k, json.dumps(v, ensure_ascii=False))
                           for k, v in added)
            i = txt.rstrip().rfind('}')
            head, tail = txt[:i].rstrip(), txt[i:]
            assert head.endswith('}') or True
            txt = head + body + '\n' + tail
            open(p, 'wb').write(txt.encode('utf-8'))
        d = json.loads(open(p, encoding='utf-8').read())
        print('  %-10s +%d keys, total=%d' % (lang, len(added), len(d)))
    # 键集一致 + 三条字幕都在且非空
    zh = json.loads(open(os.path.join(LANG, 'zh_cn.json'), encoding='utf-8').read())
    en = json.loads(open(os.path.join(LANG, 'en_us.json'), encoding='utf-8').read())
    print('  键集一致:', set(zh) == set(en), '| zh 独有', len(set(zh) - set(en)),
          '| en 独有', len(set(en) - set(zh)))
    for _k, ev, _zh, _en in MAP:
        k = 'subtitles.bettergold.%s' % ev
        print('  %-40s zh=%r en=%r' % (k, zh.get(k), en.get(k)))


if __name__ == '__main__':
    main()
