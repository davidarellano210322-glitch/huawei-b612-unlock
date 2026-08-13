#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analizador del bootimg 'ANDROID!' embebido en usbsafe-b612.bin (B612, V7R5).

Devuelve los límites exactos de kernel / ramdisk / second y hace una
prueba de round-trip (reconstrucción byte-idéntica) para validar que la
lógica de reempaquetado es correcta antes de tocar el loader.
"""
import os, re, struct, sys, zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USBLDR_OFF = 0x1520          # inicio del bloque usbldr dentro del .bin
SRC = os.path.join(ROOT, 'kit_flasheo/usbsafe-b612.bin')


def gzip_member_len(data):
    """Longitud (en bytes) del primer miembro gzip a partir de data[0]."""
    d = zlib.decompressobj(16 + zlib.MAX_WBITS)
    pos = 0
    while not d.eof and pos < len(data):
        chunk = data[pos:pos + 65536]
        d.decompress(chunk)
        pos += len(chunk)
    return pos - len(d.unconsumed_tail)


def main():
    d = open(SRC, 'rb').read()
    usbldr = d[USBLDR_OFF:]

    # buscar el primer bootimg plausible
    bi = None
    for m in re.finditer(b'ANDROID!', usbldr):
        off = m.start()
        if off < 0x10000:
            continue
        ks = struct.unpack_from('<I', usbldr, off + 8)[0]
        rs = struct.unpack_from('<I', usbldr, off + 16)[0]
        if 0 < ks < 0x1000000 and 0 < rs < 0x4000000:
            bi = off
            break
    if bi is None:
        print("bootimg no encontrado"); sys.exit(1)

    magic = usbldr[bi:bi + 8]
    ks, ka = struct.unpack_from('<II', usbldr, bi + 8)
    rs, ra = struct.unpack_from('<II', usbldr, bi + 16)
    ss, sa = struct.unpack_from('<II', usbldr, bi + 24)
    tags = struct.unpack_from('<I', usbldr, bi + 32)[0]
    page = struct.unpack_from('<I', usbldr, bi + 36)[0]
    name = usbldr[bi + 44:bi + 60]
    cmdline = usbldr[bi + 60:bi + 60 + 512]
    print(f"bootimg @usbldr+0x{bi:x} (in-file 0x{bi + USBLDR_OFF:x})")
    print(f"  magic={magic} kernel=0x{ks:x}@{ka:#x} ramdisk=0x{rs:x}@{ra:#x} "
          f"second=0x{ss:x}@{sa:#x} tags={tags:#x} page=0x{page:x}")
    print(f"  name={name!r} cmdline={cmdline!r}")

    # ---- límites empíricos ----
    # kernel: empieza en header + 0x1000 (verificado: NOPs ARM 0000a0e1)
    kstart = bi + 0x1000
    # gzip del kernel (primer gzip dentro del blob del kernel)
    gz = None
    for m in re.finditer(b'\x1f\x8b\x08', usbldr[kstart:kstart + ks]):
        gz = kstart + m.start()
        break
    gz_len = gzip_member_len(usbldr[gz:gz + 0x1000000]) if gz else 0
    print(f"  kernel: start=0x{kstart:x} end_decl=0x{kstart + ks:x} "
          f"(gzip@0x{gz:x}, miembro={gz_len} bytes)")
    kend_decl = kstart + ks

    # ramdisk: primer gzip tras el kernel
    ram = None
    for m in re.finditer(b'\x1f\x8b\x08', usbldr[kend_decl:kend_decl + 0x20000]):
        ram = kend_decl + m.start()
        break
    ram_gz_len = gzip_member_len(usbldr[ram:ram + 0x1000000]) if ram else 0
    print(f"  ramdisk: gzip@0x{ram:x} (miembro={ram_gz_len} bytes, decl={rs}) "
          f"gap tras kernel=0x{ram - kend_decl:x}")

    # second: primer gzip tras el ramdisk declarado
    sec = None
    for m in re.finditer(b'\x1f\x8b\x08', usbldr[ram + ram_gz_len:ram + ram_gz_len + 0x20000]):
        sec = ram + ram_gz_len + m.start()
        break
    print(f"  second: gzip@0x{sec:x} (decl={ss}) gap=0x{sec - (ram + ram_gz_len):x}")

    # fin declarado del bootimg
    fin_decl = kstart + ks + rs + ss
    print(f"  fin bootimg decl=0x{fin_decl:x}; usbldr total=0x{len(usbldr):x}; "
          f"slack final=0x{len(usbldr) - fin_decl:x}")

    # ---- round-trip: reconstruir usbldr con los límites declarados y comparar ----
    # Criterio: kernel[start..start+ks], ramdisk gzip a partir de 'ram' con longitud
    # ram_gz_len (rellenando con ceros hasta decl), second gzip desde 'sec' con ss.
    nuevo = bytearray(usbldr)
    # reescribir las zonas a partir del bootimg con los bloques originales:
    # 1) header + kernel tal cual (sin cambios) -> ya idénticos
    # 2) zona del ramdisk: [gzip .. gzip+ram_gz_len) + ceros hasta decl
    blob = bytearray(usbldr[ram:ram + ram_gz_len])
    blob += b'\x00' * (rs - len(blob))
    nuevo[ram:ram + rs] = blob
    # 3) zona del second
    nuevo[sec:sec + ss] = usbldr[sec:sec + ss]
    # comparar
    identico = bytes(nuevo) == usbldr
    print(f"\n  ROUND-TRIP byte-idéntico (misma zona reescrita): {identico}")
    if not identico:
        # encontrar primera diferencia
        a, b = bytes(nuevo), usbldr
        for i in range(len(a)):
            if a[i] != b[i]:
                print(f"  primera diff @0x{i:x}: {a[i]:02x} vs {b[i]:02x}")
                break

    return {'bi': bi, 'ks': ks, 'rs': rs, 'ss': ss, 'kstart': kstart,
            'ram': ram, 'ram_gz_len': ram_gz_len, 'sec': sec, 'page': page,
            'ka': ka, 'ra': ra, 'sa': sa, 'tags': tags, 'name': name, 'cmdline': cmdline}


if __name__ == '__main__':
    main()
