#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Construye el shell loader V7R5 para el B612.

Parte del bootloader seguro usbsafe-b612.bin y sustituye el ramdisk de la
imagen de arranque 'ANDROID!' embebida por un initramfs autónomo que arranca
una consola (serial ttyAMA0, telnet :23, adb :5555) usando un busybox
estático ARM extraído del firmware M_AT.

Estrategia de reempaquetado (sin cambiar el tamaño total del bloque usbldr):
  - El ramdisk nuevo se coloca en la misma posición que el original.
  - La ranura del 'second' (un cpio inútil con solo sbin/reboot) se absorbe:
    si el ramdisk nuevo cabe en ramdisk+second, second_size se pone a 0 y
    TODO lo que va después (cola) queda en su posición absoluta original.
  - Únicamente cambian los campos ramdisk_size y second_size del header
    del bootimg; la cabecera del usbloader (tamaño del bloque) no cambia.

Uso:  python construir_shell.py
Salida: shell_loader/usbloader-b612-shell.bin (+ copia en kit_flasheo/)
"""
import gzip as gzipmod
import io
import os
import re
import struct
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'kit_flasheo', 'usbsafe-b612.bin')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'usbloader-b612-shell.bin')
OUT_KIT = os.path.join(ROOT, 'kit_flasheo', 'usbloader-b612-shell.bin')
RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raiz')
BIN_STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extraido', 'bin', 'busyboxx_static')
ADBD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extraido', 'bin', 'adbd')

USBLDR_OFF = 0x1520
PAGE = 0x1000


# ----------------------------------------------------------------------
# utilidades cpio newc
# ----------------------------------------------------------------------
def cpio_header(name, mode, size=0, nlink=1, uid=0, gid=0, mtime=0,
                rdevmajor=0, rdevminor=0):
    def hx8(v):
        return ('%08x' % v).encode()
    # newc: magic + ino + mode + uid + gid + nlink + mtime + size +
    #       devmajor + devminor + rdevmajor + rdevminor + namesize + check
    # mode conserva TODOS los bits de tipo (dir/symlink/reg/char) + permisos
    hdr = (b'070701' + hx8(0) + hx8(mode & 0o177777) + hx8(uid) +
           hx8(gid) + hx8(nlink) + hx8(mtime) + hx8(size) + hx8(0) + hx8(0) +
           hx8(rdevmajor) + hx8(rdevminor) + hx8(len(name) + 1) + hx8(0))
    assert len(hdr) == 110, len(hdr)
    pad = (4 - ((110 + len(name) + 1) % 4)) % 4
    return hdr + name.encode() + b'\x00' + b'\x00' * pad


def cpio_file(name, content, mode):
    # si no trae bits de tipo, asumir archivo regular
    if not (mode & 0o170000):
        mode |= 0o100000
    out = cpio_header(name, mode, len(content))
    out += content
    out += b'\x00' * ((4 - (len(content) % 4)) % 4)
    return out


def cpio_dir(name, mode=0o755):
    return cpio_header(name, 0o040000 | mode)


def cpio_symlink(name, target, mode=0o777):
    return cpio_file(name, target.encode(), 0o120000 | mode)


def cpio_dev(name, major, minor, mode=0o600):
    out = cpio_header(name, 0o020000 | mode, rdevmajor=major, rdevminor=minor)
    return out


def build_cpio(entries):
    """entries: lista de (tipo, name, ...) ya serializadas en bytes."""
    buf = b''.join(entries)
    # trailer
    buf += cpio_header('TRAILER!!!', 0)
    return buf


# ----------------------------------------------------------------------
# localización de componentes dentro del loader
# ----------------------------------------------------------------------
def localizar_bootimg(usbldr):
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
        raise SystemExit('bootimg ANDROID! no encontrado en el loader')
    ks = struct.unpack_from('<I', usbldr, bi + 8)[0]
    rs = struct.unpack_from('<I', usbldr, bi + 16)[0]
    ss = struct.unpack_from('<I', usbldr, bi + 24)[0]
    kstart = bi + PAGE
    # ramdisk: primer gzip tras el kernel declarado
    ram = None
    for m in re.finditer(b'\x1f\x8b\x08', usbldr[kstart + ks:kstart + ks + 0x20000]):
        ram = kstart + ks + m.start()
        break
    if ram is None:
        raise SystemExit('gzip del ramdisk no encontrado')
    # second: primer gzip tras la zona DECLARADA del ramdisk (puede haber
    # un pequeño gap de padding entre ambos)
    sec = None
    for m in re.finditer(b'\x1f\x8b\x08', usbldr[ram + rs:ram + rs + 0x20000]):
        sec = ram + rs + m.start()
        break
    if sec is None:
        raise SystemExit('gzip del second no encontrado')
    return {'bi': bi, 'ks': ks, 'rs': rs, 'ss': ss, 'kstart': kstart,
            'ram': ram, 'sec': sec}


# ----------------------------------------------------------------------
# construcción del initramfs del shell
# ----------------------------------------------------------------------
def construir_initramfs():
    if not os.path.exists(BIN_STATIC):
        raise SystemExit('falta busyboxx_static (ejecuta extraer primero)')
    bb = open(BIN_STATIC, 'rb').read()
    adbd = open(ADBD, 'rb').read() if os.path.exists(ADBD) else b''

    cfg = {}
    for rel in ['etc/inittab', 'etc/profile', 'etc/init.d/rcS', 'default.prop']:
        p = os.path.join(RAIZ, rel)
        if os.path.exists(p):
            cfg[rel] = open(p, 'rb').read()

    # --- arbol del initramfs ---
    e = []
    e.append(cpio_dir('.'))
    e.append(cpio_dir('bin'))
    e.append(cpio_dir('dev'))
    e.append(cpio_dir('etc'))
    e.append(cpio_dir('etc/init.d'))
    e.append(cpio_dir('proc'))
    e.append(cpio_dir('root'))
    e.append(cpio_dir('sbin'))
    e.append(cpio_dir('sys'))
    e.append(cpio_dir('tmp'))
    e.append(cpio_dir('var'))

    # busybox estático
    e.append(cpio_file('bin/busyboxx', bb, 0o755))
    # applets por symlink (argv[0] -> applet de busybox)
    for app in ['init', 'sh', 'telnetd', 'login', 'mount', 'mknod', 'devmem',
                'vi', 'nc', 'ps', 'top', 'cat', 'ls', 'ifconfig', 'ip',
                'kill', 'ps', 'wget', 'dmesg', 'mount', 'umount', 'echo',
                'sleep', 'cp', 'mv', 'rm', 'mkdir', 'chmod', 'chown']:
        e.append(cpio_symlink('bin/' + app, 'busyboxx'))
    e.append(cpio_symlink('sbin/init', 'busyboxx'))
    # /init -> busybox (applet init)
    e.append(cpio_symlink('init', 'bin/busyboxx'))
    # adbd estático
    if adbd:
        e.append(cpio_file('bin/adbd', adbd, 0o755))

    # configs
    for rel, content in cfg.items():
        e.append(cpio_file(rel, content, 0o755 if rel == 'etc/init.d/rcS' else 0o644))

    # nodos de dispositivo
    e.append(cpio_dev('dev/console', 5, 1))
    e.append(cpio_dev('dev/null', 1, 3))
    e.append(cpio_dev('dev/ttyAMA0', 204, 64))
    e.append(cpio_dev('dev/ttyS0', 204, 64))
    e.append(cpio_dev('dev/tty', 5, 0))

    cpio = build_cpio(e)
    # formato GZIP (igual que el ramdisk original: 1f 8b 08 ...), no zlib
    gz = gzipmod.compress(cpio, compresslevel=9)
    return cpio, gz


# ----------------------------------------------------------------------
# ensamblado del loader
# ----------------------------------------------------------------------
def ensamblar(usbldr, comp, gz_ramdisk, rs_new=None, ss_new=None):
    bi = comp['bi']
    ram = comp['ram']
    rs = comp['rs']
    ss = comp['ss']
    sec = comp['sec']

    if rs_new is None:
        rs_new = rs
    if ss_new is None:
        ss_new = ss
    if len(gz_ramdisk) > rs_new:
        raise SystemExit(f'ramdisk gzip {len(gz_ramdisk)} > ranura {rs_new}')

    # ranura absorbible: desde el ramdisk original hasta el FIN del second
    fin_second = sec + ss
    slot = fin_second - ram
    if len(gz_ramdisk) > slot:
        raise SystemExit(
            f'ramdisk nuevo demasiado grande: {len(gz_ramdisk)} > {slot} '
            '(ranura ramdisk+second)')

    out = bytearray(usbldr)

    # 1) header del bootimg: actualizar ramdisk_size y second_size
    struct.pack_into('<I', out, bi + 16, rs_new)
    struct.pack_into('<I', out, bi + 24, ss_new)

    # 2) ramdisk nuevo (en la posición del original)
    out[ram:ram + len(gz_ramdisk)] = gz_ramdisk

    # 3) relleno hasta el tamaño declarado del ramdisk
    out[ram + len(gz_ramdisk):ram + rs_new] = b'\x00' * max(0, rs_new - len(gz_ramdisk))

    # 4) si absorbemos el second (ss_new=0), rellenar con ceros TODA la zona
    #    [fin del ramdisk .. fin del second]; en round-trip (ss_new=ss) la
    #    zona del second se deja intacta.
    if ss_new == 0:
        out[ram + rs_new:fin_second] = b'\x00' * (fin_second - ram - rs_new)

    # 5) TODO lo demás (kernel, cola tras el bootimg) queda en su sitio.
    return bytes(out)


# ----------------------------------------------------------------------
def main():
    d = open(SRC, 'rb').read()
    usbldr = d[USBLDR_OFF:]

    print(f"== {os.path.basename(SRC)}: {len(d)} bytes")
    comp = localizar_bootimg(usbldr)
    print(f"bootimg @0x{comp['bi']:x}: kernel 0x{comp['ks']:x} "
          f"ramdisk 0x{comp['rs']:x} second 0x{comp['ss']:x} "
          f"ramdisk_gzip @0x{comp['ram']:x}")

    # --- round-trip: reconstruir con los componentes ORIGINALES ---
    gz_orig = usbldr[comp['ram']:comp['ram'] + comp['rs']]
    rt = ensamblar(usbldr, comp, gz_orig, rs_new=comp['rs'], ss_new=comp['ss'])
    if rt == usbldr:
        print("ROUND-TRIP: reconstrucción byte-idéntica OK (lógica validada)")
    else:
        for i in range(len(rt)):
            if rt[i] != usbldr[i]:
                print(f"ROUND-TRIP FALLO en 0x{i:x}: {rt[i]:02x} vs {usbldr[i]:02x}")
                raise SystemExit(1)

    # --- initramfs del shell ---
    cpio, gz = construir_initramfs()
    print(f"initramfs: cpio {len(cpio)} bytes -> gzip {len(gz)} bytes "
          f"(ranura disponible {comp['rs'] + comp['ss']} bytes)")

    nuevo_usbldr = ensamblar(usbldr, comp, gz, rs_new=len(gz), ss_new=0)

    # --- ensamblar archivo completo ---
    nuevo = bytearray(d)
    nuevo[USBLDR_OFF:USBLDR_OFF + len(nuevo_usbldr)] = nuevo_usbldr

    for p in (OUT, OUT_KIT):
        with open(p, 'wb') as f:
            f.write(nuevo)
        print(f"escrito: {p} ({len(nuevo)} bytes)")

    # --- verificación: reparsear el resultado ---
    v = localizar_bootimg(nuevo_usbldr)
    rs_new = struct.unpack_from('<I', nuevo_usbldr, v['bi'] + 16)[0]
    ss_new = struct.unpack_from('<I', nuevo_usbldr, v['bi'] + 24)[0]
    gz_new = nuevo_usbldr[v['ram']:v['ram'] + rs_new]
    try:
        cp = zlib.decompress(gz_new, 16 + zlib.MAX_WBITS)
        ok_cpio = b'070701' in cp[:8] or b'070702' in cp[:8]
    except Exception as e:
        ok_cpio = False
        print('  advertencia descompresión ramdisk:', e)
    print(f"verificación: ramdisk_size={rs_new} second_size={ss_new} "
          f"cpio válido={ok_cpio} kernel@0x{v['kstart']:x} intacto "
          f"(magic kernel: {nuevo_usbldr[v['kstart']:v['kstart']+4].hex()})")

    print("""
LISTO. Cargar en el B612 con el exploit secuboot:
    balong_usbdload_x.exe -x 4 usbloader-b612-shell.bin
(puerto en modo USB Boot: testpoint BOOT + GND; el -x 4 desactiva la
verificación de firma del BootROM, imprescindible para un loader modificado)

Consolas esperadas tras arrancar:
    - serial:  ttyAMA0 @ 115200  (UART del B612)
    - telnet:  puerto 23 (IP LAN del router)
    - adb:     puerto 5555  (adb connect <IP>:5555)
""")


if __name__ == '__main__':
    main()
