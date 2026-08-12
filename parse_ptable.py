import struct

path = "C:/Users/davis/Desktop/herramienta de desbloque/kit_flasheo/B612_11.195.03.00.00_moddedv3.bin"
data = open(path, "rb").read()

# la ptable empieza después de "ptable 1.00" / "V7R500_CPE" / "m3boot"
# entrada: name[16] + 32 bytes de campos
start = data.find(b"m3boot")
print("m3boot en:", hex(start))
pos = start
entries = []
while pos + 48 <= len(data):
    name = data[pos:pos+16].rstrip(b"\x00").decode("latin1", "replace")
    if not name or not all(32 <= ord(c) < 127 or c == "\x00" for c in name):
        break
    fields = data[pos+16:pos+48]
    # probar: 4x uint64 LE
    f64 = struct.unpack("<QQQQ", fields)
    # probar: 8x uint32 LE
    f32 = struct.unpack("<IIIIIIII", fields)
    entries.append((name, f32, f64))
    pos += 48
    if len(entries) > 40:
        break

print("entradas:", len(entries))
for name, f32, f64 in entries:
    print("%-16s u32=%s | u64=%s" % (name, [hex(x) for x in f32], [hex(x) for x in f64]))
