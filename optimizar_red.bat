@echo off
:: ============================================================================
:: OPTIMIZADOR DE RED, DNS Y WI-FI PARA MAXIMA VELOCIDAD Y ESTABILIDAD
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
color 0B
echo ============================================================================
echo      OPTIMIZANDO CONEXION, DNS, WI-FI 6 Y RENDIMIENTO DE RED
echo ============================================================================
echo.

echo [1/7] Deshabilitando servicios conflictivos de Killer Network Suite...
sc stop "Killer Network Service" >nul 2>&1
sc config "Killer Network Service" start=disabled >nul 2>&1
sc stop "Killer Analytics Service" >nul 2>&1
sc config "Killer Analytics Service" start=disabled >nul 2>&1
sc stop "Killer Wifi Optimization Service" >nul 2>&1
sc config "Killer Wifi Optimization Service" start=disabled >nul 2>&1
sc stop "KNDBWM" >nul 2>&1
sc config "KNDBWM" start=disabled >nul 2>&1
echo   - Servicios de throttling e inspeccion Killer desactivados.

echo.
echo [2/7] Optimizando parametros avanzados del adaptador Intel Wi-Fi 6 AX201...
powershell -NoProfile -Command "Set-NetAdapterAdvancedProperty -Name 'Wi-Fi' -DisplayName 'Agresividad de itinerancia' -DisplayValue '1. Mínimo' -ErrorAction SilentlyContinue"
powershell -NoProfile -Command "Set-NetAdapterAdvancedProperty -Name 'Wi-Fi' -DisplayName 'Banda preferida' -DisplayValue '3. Preferencia de banda 5 GHz' -ErrorAction SilentlyContinue"
powershell -NoProfile -Command "Set-NetAdapterAdvancedProperty -Name 'Wi-Fi' -DisplayName 'Impulsar la capacidad de proceso' -DisplayValue 'Activado' -ErrorAction SilentlyContinue"
powershell -NoProfile -Command "Set-NetAdapterAdvancedProperty -Name 'Wi-Fi' -DisplayName 'Modo de ahorro de energía MIMO' -DisplayValue 'Sin SMPS' -ErrorAction SilentlyContinue"
echo   - Wi-Fi 6 configurado: Itinerancia Minima, Banda 5GHz forzada, Throughput Booster activado, MIMO sin ahorro.

echo.
echo [3/7] Asignando Servidores DNS de Ultra-Baja Latencia (Cloudflare + Google)...
powershell -NoProfile -Command "Set-DnsClientServerAddress -InterfaceAlias 'Wi-Fi' -ServerAddresses @('1.1.1.1', '1.0.0.1', '8.8.8.8') -ErrorAction SilentlyContinue"
echo   - DNS asignados: Primario 1.1.1.1, Secundario 1.0.0.1, Respaldo 8.8.8.8

echo.
echo [4/7] Optimizando Pila TCP/IP de Windows para Minimo Jitter y Maxima Velocidad...
netsh int tcp set global autotuninglevel=normal >nul 2>&1
netsh int tcp set global rss=enabled >nul 2>&1
netsh int tcp set global fastopen=enabled >nul 2>&1
netsh int tcp set global timestamps=allowed >nul 2>&1
netsh int tcp set global initialRto=2000 >nul 2>&1
netsh int tcp set supplemental template=internet congestionprovider=cubic >nul 2>&1
echo   - TCP Auto-Tuning, RSS, Fast Open y Congestion CUBIC activados.

echo.
echo [5/7] Eliminando retardos por timeout IPv6 y rutas fantasma...
powershell -NoProfile -Command "Disable-NetAdapterBinding -Name 'Wi-Fi' -ComponentID 'ms_tcpip6' -ErrorAction SilentlyContinue"
powershell -NoProfile -Command "Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | Where-Object { $_.InterfaceAlias -ne 'Wi-Fi' } | ForEach-Object { Remove-NetRoute -InterfaceIndex $_.InterfaceIndex -DestinationPrefix '0.0.0.0/0' -Confirm:$false -ErrorAction SilentlyContinue }"
echo   - IPv6 deshabilitado en Wi-Fi para evitar demoras de 2 seg en resolucion AAAA.
echo   - Rutas residuales limpiadas.

echo.
echo [6/7] Desactivando subida P2P de Windows Update en segundo plano...
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization" /v DODownloadMode /t REG_DWORD /d 0 /f >nul 2>&1
echo   - P2P Delivery Optimization desactivado.

echo.
echo [7/7] Vaciando cache DNS y renovando registros...
ipconfig /flushdns >nul 2>&1
powershell -NoProfile -Command "Clear-DnsClientCache"
echo   - Cache DNS limpiada.

echo.
echo ============================================================================
echo   TODO LISTO: Tu red y Wi-Fi han sido optimizados a su maximo rendimiento.
echo ============================================================================
echo.
pause
