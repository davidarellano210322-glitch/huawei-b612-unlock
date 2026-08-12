# 🛡️ 03. Auditoría de Seguridad WebUI y Endpoints HiLink

Este documento registra la auditoría de seguridad realizada sobre la interfaz web (HiLink API) del router **Huawei B612s-51d** con firmware de fábrica de Entel Chile (`11.192.00.00.110`), detallando los endpoints sondeados, respuestas XML y puertos abiertos.

---

## 1. Escaneo de Puertos de Red

Se realizó un escaneo profundo sobre la dirección IP de gestión del router (`192.168.8.1`):

| Puerto | Protocolo / Servicio | Estado | Comportamiento en Build Entel C110 |
| :--- | :--- | :--- | :--- |
| **53** | DNS / dnsmasq | **ABIERTO** | Servidor DNS local para resolución de `hilink.net` y `router.huawei`. |
| **80** | HTTP / WebUI | **ABIERTO** | Servidor web principal HiLink. Requiere autenticación SCRAM. |
| **443** | HTTPS / TLS | **ABIERTO** | Acceso web cifrado con certificado autofirmado de Huawei. |
| **23** | Telnet Estándar | **CERRADO** | Bloqueado de fábrica por reglas de firewall iptables. |
| **5510** | Telnet Shell de Diagnóstico | **CERRADO** | Inactivo en firmware oficial de producción. |
| **5555** | ADB (Android Debug Bridge) | **CERRADO** | Inactivo. daemon `adbd` no iniciado. |
| **54321** | Config Update Listener | **CERRADO** | Inactivo. |

---

## 2. Matriz de Endpoints HiLink Auditados

Se diseñaron herramientas automatizadas ([`endpoints_b612.py`](../endpoints_b612.py) y [`sonda_b612.py`](../sonda_b612.py)) para mapear todas las rutas de la API bajo sesión autenticada de administrador.

### A. Endpoints de Diagnóstico y Estado (Activos)

| Endpoint | Método | Código Respuesta | Datos Obtenidos |
| :--- | :--- | :--- | :--- |
| `/api/webserver/SesTokInfo` | GET | `200 OK` | Cookie `SessionID` y token CSRF inicial para handshake. |
| `/api/user/challenge_login` | POST | `200 OK` | Sal y Server Nonce para cálculo SCRAM-SHA256. |
| `/api/user/authentication_login` | POST | `200 OK` | Validación de credenciales admin y confirmación de sesión. |
| `/api/device/information` | GET | `200 OK` | Versión `11.192.00.00.110`, IMEI `864596030624094`, DeviceName `B612s-51d`. |
| `/api/monitoring/status` | GET | `200 OK` | Estado de conexión `902` (desconectado por bloqueo SIM), nivel de señal. |
| `/api/pin/status` | GET | `200 OK` | `SimState = 257` (SIM detectada lista sin código PIN). |
| `/api/pin/simlock` | GET | `200 OK` | `SimLockEnable = 1`, `SimLockRemainTimes = 2`, `SimLockVersion = 5`. |

### B. Endpoints de Actualización y Subida de Firmware (Bloqueados / Stripped)

| Endpoint | Método | Código de Error | Causa Técnica |
| :--- | :--- | :--- | :--- |
| `/api/filemanager/upload` | POST Multipart | `<error><code>100003</code></error>` | **Handler no soportado.** La compilación de Entel C110 deshabilitó el módulo `filemanager` del backend. |
| `/api/update/upgrade-file` | POST Multipart | `100003` | No implementado en el webserver. |
| `/api/upgrade/upgrade-file` | POST Multipart | `100003` | No implementado en el webserver. |
| `/api/device/upgrade` | POST | `100003` | No implementado en el webserver. |
| `/upload` / `/cgi-bin/upgrade` | POST | `100003` / `404 Not Found` | Rutas legacy eliminadas. |

### C. Subsistema de Actualización en Línea (Online-Update)

| Endpoint | Método | Respuesta | Diagnóstico |
| :--- | :--- | :--- | :--- |
| `/api/online-update/status` | GET | `<CurrentComponentStatus>13</CurrentComponentStatus>` | Estado `13` = `QUERY_FAILED` (no hay conexión a Internet). |
| `/api/online-update/url-list` | GET | `<error><code>100001</code></error>` | Sin servidores de actualización configurados accesibles. |
| `/api/online-update/check-new-version` | POST | `<error><code>125003</code></error>` | Rechazado por falta de conectividad WAN. |
| `/api/online-update/forceupdate-config` | POST | `<error><code>100003</code></error>` | Bloqueado para usuario administrador. |

---

## 3. Conclusión de la Auditoría WebUI

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          VEREDICTO WEBUI                                │
│                                                                         │
│  ❌ La vía de actualización local o desbloqueo por navegador web está   │
│     TOTALMENTE CERRADA en la versión 11.192.00.00.110 (Entel CUST-C110).│
│                                                                         │
│  • Todos los handlers multipart retornan error 100003 en 0 segundos.    │
│  • Los binarios internos no procesan archivos cargados vía HTTP.        │
│  • El router requiere intervención por Hardware (USB DLOAD) o NCK.      │
└─────────────────────────────────────────────────────────────────────────┘
```

---
[⬅️ Anterior: Análisis e Ingeniería Inversa](./02_ANALISIS_REVERSE_ENGINEERING.md) | [Siguiente: Guías de Desbloqueo Viables ➡️](./04_GUIAS_DE_DESBLOQUEO_VIABLES.md)
