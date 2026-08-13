# 11 — Verificación Forense: unlock_v7r11 (¿algoritmo V5 o interfaz?)

**Objetivo:** determinar si `unlock_v7r11_2018-07-14.exe` contiene un
calculador del algoritmo SIM-Lock V5 o es solo una interfaz de
consultas/escritura. Resultado: **NO contiene ningún algoritmo — es un
cliente ADB que escribe el item NVRAM 8268 directamente**, usando
exactamente la misma técnica que este proyecto ya documenta.

---

## 1. Estructura del archivo

| Capa | Detalle |
|---|---|
| Archivo | `pack_huawei/huaweiB612/unlock_v7r11_2018-07-14.exe` (445.088 bytes) |
| `file` | `PE32 executable for MS Windows 5.00 (GUI), Intel i386, RAR self-extracting archive, 4 sections` |
| **Es un RAR SFX** | El PE es el stub estándar de WinRAR; el archivo RAR5 real está embebido en `0x2f000` (252.576 bytes) |
| Comentario del RAR | `Setup=go.cmd`, `Setup=hideconsole bin\adb kill-server`, `TempMode`, `Silent=1` |

## 2. Contenido real del RAR (extraído)

```
bin/adb.exe         584.584 B  (adb de Google, Nov 2012)
bin/AdbWinApi.dll   102.936 B
hideconsole.exe       7.168 B  (solo CreateProcessW+WaitForSingleObject: oculta consola y lanza adb)
go.cmd                1.282 B  (el "cerebro": script batch en ruso CP866)
```

**No hay ningún binario compilado de cálculo de códigos.** Todo el
"unlocker" es un script de lote.

## 3. go.cmd decodificado (CP866 → texto legible)

```
@title Разблокировка устройств V7R2, V7R11 и V7R50
(Desbloqueo de dispositivos V7R2, V7R11 y V7R50)

1. Pregunta la IP del dispositivo (192.168.8.1 / 192.168.1.1 / otra).
2. bin\adb kill-server
3. bin\adb connect <IP>:5555                      ← entra por ADB
4. bin\adb shell busybox killall add_param        ← mata el proceso add_param
5. bin\adb shell "atc AT^NVWREX=8268,0,12,1,0,0,0,2,0,0,0,A,0,0,0"
                                                  ← ESCRIBE el item 8268 (desbloqueo)
6. bin\adb shell "echo -en 'AT^RESET\r' > /dev/appvcom1"   ← reinicia
```

## 4. Conclusión

1. **NO contiene el algoritmo V5.** No hay ninguna rutina de cálculo,
   MD5, tablas de sal, ni consulta a servidor. El análisis de strings
   del PE completo (445 KB) no encuentra `http`, `server`, `md5`,
   `IMEI`, `NCK`, `algo`, `salt`, `hash` ni `credit` — solo el stub SFX
   de WinRAR y el manifest.

2. **Es exactamente la técnica de escritura NVRAM** que este proyecto
   ya tiene: `atc at^nvwrex=8268,0,12,1,0,0,0,2,0,0,0,a,0,0,0` + reset.
   La única diferencia es el transporte: unlock_v7r11 entra por **ADB
   (puerto 5555)**, nuestro `desbloquear_b612.py` entra por **telnet
   (23/5510)**. El comando de desbloqueo es idéntico.

3. **Por qué no sirve "sin abrir" el router:** el script asume que el
   dispositivo ya tiene **ADB abierto en el puerto 5555**. En el
   firmware de fábrica de Entel (C110) el puerto 5555 está CERRADO
   (auditoría Cap. 03) — por eso el pack original se usaba DESPUÉS de
   flashear un firmware con telnet/ADB activos (M_AT), o en routers
   donde el operador dejó ADB abierto.

4. **Implicación para el proyecto:** confirma dos cosas ya conocidas:
   - No existe calculador V5 (ni siquiera en herramientas que
     aparentan ser "calculadoras de códigos").
   - La vía de desbloqueo es la escritura directa del item 8268, que
     ya tenemos implementada y documentada (Caps. 04, 09 y 10).

## 5. Cómo reproducir

```
cd pack_huawei/huaweiB612
7z x unlock_v7r11_2018-07-14.exe   (o: extraer el RAR desde 0x2f000)
# leer go.cmd con codificación CP866
python -c "open('go.cmd','rb').read().decode('cp866')"
```

## 6. Archivos relacionados

- `pack_huawei/huaweiB612/unlock_v7r11_2018-07-14.exe` (original)
- `pack_huawei/huaweiB612/_unlock_extract/` (extraído en este análisis)
- `documentacion/03_AUDITORIA_WEBUI_Y_ENDPOINTS.md` (puertos cerrados)
- `documentacion/04_GUIAS_DE_DESBLOQUEO_VIABLES.md` (rutas reales)
- `desbloquear_b612.py` (mismo comando NVWREX vía telnet)
