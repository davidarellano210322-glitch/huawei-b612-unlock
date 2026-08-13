# 🔌 Capítulo 14: Protocolos de Conmutación USB, Modos Compuestos y Diagnóstico (AT^SETPORT / AT^GODLOAD)

## 1. Introducción y Arquitectura USB de Huawei Balong
En la plataforma **HiSilicon Balong V7R5 (Hi6950)**, la interfaz USB del módem opera como un **dispositivo compuesto dinámico** (*USB Composite Device* con VID `0x12D1`). 

El módem conmuta sus endpoints y funciones lógicas (puertos serie COM, interfaz de red virtual RNDIS/CDC-NCM, almacenamiento masivo o interfaz de flasheo de bajo nivel) según su modo de arranque y configuración interna.

---

## 2. Mapa de Modos y Descriptores USB (PIDs de Huawei)

```
                       ┌─────────────────────────────────────────┐
                       │     MODOS DE ENUMERACIÓN USB (VID 12D1) │
                       └────────────────────┬────────────────────┘
                                            │
         ┌──────────────────────────────────┼──────────────────────────────────┐
         │                                  │                                  │
         ▼                                  ▼                                  ▼
   [ PID 1443 ]                       [ PID 14DB ]                       [ PID 1506 ]
 Modo Download / BootROM           Modo HiLink Residencial             Modo Depuración / Módem
 • Testpoint (Modo Aguja)          • Interfaz CDC-NCM (Ethernet)      • Puerto PCUI (AT Commands)
 • balong_usbdload (-x 4)          • Servidor Web 192.168.8.1         • Puerto Modem (Datos PPP)
 • 3G PC UI Interface              • Puertos COM Ocultos              • Puerto Diag (Qualcomm/Balong)
```

| Product ID (PID) | Modo Operativo | Interfaces Expuestas en Windows/Linux | Propósito y Función |
| :---: | :--- | :--- | :--- |
| **`PID_1443`** | **Modo Download (BOOT)** | `HUAWEI Mobile Connect - 3G PC UI Interface` | Flasheo de bajo nivel vía `balong_usbdload_x`. |
| **`PID_14DB`** | **Modo HiLink (Stock)** | Interfaz Ethernet Virtual (NDIS) | Modo estándar con WebUI en `192.168.8.1`. |
| **`PID_1506`** | **Modo Módem / Debug** | 3 Puertos Seriales (PCUI, Modem, Diag) | Diagnóstico por comandos AT directos sin WebUI. |
| **`PID_1442`** | **Modo Mass Storage** | Unidad CD-ROM virtual (ISO con drivers) | Instalación automática de controladores. |

---

## 3. Comandos de Conmutación de Puertos (`AT^SETPORT`)

En módems Huawei con acceso a terminal AT, el comando propietario `AT^SETPORT` controla qué interfaces USB se activan en cada modo:

```text
AT^SETPORT?             --> Consulta la configuración actual de puertos
AT^SETPORT=?            --> Lista todos los tipos de interfaces disponibles
AT^SETPORT="FF;1,2,3"   --> Deshabilita modo CD-ROM y fuerza: 1(Diag), 2(PCUI), 3(Modem)
```

### Tabla de Códigos de Interfaz:
* **`1`:** Interfaz de Diagnóstico (Diag / NVRAM Tool).
* **`2`:** Interfaz PCUI (Consola de comandos AT).
* **`3`:** Interfaz Módem (Llamadas de datos y marcado PPP).
* **`10`:** Interfaz NDIS / Red Virtual (HiLink).
* **`A1`:** Unidad virtual de CD-ROM (Mass Storage).
* **`A2`:** Lector de tarjetas MicroSD.

---

## 4. El Comando de Entrada al Bootloader: `AT^GODLOAD`

El firmware Balong incluye la instrucción no documentada `AT^GODLOAD`:
* **Función:** Fuerza al procesador a saltar desde el sistema operativo Linux en ejecución hacia la dirección de la **BootROM en memoria SRAM**, re-enumerando inmediatamente el puerto USB como **`PID_1443` (Modo Download)** sin necesidad de abrir el equipo ni hacer puente físico.
* **Estado en Entel C110:** Dado que el firmware deshabilitó todos los puertos AT serie externos y eliminó los endpoints `/api/system/atcmd`, no es posible inyectar `AT^GODLOAD` por software en esta compilación sin tener acceso Telnet previo.

---

## 5. El Mecanismo de Conmutación por Mensaje SCSI (`usb_modeswitch`)

En sistemas Linux, las tarjetas HiLink alternan del modo CD-ROM (`PID_1442`) al modo módem/red enviando un paquete de control SCSI especial a través de la interfaz de almacenamiento:

```bash
# Mensaje de conmutación estándar Huawei:
55 53 42 43 12 34 56 78 00 00 00 00 00 00 00 11 06 20 00 00 01 00 00 00 00 00 00 00 00 00 00
```

### Por qué no conmuta a puertos serie en el B612s-51d:
En los routers de escritorio (CPE), el kernel Linux embebido asigna el descriptor compuesto fijo `PID_14DB` en el controlador `hiusb` / `dwc_otg`. El driver ignora deliberadamente las solicitudes de conmutación SCSI externas, garantizando que el router permanezca siempre en modo puerta de enlace LAN/Wi-Fi.

---

## 6. Conclusiones y Resumen Arquitectónico

1. **Blindaje de interfaces en firmware C110:** La desactivación de endpoints de diagnóstico y puertos AT impide la conmutación remota por software (`AT^SETPORT` / `AT^GODLOAD`).
2. **El Testpoint como vector maestro:** El puente físico del punto **BOOT a GND** es el único mecanismo capaz de forzar al procesador a arrancar en **`PID_1443`**, permitiendo inyectar el **Shell Loader (`usbloader-b612-shell.bin`)** con el exploit Secuboot (`-x 4`) para anular el bloqueo en la NVRAM.
