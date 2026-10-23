import gzip
import hashlib
import json
import sys

sys.stdout.reconfigure(errors="replace")
p = r'src\main\resources\data\bettergold\structure\golden_prison\exit.nbt'
raw = open(p, 'rb').read()
dec = gzip.decompress(raw)
print('file bytes', len(raw), hashlib.sha256(raw).hexdigest())
print('dec bytes', len(dec), hashlib.sha256(dec).hexdigest())
print('count b"room"', dec.count(b'room'))
print('count b"lane"', dec.count(b'lane'))
print('count b"empty"', dec.count(b'empty'))
i = dec.find(b'room')
print('ctx', dec[max(0, i - 60):i + 40])
