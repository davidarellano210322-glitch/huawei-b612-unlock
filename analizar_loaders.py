#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analizador de usbloaders: identifica plataforma y compatibilidad con el
patcher de balong-usbdload (pv7r1/pv7r2/pv7r11/pv7r22) y con el exploit -x.

Cabecera usbloader (balong-usbdload.c):
  off  0: uint32 sig (0x20000)
  off 36: 16 bytes descriptor raminit {lmode u32, size u32, adr u32, offset u32}
  off 52: 16 bytes descriptor usbldr  {lmode u32, size u32, adr u32, offset u32}
"""
import os
import struct

# Firmas de parcheo de eraseall (patcher.c) -> plataforma
SIGS = {
    "V7R1  (Hi6920)": bytes.fromhex("3DE2E0E300E09EE55CC39FE50C005EE1000000000A"),
    "V7R2  (Hi6930)": bytes.fromhex("0030A0E39A3F07EEFF2F0FE3E12F44E3073002E59A3F07EE0040A0E3E04F44E34E3604E34C3444E3303384E5"),
    "V7R11 (Hi6921)": bytes.fromhex("000050E37080BD080030A0E34E2604E3E03F44E3552244E34C019FE54EC604E348419FE50210A0E14CC444E35C2383E500008FE040C383E5"),
    "V7R22 (Hi6932)": bytes.fromhex("123BA0E34A354AE30020A0E37820C3E57920C3E57A20C3E57B20C3E50000A0E3"),
    "V7R22_2       ": bytes.fromhex("183094E5102094E50D00A0E1304084E214308DE510208DE5"),
    "V7R22_3       ": bytes.fromhex("103094E50D00A0E110308DE5183094E514308DE5"),
}

PTABLE_MAGIC = bytes.fromhex("705461626c6548656164000000000080")
ANDROID = b"ANDROID!"

def scan(path):
    data = open(path, "rb").read()
    sig = struct.unpack_from("<I", data, 0)[0]
    out = [f"== {os.path.basename(path)}  ({len(data)} bytes)"]
    out.append(f"   sig(off0)=0x{sig:x} {'OK' if sig == 0x20000 else 'NO-USBLDR'}")

    # Descriptores de bloque (raminit y usbldr)
    for name, off in (("raminit", 36), ("usbldr", 52)):
        lmode, size, adr, offs = struct.unpack_from("<IIII", data, off)
        out.append(f"   {name:7s} lmode={lmode} size=0x{size:x}({size}) adr=0x{adr:08x} offset=0x{offs:x}")

    # Firmas de parcheo
    found = []
    for plat, sg in SIGS.items():
        idx = data.find(sg)
        if idx >= 0:
            found.append(f"{plat}@0x{idx:x}")
    out.append(f"   patch-sig: {', '.join(found) if found else 'NINGUNA (patcher NO la soporta)'}")

    # Tabla de particiones
    ptoff = data.find(PTABLE_MAGIC)
    if ptoff >= 0:
        prod = data[ptoff + 32: ptoff + 48].decode(errors="replace").strip("\x00")
        ver = data[ptoff + 16: ptoff + 32].decode(errors="replace").strip("\x00")
        out.append(f"   ptable @0x{ptoff:x}  version={ver!r} product={prod!r}")
    else:
        out.append(f"   ptable: NO encontrada")

    # Kernel ANDROID
    koff = data.rfind(ANDROID)
    if koff >= 0:
        out.append(f"   kernel ANDROID! @0x{koff:x} (carga fastboot posible)")
    return "\n".join(out), found, ptoff


if __name__ == "__main__":
    import sys
    roots = sys.argv[1:] or ["balong-usbdload", "kit_flasheo"]
    files = []
    for r in roots:
        for f in sorted(os.listdir(r)):
            if f.endswith((".bin", ".BIN")) or (f.endswith(".exe") is False and os.path.isfile(os.path.join(r, f))):
                if f.lower().endswith((".bin",)):
                    files.append(os.path.join(r, f))
    for fp in files:
        try:
            print(scan(fp)[0])
            print()
        except Exception as e:
            print(f"== {fp}: ERROR {e}\n")
