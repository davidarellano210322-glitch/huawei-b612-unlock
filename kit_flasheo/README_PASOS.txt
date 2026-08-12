===========================================================
 GUIA DE FLASHEO USB - Huawei B612s-51d (Entel Chile)
===========================================================
Kit completo con: 2 firmwares (con telnet+adb verificados),
balong_usbdload, balong_flash, usbsafe-b612.bin, drivers.

ANTES DE EMPEZAR
- Desactiva las actualizaciones automaticas en la web del
  router (192.168.8.1 -> Ajustes). No flashees si el router
  esta haciendo otra cosa.
- Este metodo es EL UNICO PROBADO para el -51d (usuario aomsk
  en 4PDA lo hizo exactamente asi). NO se puede por web.
- Riesgo bajo pero real: si algo sale mal se puede repetir el
  flasheo. No hagas factory reset despues de desbloquear.

-----------------------------------------------------------
PASO 0: DRIVERS (solo la primera vez)
-----------------------------------------------------------
1. Instala drivers\FC_Serial_Driver_Setup.exe
2. Instala drivers\HUAWEI_DataCard_Driver_6.00.08.00_Setup.exe
3. Si usas Windows 10/11: doble clic en drivers\Windows10_fix.reg
   (acepta el aviso, importa el registro)
4. Reinicia la PC.

-----------------------------------------------------------
PASO 1: MODO DOWNLOAD (metodo de la aguja)
-----------------------------------------------------------
El router tiene un punto BOOT en la placa. Hay que ponerlo en
modo descarga por USB asi:

1. DESENCHUFA el router (sin corriente).
2. Abre la carcasa (4 tornillos). Localiza los pads de BOOT:
   - En el foro capa9, hilo "algun mod para b612 de entel"
     (es tu mismo router Entel) hay una foto con los 2 contactos
     marcados en rojo.
   - En el canal Telegram t.me/huaweiunlock, el archivo
     "plata.jpg" muestra los puntos del B612/TF-i60.
   - OJO: la placa del -51d NO es identica a la del -25d
     (lo confirmo el usuario TOMCAT en 4PDA).
3. Cortocircuita el pad BOOT con GND (destornillador/pinza,
   o cable) y MANTENLO.
4. Conecta el cable USB del router a la PC (el puerto USB del
   router, o los pads de datos si usas cable soldado).
5. ENCHUFA el router a la corriente. Espera 2-3 segundos.
6. SUELTA el cortocircuito del BOOT.
7. En Administrador de dispositivos debe aparecer un puerto
   nuevo: "HUAWEI Mobile Connect - 3G PC UI Interface" o
   VID_12D1&PID_1443 [BOOT_3G] con un numero COM (ej: COM33).

Si no aparece el puerto: revisa los puntos de contacto,
reinstala drivers y repite. (El usuario aomsk con -51d no
tuvo problemas con este metodo.)

-----------------------------------------------------------
PASO 2: CARGAR USBSAFE
-----------------------------------------------------------
Desde esta carpeta (kit_flasheo), con el router en modo
BOOT_3G conectado:

  balong_usbdload.exe usbsafe-b612.bin

(Alternativa: Balong_USB_Downloader_1.0.1.10.exe -> Detect ->
seleccionar usbsafe-b612.bin -> Upload)

Si no detecta el COM automaticamente:
  balong_usbdload.exe -p <COM> usbsafe-b612.bin

-----------------------------------------------------------
PASO 3: FLASHEAR FIRMWARE (~10 MINUTOS)
-----------------------------------------------------------
Elige UNO de los dos firmware (ambos traen telnet+adb, ya
verificado analizando los archivos):

  OPCION A (recomendada, familia M_AT):
    balong_flash.exe -gd B612_UPDATE_81.201.01.01.234_sec_M_AT_V3.9.bin

  OPCION B (11.195, muy estable en FDD):
    balong_flash.exe -gd B612_11.195.03.00.00_moddedv3.bin

(o con puerto explicito: balong_flash.exe -p 33 -gd <archivo>)

IMPORTANTE:
- Debe tardar ~10 minutos. Si termina en 1 minuto, el driver
  esta mal instalado -> bootloop. Reinstala drivers y repite.
- NO desconectes ni quites corriente durante el flasheo.
- Si el flasheo falla a mitad, repite el proceso desde el paso 1.

-----------------------------------------------------------
PASO 4: PRIMER ENCENDIDO
-----------------------------------------------------------
1. Desconecta el cable USB del router.
2. Quita la corriente 5 segundos y vuelve a enchufar.
3. Espera 1-2 minutos hasta que las luces queden estables.
4. Conecta tu PC al LAN/WiFi del router (192.168.8.1 debe
   responder).

-----------------------------------------------------------
PASO 5: DESBLOQUEAR (telnet)
-----------------------------------------------------------
Con la PC en la red del router, corre (desde la carpeta
herramienta de desbloque):

  python desbloquear_b612.py

Ese script prueba telnet (23 y 5510) y envia el comando que
quita el SIM-Lock:
  atc at^nvwrex=8268,0,12,1,0,0,0,2,0,0,0,a,0,0,0

Alternativa manual:
  telnet 192.168.1.1 5510
  (usuario: root, si pide) y luego:
  atc at^nvwrex=8268,0,12,1,0,0,0,2,0,0,0,a,0,0,0

Despues apaga/enciende el router (corte breve de corriente)
y pon la SIM de la otra compania.

-----------------------------------------------------------
ADVERTENCIAS FINALES (importantes)
-----------------------------------------------------------
- NO hagas factory reset despues del desbloqueo: la NVRAM
  queda marcada y pierdes conexion (aviso de gonzalo bahia,
  usuario con tu mismo router Entel).
- Si quieres respaldar la NVRAM antes de tocar nada, puedes
  hacerlo via adb/telnet (at^nvrd) o con la herramienta
  unlock_v7r11_2018-07-14.exe del pack original (pestaña ADB,
  connect 192.168.8.1:5555).
- El cambio de CUST (por si quieres otro operador/bandas):
  atc AT^VERSION=INI,B612s-25dCUST-B00C00
- Si todo falla: llama a Entel al 800 367 626, pide el NCK
  gratis con tu IMEI (ley chilena), es sin riesgo.
===========================================================
