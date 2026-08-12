import struct

path = "C:/Users/davis/Desktop/herramienta de desbloque/kit_flasheo/B612_11.195.03.00.00_moddedv3.bin"
data = open(path, "rb").read()
off = 0x1ff679e
sb = data[off:off + 96]
fmt = "<IIIIIIHHIIIII"
print("len(data)=", len(data), "len(sb)=", len(sb), "len(sb[:52])=", len(sb[:52]))
print("calcsize(fmt)=", struct.calcsize(fmt))
vals = struct.unpack(fmt, sb[:struct.calcsize(fmt)])
magic, inodes, mtime, blocksize, frags, comp, blocklog, flags, idcount, vmaj, vmin, rootinode, bytes_used = vals
print("magic=%#x inodes=%d blocksize=%d comp=%d blocklog=%d vmaj=%d.%d" % (magic, inodes, blocksize, comp, blocklog, vmaj, vmin))
print("bytes_used=%d -> fin aprox %#x" % (bytes_used, off + bytes_used))
with open("rootfs.sqsh", "wb") as f:
    f.write(data[off:off + bytes_used])
print("carve:", bytes_used, "bytes")
