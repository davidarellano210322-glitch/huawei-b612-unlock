# 📡 Dossier de Documentación: Desbloqueo Huawei B612s-51d (Entel Chile)

> **Proyecto:** Análisis de Seguridad, Ingeniería Inversa y Métodos de Desbloqueo de Red (SIM-Lock V5) para Router 4G LTE Huawei B612s-51d (Compilación CUST-C110 de Entel Chile).

---

## 🗂️ Índice de Módulos Documentales

| N° | Documento | Descripción / Contenido |
| :---: | :--- | :--- |
| **01** | [📱 01_ESTADO_DEL_DISPOSITIVO.md](./01_ESTADO_DEL_DISPOSITIVO.md) | Especificaciones de hardware, versión de firmware C110, telemetría de la SIM WOM y arquitectura criptográfica SCRAM-SHA256. |
| **02** | [🔬 02_ANALISIS_REVERSE_ENGINEERING.md](./02_ANALISIS_REVERSE_ENGINEERING.md) | Desensamblado de `unlock_v7r11`, mitos de los algoritmos V5, desmontaje de `inst_webui` y bypass por NVRAM. |
| **03** | [🛡️ 03_AUDITORIA_WEBUI_Y_ENDPOINTS.md](./03_AUDITORIA_WEBUI_Y_ENDPOINTS.md) | Auditoría exhaustiva de más de 40 endpoints HiLink, pruebas multipart y diagnóstico del error 100003. |
| **04** | [🚀 04_GUIAS_DE_DESBLOQUEO_VIABLES.md](./04_GUIAS_DE_DESBLOQUEO_VIABLES.md) | Guías paso a paso: Modo Aguja (Flasheo USB + Telnet AT) y Procedimiento Legal Subtel para código NCK oficial. |
| **05** | [🛠️ 05_CATALOGO_SCRIPTS_HERRAMIENTAS.md](./05_CATALOGO_SCRIPTS_HERRAMIENTAS.md) | Manual de uso y parámetros de cada script desarrollado en Python (`sesion_b612.py`, `desbloquear_b612.py`, etc.). |
| **06** | [📅 06_CRONOLOGIA_E_HISTORIAL_INVESTIGACION.md](./06_CRONOLOGIA_E_HISTORIAL_INVESTIGACION.md) | Bitácora de la investigación día a día: hipótesis, pruebas de laboratorio, errores encontrados y conclusiones. |
| **07** | [📚 07_FUENTES_Y_REFERENCIAS.md](./07_FUENTES_Y_REFERENCIAS.md) | Referencias de foros 4PDA, comunidad Capa9 Chile, instructivo oficial UCSC/Entel y normativa Subtel. |
| **08** | [🧬 08_EXPLOIT_SECUBOOT_Y_ECOSISTEMA_BALONG.md](./08_EXPLOIT_SECUBOOT_Y_ECOSISTEMA_BALONG.md) | Análisis del exploit Secuboot Bypass (`-x`), comparación con PotatoNV, mapa NVRAM `nvid.c` y arquitectura Hi6950. |
| **09** | [🐚 09_SHELL_LOADER_V7R5_Y_BACKUP_NVRAM.md](./09_SHELL_LOADER_V7R5_Y_BACKUP_NVRAM.md) | Construcción del Shell Loader V7R5 autónomo en RAM, volcado completo de NVRAM y decodificación real del ítem 8268. |
| **10** | [🧪 10_PRUEBA_SHELL_LOADER_EN_HARDWARE.md](./10_PRUEBA_SHELL_LOADER_EN_HARDWARE.md) | Guía práctica de prueba del Shell Loader en el B612 real: testpoint, carga con `-x 4`, consolas y diagnóstico. |
| **11** | [🔍 11_VERIFICACION_UNLOCK_V7R11.md](./11_VERIFICACION_UNLOCK_V7R11.md) | Análisis forense de `unlock_v7r11`: se confirma que NO contiene algoritmo V5 — es un cliente ADB de escritura NVRAM. |
| **12** | [🛡️ 12_AUDITORIA_AVANZADA_VECTORES_SOFTWARE.md](./12_AUDITORIA_AVANZADA_VECTORES_SOFTWARE.md) | Auditoría en vivo de SCRAM Huawei (inversión de claves), fuzzing de inyección de diagnóstico y análisis de TR-069/CWMP. |
| **13** | [🧬 13_ANALISIS_AVANZADO_APN_HOTA_Y_PARTICIONES.md](./13_ANALISIS_AVANZADO_APN_HOTA_Y_PARTICIONES.md) | Inyección AT en perfiles APN, arquitectura de firmas HOTA, particiones NAND y arquitectura dual-core AP/CP. |

---

## 📊 Resumen Rápido del Estado del Dispositivo

* **Modelo:** Huawei B612s-51d (SoC HiSilicon Balong 711 / V7R5 Hi6950)
* **IMEI:** `864596030624094`
* **Firmware:** `11.192.00.00.110` (Entel Chile CUST-B00C110)
* **Estado SIM-Lock:** Activo (`SimLockEnable=1`, `SimLockVersion=5`)
* **Intentos Restantes:** **2 intentos críticos** (`SimLockRemainTimes=2`) ⚠️ **NO PROBAR CÓDIGOS AL AZAR**
* **Veredicto WebUI:** Endpoints de upload despojados (`100003`). Flasheo web cerrado sin hardware previo.

---
[🏠 Volver al README Principal](../README.md)
