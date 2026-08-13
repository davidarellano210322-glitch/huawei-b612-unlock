# 10 — Prueba del Shell Loader V7R5 en Hardware (B612s-51d)

**Router:** Huawei B612s-51d (Balong V7R5 / Hi6950) • IMEI 864596030624094
**Fecha:** 2026-08-13
**Estado:** ⏳ Pendiente de validación en el dispositivo real

---

## 1. Qué estamos probando

`kit_flasheo/usbloader-b612-shell.bin` es un usbloader que, en lugar de
flashear, **arranca un Linux en RAM** con consola root (serial + telnet
+ adb). La prueba consiste en:

1. Poner el router en modo USB Boot (testpoint BOOT + GND).
2. Cargar el shell loader con el exploit secuboot: `-x 4`.
3. Verificar que el kernel arranca el initramfs del shell.
4. Entrar por consola y escribir el item NVRAM 8268 (desbloqueo).

**Es un cambio 100% en RAM** — nada se escribe en flash. Si algo falla,
el router queda exactamente como estaba.

---

## 2. Material necesario

| Material | Notas |
|---|---|
| PC Windows con puerto USB | El exploit usa drivers Windows (FC_Serial, Huawei DataCard) |
| Cable USB (datos) del router | El que venía con el B612 |
| Destornillador pequeño / pinza | Para el puente del testpoint |
| **Adaptador USB-UART (opcional pero MUY recomendado)** | Para ver los logs de arranque del kernel por ttyAMA0 @ 115200 |
| Cable Ethernet | Para entrar por telnet 192.168.8.1 si el UART no está disponible |

> 💡 **El UART es la diferencia entre "no arrancó" y "saber por qué no
> arrancó".** Sin él solo sabrás si el USB se re-enumera o no. Con él
> verás el log del kernel y podrás diagnosticar (consola=, initramfs, etc.).

---

## 3. Preparación (una sola vez)

```cmd
:: 1) Instalar drivers (kit_flasheo/drivers/):
FC_Serial_Driver_Setup.exe
HUAWEI_DataCard_Driver_6.00.08.00_Setup.exe
:: 2) En Windows 10/11: doble clic en Windows10_fix.reg
:: 3) Reiniciar la PC
```

---

## 4. Entrar en modo USB Boot (testpoint)

1. **Desenchufar** el router (sin corriente).
2. Abrir la carcasa (4 tornillos) y localizar el pad **BOOT** en la placa.
   * Referencias: hilo capa9 "algun mod para b612 de entel" (foto con
     los 2 contactos en rojo); canal Telegram t.me/huaweiunlock,
     archivo "plata.jpg" (puntos del B612/TF-i60).
   * ⚠️ La placa del **-51d NO es idéntica** a la del -25d (confirmado
     por usuario TOMCAT en 4PDA).
3. **Cortocircuitar** BOOT con GND (pinza/cable) y MANTENERLO.
4. Conectar el cable USB del router a la PC.
5. **Enchufar** el router a la corriente, esperar 2-3 segundos.
6. **Soltar** el cortocircuito.
7. En Administrador de dispositivos debe aparecer:
   `HUAWEI Mobile Connect - 3G PC UI Interface` o `VID_12D1 & PID_1443`
   `[BOOT_3G]` con un número de puerto COM (ej. COM33).

> Si no aparece el puerto: revisar contactos, reinstalar drivers, repetir.

---

## 5. Cargar el shell loader

```cmd
cd kit_flasheo
balong_usbdload_x.exe -x 4 usbloader-b612-shell.bin
```

- **`-x 4` es imprescindible** (V7R5 / Hi6950): nuestro loader no tiene
  firma de fábrica; sin el exploit el BootROM lo rechaza
  (`oem ca check error / image check error`).
- Si no detecta el COM automáticamente:
  `balong_usbdload_x.exe -p <COM> -x 4 usbloader-b612-shell.bin`

### Qué esperar

1. El programa escribe el usbloader en RAM vía el puerto BOOT_3G.
2. El loader arranca su fastboot → lee el bootimg embebido (kernel +
   ramdisk) → "Booting Linux".
3. El dispositivo USB se re-enumera (desaparece BOOT_3G, aparece la
   interfaz normal del módem).
4. Si tienes UART conectado: aparece el log del kernel con nuestro
   initramfs montándose.

---

## 6. Verificar el arranque de la consola

### 6.1 Vía UART serial (recomendado)

```cmd
:: PuTTY / Tera Term / minicom
:: Velocidad: 115200, 8N1, sin flujo
:: Conectar al puerto del adaptador USB-UART
```

Deberías ver el arranque del kernel y, al final, el prompt de busybox:

```
Booting Linux ...
...
Freeing unused kernel memory: ...K
[init] mounting /proc /sys /dev...
Starting telnetd on port 23
Starting adbd...
/ #
```

### 6.2 Vía telnet (si el módem levanta la red LAN)

```cmd
telnet 192.168.8.1
:: debería dar prompt de shell raíz directamente
```

### 6.3 Vía adb

```cmd
adb connect 192.168.8.1:5555
adb shell
```

---

## 7. Desbloquear desde la shell (si arrancó)

Una vez con prompt de shell raíz:

```
atc at^nvwrex=8268,0,12,1,0,0,0,2,0,0,0,a,0,0,0
```

Luego reiniciar con corte de corriente, sacar el testpoint y probar la
SIM del otro operador.

---

## 8. Diagnóstico si NO arranca

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| El USB se re-enumera pero no hay telnet/adb | El kernel arrancó pero el initramfs falló | Leer UART: revisar `console=` y la cmdline que pasa el loader al kernel |
| El programa reporta error de escritura en RAM | Puente mal hecho / driver / puerto equivocado | Rehacer testpoint, verificar COM, `-p <COM>` explícito |
| No aparece BOOT_3G | Driver o testpoint | Reinstalar drivers, repetir testpoint |
| UART muestra "image check error" | El exploit no se aplicó | Confirmar que se usó `-x 4` (no `-x 2`/`-x 3`) |
| UART muestra kernel panic / no init | El kernel no acepta este initramfs | Revisar cmdline del loader (mem=50M console=ttyAMA0,115200) |

**Regla de oro:** si algo no cuadra, **NO flashear nada más** — apagar,
desenchufar, y volver al método probado (M_AT) o al NCK de Entel.
El shell loader no escribió nada, así que el router sigue intacto.

---

## 9. Checklist final

- [ ] Drivers instalados + reinicio
- [ ] Backup de NVRAM hecho antes de probar (ver doc 09)
- [ ] Router en BOOT_3G (VID_12D1 & PID_1443)
- [ ] `balong_usbdload_x.exe -x 4 usbloader-b612-shell.bin` sin errores
- [ ] UART muestra "Booting Linux" (o telnet/adb responde)
- [ ] `atc at^nvwrex=8268,...` → OK
- [ ] Reboot + SIM de otro operador registrada
