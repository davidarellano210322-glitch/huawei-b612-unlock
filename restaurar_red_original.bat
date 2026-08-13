@echo off
:: ============================================================================
:: RESTAURADOR DE RED Y CONFIGURACION ORIGINAL DE WINDOWS
:: ============================================================================
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo Solicitando permisos de Administrador...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"

cls
color 0E
echo ============================================================================
echo      RESTAURANDO CONFIGURACION DE RED Y VALORES POR DEFECTO
echo ============================================================================
echo.

echo [1/6] Restaurando propiedades del adaptador Intel Wi-Fi 6 AX201 a valores por defecto...
powershell -NoProfile -Command "Set-NetAdapterAdvancedProperty -Name 'Wi-Fi' -DisplayName 'Agresividad de itinerancia' -DisplayValue '3. Mediano' -ErrorAction SilentlyContinue"
powershell -NoProfile -Command "Set-NetAdapterAdvancedProperty -Name 'Wi-Fi' -DisplayName 'Banda preferida' -DisplayValue '1. Sin preferencias' -ErrorAction SilentlyContinue"
powershell -NoProfile -Command "Set-NetAdapterAdvancedProperty -Name 'Wi-Fi' -DisplayName 'Impulsar la capacidad de proceso' -DisplayValue 'Desactivado' -ErrorAction SilentlyContinue"
powershell -NoProfile -Command "Set-NetAdapterAdvancedProperty -Name 'Wi-Fi' -DisplayName 'Modo de ahorro de energía MIMO' -DisplayValue 'SMPS automático' -ErrorAction SilentlyContinue"
echo   - Adaptador Wi-Fi restaurado a sus valores iniciales de fábrica.

echo.
echo [2/6] Reactivando servicios de Killer Network Suite...
sc config "Killer Network Service" start=auto >nul 2>&1
sc start "Killer Network Service" >nul 2>&1
sc config "Killer Analytics Service" start=auto >nul 2>&1
sc start "Killer Analytics Service" >nul 2>&1
sc config "Killer Wifi Optimization Service" start=demand >nul 2>&1
sc start "Killer Wifi Optimization Service" >nul 2>&1
sc config "KNDBWM" start=demand >nul 2>&1
echo   - Servicios Killer reconfigurados a su estado anterior.

echo.
echo [3/6] Restaurando DNS automaticos (DHCP del router)...
powershell -NoProfile -Command "Set-DnsClientServerAddress -InterfaceAlias 'Wi-Fi' -ResetServerAddresses -ErrorAction SilentlyContinue"
echo   - Servidores DNS asignados nuevamente por DHCP del router.

echo.
echo [4/6] Reactivando componente IPv6 en el adaptador Wi-Fi...
powershell -NoProfile -Command "Enable-NetAdapterBinding -Name 'Wi-Fi' -ComponentID 'ms_tcpip6' -ErrorAction SilentlyContinue"
echo   - Pila IPv6 reactivada.

echo.
echo [5/6] Restaurando pila TCP/IP y Delivery Optimization a valores estándar de Windows...
netsh int tcp set global autotuninglevel=normal >nul 2>&1
netsh int tcp set global rss=default >nul 2>&1
netsh int tcp set supplemental template=internet congestionprovider=default >nul 2>&1
reg delete "HKLM\SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization" /v DODownloadMode /f >nul 2>&1
echo   - Pila TCP/IP y Windows Update P2P restaurados.

echo.
echo [6/6] Vaciando cache DNS y renovando adaptadores...
ipconfig /flushdns >nul 2>&1
powershell -NoProfile -Command "Clear-DnsClientCache"
echo   - Cache DNS limpiada.

echo.
echo ============================================================================
echo   RESTAURACION COMPLETADA: Tu equipo ha vuelto a su configuracion inicial.
echo ============================================================================
echo.
pause
