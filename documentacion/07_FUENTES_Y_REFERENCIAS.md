# 📚 07. Fuentes, Referencias y Créditos de la Investigación

Este documento compila las fuentes comunitarias, documentación oficial, referencias técnicas y repositorios consultados a lo largo del proceso de investigación e ingeniería inversa.

---

## 🌐 1. Foros Especializados y Comunidad

### Foro 4PDA (Rusia)
* **Temas Principales:** Módems y Routers 4G Huawei basados en chipset Balong V7R11 (B612, B525, B528, E5186).
* **Aportes Relevantes:**
  * **forth32 / rust33:** Desarrollo original de las utilidades de flasheo de bajo nivel `balong_flash` y `balong_usbdload`.
  * **aomsk:** Confirmación del procedimiento de testpoint y flasheo USB exitoso en la variante **B612s-51d**.
  * **TOMCAT:** Diferencias de ruteo de pistas en PCB entre las variantes `-25d` y `-51d`.
  * **Valikov:** Compilaciones de firmware modificado de la serie **M_AT** con soporte Telnet y ADB activo.

### Comunidad Capa9.net (Chile)
* **Hilo:** *"Algún mod para B612 de Entel"*
* **Aportes:**
  * Fotografías del punto Testpoint / BOOT específico para la versión comercializada por Entel Chile.
  * Reporte del usuario **gonzalo bahia** respecto a la pérdida de configuración de NVRAM al ejecutar Factory Reset post-desbloqueo.

---

## 📦 2. Canales de Distribución y Archivos de Telegram

* **Canal `t.me/huaweiunlock`:**
  * `1.USB Safe Loader.zip` (Cargador seguro de RAM `usbsafe-b612.bin`).
  * `B612_UPDATE_81.201.01.01.234_sec_M_AT_V3.9.bin` (Firmware con herramientas AT).
  * `flash_via_balongflash_2018-06-11.rar` (Toolchain de flasheo USB).
* **Canal `t.me/modem_land`:**
  * Repositorio de firmwares WebUI y utilidades para módems Balong 711 / 722.

---

## 🏛️ 3. Documentación Oficial y Marco Normativo

### Instructivo Oficial Entel Chile
* **Documento:** *Instructivo Habilitación BAM Huawei B612*
* **Fuente:** Repositorio Oficial UCSC (Universidad Católica de la Santísima Concepción)  
  `https://sitios.ucsc.cl/dae/wp-content/uploads/sites/31/2020/05/INSTRUCTIVO-HABILITACIÓN-BAM-B612.pdf`
* **Revelación:** Procedimiento interno donde Entel almacena y entrega los códigos NCK asociados unívocamente al IMEI del equipo.

### Subsecretaría de Telecomunicaciones (SUBTEL Chile)
* **Normativa:** *Reglamento de Desbloqueo y Homologación de Equipos Terminales Móviles*
* **Derecho del Usuario:** Todo operador en Chile está obligado a suministrar el código de desbloqueo de red de forma gratuita, expedita y sin condiciones contractuales.
* **Portal de Denuncias:** [Reclamos Subtel](https://reclamos.subtel.gob.cl)

---
[⬅️ Anterior: Cronología de la Investigación](./06_CRONOLOGIA_E_HISTORIAL_INVESTIGACION.md) | [Volver al README Principal 🏠](./README.md)
