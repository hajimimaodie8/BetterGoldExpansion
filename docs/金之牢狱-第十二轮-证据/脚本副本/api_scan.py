import zipfile
import re

z = zipfile.ZipFile(r'build\moddev\artifacts\neoforge-21.1.228-sources.jar')
out = []


def grab(name, pat, ctx=600, limit=4):
    try:
        s = z.read(name).decode('utf-8')
    except KeyError:
        out.append('MISSING %s' % name)
        return
    out.append('===== %s' % name)
    for m in list(re.finditer(pat, s))[:limit]:
        out.append(s[max(0, m.start() - 200):m.start() + ctx])


grab('net/minecraft/world/level/levelgen/structure/Structure.java',
     r'public static record StructureSettings|public static class StructureSettings|record Gen', 900, 3)
grab('net/minecraft/world/level/levelgen/structure/Structure.java',
     r'public StructureStart generate\(', 900, 2)
grab('net/minecraft/world/level/levelgen/structure/pools/DimensionPadding.java', r'public record|class', 600, 2)
grab('net/minecraft/world/level/levelgen/structure/structures/JigsawStructure.java',
     r'DEFAULT_LIQUID_SETTINGS|DEFAULT_DIMENSION_PADDING', 300, 4)
grab('net/minecraft/world/level/levelgen/heightproviders/UniformHeight.java', r'public static|class', 400, 3)
open(r'probe\gpr\api_scan.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('ok', len(out))
