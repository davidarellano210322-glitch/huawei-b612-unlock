@echo off
REM ============================================================
REM  Flasheo USB del Huawei B612 (Mod3-9 - 81.201.01.01.234)
REM  Requiere: router en modo download (metodo de la aguja) y
REM  drivers instalados. Lee README_PASOS.txt ANTES.
REM ============================================================
echo.
echo  PASO 1/2: Cargando usbsafe-b612.bin en el router...
echo  (el router debe estar en modo BOOT_3G, conectado por USB)
echo.
balong_usbdload.exe usbsafe-b612.bin
echo.
pause
echo  PASO 2/2: Flasheando firmware... ESTO TARDA ~10 MINUTOS.
echo  Si termina en 1 minuto, el driver esta mal -> bootloop.
echo  NO desconectar ni apagar durante el proceso.
echo.
balong_flash.exe -gd B612_UPDATE_81.201.01.01.234_sec_M_AT_V3.9.bin
echo.
pause
echo  Listo. Desconecta USB, quita corriente 5 seg, vuelve a
echo  encender SIN SIM, espera 1-2 min y corre desbloquear_b612.py
pause
