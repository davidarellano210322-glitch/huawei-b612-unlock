import os, re

path = "C:/Users/davis/Desktop/herramienta de desbloque/kit_flasheo/B612_11.195.03.00.00_moddedv3.bin"
data = open(path, "rb").read()

outdir = "webui_flat"
os.makedirs(outdir, exist_ok=True)

region = data[0x2d00000:0x4000000]
base = 0x2d00000

headers = []
for m in re.finditer(b"070701", region):
    pos = m.start()
    if pos + 110 > len(region):
        break
    hdr = region[pos:pos+110]
    try:
        def fld(i):
            return int(hdr[6+i*8:14+i*8], 16)
        filesize = fld(6); namesize = fld(11)
    except ValueError:
        continue
    if namesize < 2 or namesize > 300:
        continue
    name = region[pos+110:pos+110+namesize-1].decode("utf-8", "replace")
    if not name or "\x00" in name:
        continue
    if not (name.startswith("html/") or name.startswith("js/") or name.startswith("css/")
            or name.startswith("config/") or name.startswith("img/") or name.startswith("lang/")):
        continue
    headers.append((base+pos, filesize, namesize, name))

seen = {}
manifest = []
for abs_pos, filesize, namesize, name in headers:
    if name in seen:
        continue
    datastart = abs_pos + 110 + namesize
    content = data[datastart:datastart+filesize]
    if len(content) != filesize:
        continue
    seen[name] = content
    idx = len(seen)
    fname = "f%05d" % idx
    with open(os.path.join(outdir, fname), "wb") as f:
        f.write(content)
    manifest.append((fname, name, filesize))

with open(os.path.join(outdir, "MANIFEST.txt"), "w", encoding="utf-8") as mf:
    for fname, name, size in manifest:
        mf.write("%s\t%s\t%d\n" % (fname, name, size))

print("archivos:", len(manifest))
# listar los relacionados a simlock/pin/unlock
for fname, name, size in manifest:
    low = name.lower()
    if "simlock" in low or "/pin/" in low or "verify" in low or "unlock" in low or "nvram" in low or "atcmd" in low:
        print("  *", fname, name, size)
