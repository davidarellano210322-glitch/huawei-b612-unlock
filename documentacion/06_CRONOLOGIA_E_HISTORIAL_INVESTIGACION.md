# 📅 06. Cronología e Historial de la Investigación

Esta bitácora recopila cronológicamente los hitos, hipótesis planteadas, pruebas ejecutadas, fallos analizados y descubrimientos concluyentes durante el desarrollo del proyecto.

---

## 📌 Hito 1: Superación de la Barrera de Autenticación SCRAM-SHA256
* **Situación Inicial:** Los scripts genéricos de la comunidad (`unlock_b310s.py`) fallaban con errores `100006` y `108006` al intentar autenticarse con esquemas antiguos basados en hashes MD5 y SHA256 simple.
* **Hipótesis:** El router implementa la nueva arquitectura de seguridad HiLink V5 basada en RFC 5802.
* **Acción:**
  * Se analizó el tráfico entre el navegador y el router en `/api/user/challenge_login` y `/api/user/authentication_login`.
  * Se desarrolló la suite criptográfica [`test_scram.py`](../test_scram.py) para simular PBKDF2 de 100 iteraciones con sal hex y cálculo de pruebas ClientProof / ServerProof.
* **Resultado:** **Éxito.** Se creó el cliente autónomo [`sesion_b612.py`](../sesion_b612.py), logrando acceso programático 100% confiable a la API de administración.

---

## 📌 Hito 2: Diagnóstico en Vivo y Detección de Estado Crítico
* **Acción:** Se ejecutaron llamadas de diagnóstico con la SIM del operador WOM insertada.
* **Hallazgo:**
  * Chip WOM reconocido sin PIN (`SimState = 257`).
  * Bloqueo de red activo (`SimLockEnable = 1`, `SimLockVersion = 5`).
  * Conexión rechazada (`ConnectionStatus = 902`).
  * **Alerta Crítica:** `SimLockRemainTimes = 2` (solo 2 intentos restantes de los 10 originales).
* **Decisión Estratégica:** Prohibir cualquier intento de fuerza bruta o prueba ciega de códigos calculados para evitar el bloqueo permanente (*hard-lock*) del chip módem.

---

## 📌 Hito 3: Ingeniería Inversa de "unlock_v7r11" y Desmitificación V5
* **Hipótesis:** Comprobar si las utilidades distribuidas en foros rusos calculaban el código V5 localmente.
* **Acción:**
  * Desempaquetado del archivo binario `unlock_v7r11_2018-07-14.exe` (Setup Factory).
  * Inspección del script `go.cmd` y binarios internos.
* **Descubrimiento:**
  * La herramienta contenía únicamente un cliente ADB estándar (`adb.exe`) y ejecutaba `killall add_param` seguido de `atc at^nvwrex=8268,0,12,1,0,0,0,2,0,0,0,A,0,0,0`.
  * **Conclusión:** No existe calculador de algoritmos V5. El autor ruso utilizó el mismo bypass de NVRAM porque el código NCK no es derivable matemáticamente fuera de las bases de datos de Huawei / Entel.

---

## 📌 Hito 4: Hallazgo de la Base de Datos de Entel y Marco Legal Subtel
* **Investigación:**
  * Búsqueda en repositorios académicos chilenos del instructivo oficial de Entel para el módem B612 (*"Habilitación BAM B612"*, Universidad Católica de la Santísima Concepción).
  * El instructivo confirmó que el código NCK se consulta directamente en el sistema interno de Entel (*entéraT*) ingresando el IMEI.
  * Análisis de la normativa de la **Subsecretaría de Telecomunicaciones (SUBTEL Chile)**: Las operadoras tienen la obligación legal de entregar el código de desbloqueo de red sin costo alguno para cualquier equipo, sin exigir boleta ni contrato vigente.

---

## 📌 Hito 5: Auditoría Exhaustiva del Vector de Actualización WebUI
* **Hipótesis:** Determinar si era posible inyectar un firmware modificado (M_AT) a través del mecanismo de actualización local del WebUI sin abrir el equipo físicamente.
* **Acción:**
  * Desarrollo del emulador [`webui_update.py`](../webui_update.py) con soporte multipart para `/api/filemanager/upload` y cabeceras `cur_path=OU:<file>`.
  * Verificación en vivo contra el router real `192.168.8.1`.
* **Resultado:**
  * El endpoint `/api/filemanager/upload` retornó error `100003` de forma inmediata.
  * Escaneo de 15 rutas de subida alternativas: todas deshabilitadas en la compilación `11.192.00.00.110` (CUST-C110).
  * **Veredicto:** El vector WebUI está sellado de fábrica en el firmware Entel.

---

## 📌 Hito 6: Estructuración del Kit de Flasheo USB y Cierre Técnico
* **Acción:**
  * Organización de la cadena de herramientas de bajo nivel en [`kit_flasheo/`](../kit_flasheo/): `balong_usbdload.exe`, `balong_flash.exe`, cargador `usbsafe-b612.bin` y firmwares verificados `81.201 M_AT` y `11.195 modded`.
  * Creación del script [`desbloquear_b612.py`](../desbloquear_b612.py) para automatizar la inyección de comandos AT por Telnet post-flasheo.
  * Creación de la suite completa de documentación técnica lista para publicación en GitHub.

---
[⬅️ Anterior: Catálogo de Scripts](./05_CATALOGO_SCRIPTS_HERRAMIENTAS.md) | [Siguiente: Fuentes y Referencias ➡️](./07_FUENTES_Y_REFERENCIAS.md)
