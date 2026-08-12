#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper de desbloqueo Huawei B612s-51d (Entel Chile)
====================================================
USAR SOLO DESPUÉS de instalar el firmware M_AT por la web del router:
    B612-25d_UPDATE_11.192.05.00.00_M_AT.zip

Uso:
    python desbloquear_b612.py

Prueba telnet en 192.168.8.1 y 192.168.1.1 (puertos 23 y 5510).
En cuanto conecta, envía el comando que quita el SIM-Lock de la NVRAM.
Después apaga/enciende el router (corte de corriente breve) y listo.

Notas:
- NO gasta los intentos de desbloqueo (escribe la NVRAM directamente,
  no usa la página de código NCK).
- Si no conecta: confirma que la versión del router ya es 11.192.05.00.00
  (192.168.8.1 -> Configuración -> Versión de software).
- Alternativa manual:  adb connect 192.168.8.1:5555  ->  adb shell
  y dentro del shell:  atc at^nvwrex=8268,0,12,1,0,0,0,2,0,0,0,a,0,0,0
"""

import sys
import time


def intentar_telnet(host, port):
    try:
        import telnetlib
        t = telnetlib.Telnet(host, port, timeout=8)
        print(f"[OK] Telnet conectado a {host}:{port}")
        return t
    except Exception as e:
        print(f"[--] {host}:{port} -> {e}")
        return None


def main():
    print("=== Desbloqueo B612s-51d (firmware M_AT) ===")
    comando = b"atc at^nvwrex=8268,0,12,1,0,0,0,2,0,0,0,a,0,0,0\n"

    t = None
    for host in ("192.168.8.1", "192.168.1.1"):
        for port in (23, 5510):
            t = intentar_telnet(host, port)
            if t:
                break
        if t:
            break

    if not t:
        print("\nNo se pudo conectar por telnet.")
        print("-> ¿El firmware M_AT quedó instalado? Revisa la versión en 192.168.8.1")
        print("-> Intenta con Putty: telnet 192.168.8.1 (o 192.168.1.1), puerto 23")
        print("-> O por adb: adb connect 192.168.8.1:5555  y luego  adb shell")
        sys.exit(1)

    time.sleep(1)
    try:
        t.write(b"\n")
        time.sleep(1)
        print("\nEnviando: " + comando.decode().strip())
        t.write(comando)
        time.sleep(4)
        out = t.read_very_eager().decode(errors="replace")
        print("Respuesta:")
        print(out)
    finally:
        try:
            t.close()
        except Exception:
            pass

    print("""
===========================================================
Hecho. Ahora:
1) Apaga el router de la corriente y vuelve a encenderlo.
2) Espera a que prenda (1-2 min) y pon una SIM de otra compañía.
3) Entra a 192.168.8.1 y comprueba que ya no pide código de desbloqueo.
Si sigue pidiendo código, NO pruebes códigos al azar (quedan 2 intentos):
   llama a Entel al 800 367 626 y pide el NCK con tu IMEI (gratis).
===========================================================
""")


if __name__ == "__main__":
    main()
