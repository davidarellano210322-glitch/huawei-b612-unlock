# 09 — Shell Loader V7R5, Backup de NVRAM y Verificación del Item 8268

**Router:** Huawei B612s-51d (Balong V7R5 / Hi6950) • IMEI 864596030624094
**Fecha:** 2026-08-13

---

## 1. Shell Loader V7R5 — construido ✅

Se construyó `kit_flasheo/usbloader-b612-shell.bin` a partir del loader
seguro `usbsafe-b612.bin` del B612. Es un usbloader que, en vez de
flashear, arranca una **consola** (serial + telnet + adb) sin tocar el
firmware instalado.

### 1.1 Qué hay dentro

| Componente | Descripción |
|---|---|
| `raminit` | Sin cambios (bloque de arranque del usbloader) |
| `usbldr` fastboot | Sin cambios (código que expone el modo USB Boot) |
| ptable `V7R500_CPE` | Sin cambios |
| **kernel** (Android bootimg `ANDROID!` @0x5c508) | Sin cambios (zImage gzip ARM, 0x5971e0 bytes) |
| **ramdisk nuevo** | **Initramfs autónomo con busybox estático** + telnetd + adbd + consola serial |
| `second` (cpio `sbin/reboot`) | Absorbido por el ramdisk (`second_size=0`) |
| cola tras el bootimg | Sin cambios (datos firmados/cifrados, se preservan en su posición absoluta) |

El **initramfs** (2.317.340 bytes cpio → 1.297.617 bytes gzip) contiene:

```
/init  -> symlink a busyboxx (applet "init" de busybox)
/bin/busyboxx    busybox ARM estático 2.191.352 bytes (extraído del M_AT)
/bin/adbd        daemon adb ARM estático 117.968 bytes
/bin/sh, /bin/telnetd, /bin/mount, /bin/mknod, /bin/devmem, /bin/vi,
/bin/nc, /bin/ps, /bin/top, /bin/ip, /bin/wget, ...  (symlinks a busybox)
/etc/inittab     ::sysinit:/etc/init.d/rcS + shells en ttyAMA0/console
/etc/init.d/rcS  monta proc/sys/devtmpfs; lanza telnetd :23 y adbd
/etc/profile     entorno del shell
/default.prop    ro.secure=0, ro.debuggable=1, persist.sys.usb.config=adb
/dev/console (5:1), /dev/null (1:3), /dev/ttyAMA0 (204:64)  (nodos cpio)
```

### 1.2 Por qué funciona (evidencia del propio loader)

Las cadenas internas del código fastboot del loader (bloque usbldr,
offset 0x0–0x30000) confirman el flujo de arranque:

```
boot        boot kernel from flash.
boot cshell boot with cshell.
FASTBOOT simple console, enter 'help' for commands help.
kernel  @ %x (%d bytes)
ramdisk @ %x (%d bytes)
CANNOT READ KERNEL IMAGE / CANNOT READ RAMDISK IMAGE
mem=50M console=ttyAMA0,115200
Booting Linux / end boot linux
oem ca check error, usb boot... / image check error, usb boot...
```

El loader lee el bootimg embebido (kernel + ramdisk) usando los campos
del header `ANDROID!` y arranca Linux; la consola serial es
**ttyAMA0 @ 115200**. Al sustituir el ramdisk por el initramfs del
shell, el kernel arranca nuestro `/init` (busybox) y levanta las
consolas.

### 1.3 Repempaquetado (round-trip verificado)

`shell_loader/construir_shell.py` reensambla el bloque usbldr:

1. **Round-trip primero:** reconstruye el loader original con sus
   componentes originales → **byte-idéntico** (lógica validada).
2. **Build:** sustituye el ramdisk en la misma posición (0x5f3fe8 del
   bloque usbldr), absorbe la ranura del `second` (second_size → 0),
   actualiza `ramdisk_size` en el header del bootimg y **deja la cola
   (datos cifrados) y la cabecera del usbloader sin tocar** (el tamaño
   total del bloque no cambia: 0x794fe8).

Verificación del resultado: `balong_usbdload_x.exe -m
usbloader-b612-shell.bin` parsea el loader y muestra la ptable
`V7R500_CPE` correctamente; el ramdisk nuevo descomprime como cpio
válido con `070701`; el kernel queda intacto.

### 1.4 Cómo cargarlo (requiere hardware)

```cmd
:: 1) Entrar en modo USB Boot (testpoint BOOT + GND, ver kit_flasheo)
:: 2) Cargar el shell loader con el exploit secuboot (-x 4 = V7R5):
cd kit_flasheo
balong_usbdload_x.exe -x 4 usbloader-b612-shell.bin
```

**El `-x 4` es imprescindible:** el loader modificado ya no tiene la
firma de fábrica; el BootROM lo rechazaría con `oem ca check error /
image check error`. El exploit escribe 8 ceros en la estructura de
SRAM 0x1001FFEC y desactiva la verificación.

Consolas esperadas tras arrancar:
- **Serial (UART):** ttyAMA0 @ 115200 — shell raíz directo
- **Telnet:** puerto 23 (IP LAN del router) — shell raíz directo
- **ADB:** `adb connect <IP>:5555` → `adb shell`

### 1.5 Lo que requiere prueba en hardware

El análisis estático verificó: estructura del loader, localización del
bootimg, round-trip byte-idéntico, initramfs válido, y el flujo de
arranque descrito por las cadenas del propio loader. **Queda pendiente
de validar en el dispositivo real:** que el fastboot del loader arranque
el bootimg embebido en esta variante C110, y que el kernel acepte el
initramfs (si no arranca, revisar `console=` y la línea de comandos que
pasa el loader al kernel). Es un cambio puramente en RAM: nada se
escribe en flash, por lo que es seguro de probar.

---

## 2. Backup completo de la NVRAM (procedimiento)

Antes de cualquier modificación del router conviene respaldar la NVRAM
completa (IMEI, calibración RF, serial, items SIM-lock).

### 2.1 Vía 1 — fastboot (balong-fbtools) tras `-x 4`

```
1. Modo USB Boot (testpoint) → balong_usbdload_x.exe -x 4 usbsafe-b612.bin
2. El loader queda en fastboot (USB). Con balong-fbtools:
     python3 fbtool.py -p <port> oem ptable       # ver mapa de particiones
     python3 fbtool.py -p <port> dump nvimg nvimg.bin
     python3 fbtool.py -p <port> dump nvdload nvdload.bin
     python3 fbtool.py -p <port> dump nvdefault nvdefault.bin
     python3 fbtool.py -p <port> dump oeminfo oeminfo.bin
   (balong-fbtools: github.com/forth32/balong-fbtools; puerto = COMx
    o /dev/ttyUSBx del modo Boot)
3. Guardar también: m3boot, fastboot, kernel, kernelbk (imágenes de
   arranque) si se quiere restaurar todo.
```

### 2.2 Vía 2 — desde el firmware (sin hardware)

Las particiones NV ya vienen dentro del firmware de actualización. Se
pueden extraer como se hizo en esta investigación:

```
1. Localizar la firma de NV "DIN\x22" (0x224e4944) en
   B612_UPDATE_*.bin  →  offset 0x17f620e (M_AT V3.9)
2. Extraer 4 MB desde ese offset → nvram.bin
3. balong-nvtool.exe -l nvram.bin    # mapa (4 archivos: common,
                                     # TL_NvTable, PRODUCT_NvTable, GU_NvTable)
4. balong-nvtool.exe -e nvram.bin    # extrae todas las celdas a .nvm
```

### 2.3 Cómo restaurar

Con balong-nvtool se edita la imagen (`-r item:file`, `-m item+off:...`)
y se flashea la partición `nvimg` por fastboot/balong_flash. **OJO:**
solo restaurar la NVRAM del mismo equipo/IMEI; mezclar NVRAM de otro
equipo rompe IMEI/calibración.

---

## 3. Verificación del item 8268 con balong-nvtool (hecho ✅)

Con la imagen NV extraída del firmware M_AT (producto
**Balong V700R500C31B201**, V7R5), `balong-nvtool.exe -d 8268`
devuelve el valor **de fábrica (desbloqueado)**:

```
-- Item # 8268: 12 bytes -- archivo 4 (GU_NvTable.bin) -- en_NV_Item_CardlockStatus
00000000: 00 00 00 00 02 00 00 00 0a 00 00 00
```

### 3.1 Decodificación definitiva del item 8268 (12 bytes = 3 × U32 LE)

| Offset | Campo | Fábrica | Bloqueado | Write del kit |
|---|---|---|---|---|
| 0x00 | Switch cardlock (0=off, 1=on) | `0x00` | `0x01` | `0x01` |
| 0x04 | **Estado (1=bloqueado, 2=desbloqueado)** | `0x02` | `0x01` | **`0x02`** |
| 0x08 | Intentos restantes/máximos | `0x0A` (10) | `0x0A` (10) | `0x0A` (10) |

Evidencia cruzada:
- **Fábrica (desbloqueado), este dump:** `00 00 00 00 02 00 00 00 0A 00 00 00`
- **Bloqueado (comunidad, E3372 FAQ / MTS):** `01 00 00 00 01 00 00 00 0A 00 00 00`
  (la escritura que BLOQUEA un MTS usa `...,1,0,0,0,A,...` en el byte 4)
- **Unlock universal (kit):** `01 00 00 00 02 00 00 00 0A 00 00 00`
  → flips el byte 4 de `01` a `02`
- **B612 desbloqueado (simlog.txt):** WebUI `SimLockEnable=0, Remain=10`
- **Item 8269** (`CustomizeSimLockMaxTimes`, 8 bytes): `00 00 00 00 0A 00 00 00`
  (máximo de intentos = 10, coherente con `at^maxlcktms=10`)
- **Item 8267** (`CustomizeSimLockPlmnInfo`, 344 bytes): `AA AA ...`
  (lista PLMN vacía de fábrica → sin operador autorizado)
- **Item 8253** (`Sim_Personalisation_Pwd`): `12345678` (default Huawei)

> Nota sobre el byte 0: el write del kit lo deja en `1` mientras que la
> fábrica lo trae en `0`. El estado efectivo lo decide el byte 4; la
> evidencia empírica (B612 desbloqueado reporta Enable=0) confirma que
> `word1=2` es el valor desbloqueado.

### 3.2 Cómo repetir la verificación

```cmd
balong-nvtool\winbuild\Release\balong-nvtool.exe -l shell_loader\extraido\nv_b.bin
balong-nvtool\winbuild\Release\balong-nvtool.exe -d 8268 shell_loader\extraido\nv_b.bin
```

---

## 4. Archivos generados en esta ronda

```
kit_flasheo/usbloader-b612-shell.bin    shell loader V7R5 (listo para -x 4)
shell_loader/construir_shell.py         builder (extrae → modifica → reempaqueta)
shell_loader/analizar_bootimg.py        analizador del bootimg ANDROID!
shell_loader/raiz/                      plantilla del initramfs (inittab, rcS, profile)
shell_loader/extraido/                  binarios y librerías extraídos del M_AT
shell_loader/extraido/nv_b.bin          imagen NV del firmware (para nvtool)
balong-nvtool/winbuild/Release/balong-nvtool.exe   ya compilado (V1.0.215)
```

## 5. Advertencias

- El shell loader **no escribe nada en flash** (carga en RAM) → seguro
  de probar; si no arranca, el dispositivo sigue igual.
- Usar **solo** con `-x 4` (loader sin firma). Sin el exploit el
  BootROM lo rechaza.
- El backup de NVRAM es **por equipo**: restaurar la de otro router
  rompe IMEI y calibración.
- Tras el desbloqueo por NVRAM, **no hacer factory reset** (corrompe la
  calibración de señal — ver README principal).
