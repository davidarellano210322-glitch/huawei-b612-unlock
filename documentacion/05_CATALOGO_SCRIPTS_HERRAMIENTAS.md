# 🛠️ 05. Catálogo de Scripts y Herramientas Desarrolladas

Este documento describe el conjunto de herramientas en Python y utilidades de bajo nivel creadas a lo largo de la investigación para el diagnóstico, análisis criptográfico y desbloqueo del Huawei B612s-51d.

---

## 📂 Índice de Herramientas

```
├── sesion_b612.py          # Motor de sesión y autenticación SCRAM-SHA256 (RFC 5802)
├── desbloquear_b612.py      # Inyector Telnet para bypass de NVRAM (AT^NVWREX)
├── ingresar_codigo.py      # Enviador seguro de código NCK vía HiLink API
├── webui_update.py         # Emulador autónomo en Python de actualización WebUI
├── sonda_b612.py           # Diagnóstico integral de hardware, SIM y bloqueo
├── endpoints_b612.py       # Escáner y fuzzer de endpoints de la API HiLink
├── ports_deep.py           # Escáner de puertos TCP y servicios locales
├── simwatch.py             # Monitor continuo de eventos y estado de red SIM
└── test_scram.py           # Suite de pruebas unitarias criptográficas SCRAM
```

---

## 1. `sesion_b612.py`
* **Función:** Gestiona la conexión HTTP/HTTPS contra el router implementando la negociación completa del protocolo **SCRAM-SHA256** (RFC 5802).
* **Características:**
  * Manejo automático de cookies de sesión (`SessionID`) y tokens CSRF (`__RequestVerificationToken`).
  * Cálculo criptográfico de `SaltedPassword`, `ClientKey`, `StoredKey`, `ClientSignature` y `ClientProof`.
  * Validación del `ServerProof` retornado por el router para confirmar canal seguro.
* **Uso:**
```python
from sesion_b612 import SesionB612
session = SesionB612("http://192.168.8.1")
session.login("admin", "admin")
response = session.get("/api/device/information")
```

---

## 2. `desbloquear_b612.py`
* **Función:** Conexión automatizada a los puertos de diagnóstico Telnet (`23` y `5510`) habilitados en firmwares modificados (familia M_AT) para anular el bloqueo en NVRAM.
* **Comando inyectado:**
```text
atc at^nvwrex=8268,0,12,1,0,0,0,2,0,0,0,a,0,0,0
```
* **Uso:**
```bash
python desbloquear_b612.py
```

---

## 3. `ingresar_codigo.py`
* **Función:** Envío seguro del código NCK oficial a través del endpoint `/api/pin/simlock`.
* **Protecciones:**
  * Valida que el código sea numérico antes de realizar la petición.
  * Verifica el número de intentos restantes antes de disparar el POST para evitar bloqueos accidentales.
* **Uso:**
```bash
python ingresar_codigo.py 12345678
```

---

## 4. `webui_update.py`
* **Función:** Reemplazo multiplataforma en Python puro para la herramienta cerrada `inst_webui.exe`.
* **Capacidades:**
  * Modo de prueba (`--probe`): Verifica si el handler multipart `/api/filemanager/upload` responde en el firmware.
  * Modo de subida: Empaqueta el archivo ZIP con las cabeceras requeridas (`cur_path=OU:<nombre>`, `csrf_token`) y realiza seguimiento en tiempo real del progreso de actualización.
* **Uso:**
```bash
# Comprobar si el firmware soporta actualización web
python webui_update.py --probe

# Subir archivo de firmware
python webui_update.py --file B612-51d_UPDATE_81.201.01.01.234_M_AT_V3.9_para_web.zip
```

---

## 5. `sonda_b612.py`
* **Función:** Extracción completa de información de telemetría del router en formato estructurado.
* **Salida generada:** Estado de SIM, versión de algoritmo SIM-Lock, conteo de intentos, nivel de señal RSSI/RSRP, tipo de red y estado de conexión WAN.
* **Uso:**
```bash
python sonda_b612.py
```

---

## 6. `simwatch.py`
* **Función:** Monitor en segundo plano que escucha y registra cada cambio de estado en la interfaz celular cuando se inserta o retira una tarjeta SIM.
* **Uso:**
```bash
python simwatch.py
```

---
[⬅️ Anterior: Guías de Desbloqueo](./04_GUIAS_DE_DESBLOQUEO_VIABLES.md) | [Siguiente: Cronología de la Investigación ➡️](./06_CRONOLOGIA_E_HISTORIAL_INVESTIGACION.md)
