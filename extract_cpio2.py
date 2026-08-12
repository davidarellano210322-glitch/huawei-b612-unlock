import os, re

path = "C:/Users/davis/Desktop/herramienta de desbloque/kit_flasheo/B612_11.195.03.00.00_moddedv3.bin"
data = open(path, "rb").read()

outdir = "webui_full"
os.makedirs(outdir, exist_ok=True)

entries = []   # (abs_pos, filesize, namesize, name)
seen_pos = set()

for m in re.finditer(b"070701", data):
    pos = m.start()
    if pos in seen_pos or pos + 110 > len(data):
        continue
    hdr = data[pos:pos+110]
    try:
        def fld(i):
            return int(hdr[6+i*8:14+i*8], 16)
        filesize = fld(6); namesize = fld(11)
    except ValueError:
        continue
    if namesize < 2 or namesize > 400 or filesize > 0x2000000:
        continue
    name = data[pos+110:pos+110+namesize-1].decode("utf-8", "replace")
    if not name or "\x00" in name or name == "TRAILER!!!":
        continue
    # validar que name sea plausible
    if not re.match(r"^[A-Za-z0-9_./\-]+$", name):
        continue
    entries.append((pos, filesize, namesize, name))
    seen_pos.add(pos)

print("entradas válidas:", len(entries))

seen = {}
for abs_pos, filesize, namesize, name in entries:
    if name in seen:
        continue
    datastart = abs_pos + 110 + namesize
    content = data[datastart:datastart+filesize]
    if len(content) != filesize:
        continue
    seen[name] = content

# guardar con nombre hasheado + manifiesto
manifest = []
for i, (name, content) in enumerate(sorted(seen.items())):
    fname = "f%05d" % i
    with open(os.path.join(outdir, fname), "wb") as f:
        f.write(content)
    manifest.append((fname, name, len(content)))

with open(os.path.join(outdir, "MANIFEST.txt"), "w", encoding="utf-8") as mf:
    for fname, name, size in manifest:
        mf.write("%s\t%s\t%d\n" % (fname, name, size))

print("archivos únicos:", len(manifest))
for fname, name, size in manifest:
    low = name.lower()
    if any(k in low for k in ["simlock", "pin", "verify", "unlock", "nvram", "atcmd", "sms", "webserver"]):
        print("  *", fname, name, size)
