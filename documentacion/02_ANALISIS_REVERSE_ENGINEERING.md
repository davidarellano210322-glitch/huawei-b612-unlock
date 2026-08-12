# 🔬 02. Análisis e Ingeniería Inversa

Este documento detalla los hallazgos obtenidos tras el desensamblado, descompilación y análisis binario de los paquetes de firmware, herramientas rusas/iraníes y mecanismos de protección del Huawei B612s-51d.

---

## 1. Desmontaje de la Herramienta "unlock_v7r11_2018-07-14.exe"

En la comunidad de modding de módems 4G (hilos de 4PDA y canales de Telegram) circula la herramienta `unlock_v7r11_2018-07-14.exe` promocionada como "desbloqueador V7R11".

### Análisis Binario y Extracción:
El ejecutable no es un software compilado en C/C++ tradicional ni un calculador de llaves: es un instalador empaquetado con **Indigo Rose Setup Factory**. Al extraer la carga útil (*payload*) interna, se descubrió la estructura real:

```
├── bin/
│   ├── adb.exe             (Android Debug Bridge binario estándar de Google)
│   └── AdbWinApi.dll       (Librería de soporte ADB para Windows)
├── go.cmd                  (Script de ejecución en lote)
└── hideconsole.exe         (Lanzador para ocultar la terminal de comandos)
```

### Contenido del Script `go.cmd`:
```bat
@echo off
bin\adb connect 192.168.8.1:5555
bin\adb shell busybox killall add_param
bin\adb shell "atc AT^NVWREX=8268,0,12,1,0,0,0,2,0,0,0,A,0,0,0"
bin\adb shell "echo -en 'AT^RESET\r' > /dev/appvcom1"
```

### 💡 Hallazgo Clave:
1. **No existe cálculo matemático:** La herramienta **no calcula ningún código NCK** a partir del IMEI.
2. **Dependencia de ADB:** Para que funcione, el router **debe tener abierto el puerto ADB 5555**, el cual **está deshabilitado de fábrica** en el firmware stock de Entel `11.192.00.00.110`.
3. **El verdadero bypass:** Desactiva el proceso vigilante `add_param` y sobreescribe directamente la celda de bloqueo en la partición NVRAM del módem (registro `8268`).

---

## 2. La Realidad de los Algoritmos SIM-Lock (V1 a V5)

| Versión Algoritmo | Módems Compatibles | Método de Obtención / Cálculo |
| :--- | :--- | :--- |
| **V1 (Old Algo)** | E156, E160, E172, E220 | Hash MD5 (`MD5(IMEI + salt)`). Calculable localmente de forma instantánea. |
| **V2 (Algo)** | E1550, E1750, E353 | Hash SHA256 modificado (`SHA256(IMEI + salt)`). Calculable localmente. |
| **V3 / V201 (New Algo)** | E303, E3131, E3272, E3372s | Implementado en herramientas como `huaweicalc` (forth32) y `HMUC`. |
| **V4 / V5** | **B612, B525, B310s, B315s, E5186** | **Criptografía asimétrica vinculada a hardware y Base de Datos del Operador.** No existe algoritmo o calculador offline público. |

### Conclusión sobre el Código NCK:
El código NCK para el algoritmo **V5** no se deriva del IMEI mediante una fórmula matemática estática. Huawei genera los pares de llaves y los entrega en bases de datos a las operadoras telefónicas (en este caso, Entel Chile). El chip Balong valida el código contra un hash cifrado almacenado en su partición segura de hardware.

---

## 3. Análisis de la Herramienta "inst_webui" y Update Local

Se analizó la herramienta `inst_webui_2019-08-01.rar` y el código JavaScript original extraído del WebUI (`update_local.js` y `main.js`):

```javascript
// update_local.js extraído de firmware modificado
function onUpdateSubmit() {
    var filePath = $("#upload_file").val();
    var fileName = filePath.substring(filePath.lastIndexOf("\\") + 1);
    $("#cur_path").val("OU:" + fileName); // "OU" = Online Update
    
    // Envío multipart a /api/filemanager/upload
    document.forms['upload_form'].action = '/api/filemanager/upload';
    document.forms['upload_form'].submit();
}
```

### Mecanismo de Subida:
1. Petición `POST` multipart/form-data al endpoint `/api/filemanager/upload`.
2. Parámetros requeridos:
   * `csrf_token`: Prefijo `csrf:` concatenado con el token CSRF obtenido de `/api/webserver/token`.
   * `cur_path`: `OU:<nombre_archivo.zip>`.
   * `uploadfile`: Payload del firmware en formato ZIP conteniendo el binario `.bin` y la carpeta `ReleaseDoc/`.
3. Polling de progreso en `/api/monitoring/check-notifications` y `/api/online-update/status`.

Se emuló este flujo completo en el script en Python [`webui_update.py`](../webui_update.py), eliminando cualquier dependencia de herramientas `.exe` de origen dudoso.

---

## 4. Análisis de Paquetes de Firmware Disponibles

Se examinaron las imágenes de firmware disponibles en el repositorio:

### A. Firmware Modificado M_AT (Recomendado)
* **Archivo:** `B612_UPDATE_81.201.01.01.234_sec_M_AT_V3.9.bin` (66 MB)
* **Cabecera interna:** `B612__1:81.201.01.01.234`
* **Características:**
  * Telnet habilitado por defecto en puertos `23` y `5510`.
  * Servidor ADB activo en puerto `5555`.
  * Intérprete `atc` disponible para inyección directa de comandos AT al puerto `/dev/appvcom1`.

### B. Firmware Modificado 11.195 (Alternativa FDD)
* **Archivo:** `B612_11.195.03.00.00_moddedv3.bin` (70.5 MB)
* **Cabecera interna:** `B612__0:11.195.03.00.00`
* **Características:**
  * Alta estabilidad en redes 4G FDD (Bands 2/4/7/28).
  * Soporte Telnet en puerto `5510` (root).

### C. Cargador USB Bootrom (Safe Loader)
* **Archivo:** `usbsafe-b612.bin` (7.9 MB)
* **Propósito:** Inicializar la RAM y los controladores de flash cuando el procesador Balong entra en modo de emergencia *Download Mode* (VID_12D1 & PID_1443).

---
[⬅️ Anterior: Estado del Dispositivo](./01_ESTADO_DEL_DISPOSITIVO.md) | [Siguiente: Auditoría WebUI y Endpoints ➡️](./03_AUDITORIA_WEBUI_Y_ENDPOINTS.md)
