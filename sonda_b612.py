#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sonda de puertas alternativas - Huawei B612s-51d (firmware Entel)
================================================================
Uso (con la PC CONECTADA al router por cable o WiFi):
    python sonda_b612.py

Prueba:
  1) Puertos TCP comunes (ademas de 5555) en busca de telnet/ssh/adb/otros.
  2) Endpoints ocultos del WebUI (puerto 80) que podrian permitir
     comandos AT o configuracion sin flashear.
  3) La API de sesion/token de Huawei (/api/webserver/SesTokInfo).
"""
import socket
import urllib.request
import urllib.error
import json

HOST = "192.168.8.1"

PUERTOS = [21, 22, 23, 80, 443, 2323, 5000, 5555, 5510, 5540, 6000, 7547, 8080, 8443, 9000, 9999]

ENDPOINTS = [
    "/",
    "/html/index.html",
    "/html/update.html",
    "/html/atcommand.html",
    "/html/atcmd.html",
    "/html/debug.html",
    "/html/network/debug.html",
    "/api/webserver/SesTokInfo",
    "/api/device/information",
    "/api/monitoring/status",
    "/api/system/deviceinfo",
    "/api/system/atcmd",
    "/api/system/atcommand",
    "/api/atcmd",
    "/api/at/command",
    "/api/device/at",
    "/api/ntwk/atcmd",
    "/api/set/atcmd",
    "/api/security/state",
    "/api/user/state-login",
    "/api/user/login",
    "/api/global/config.xml",
    "/api/config/device",
    "/cgi-bin/luci",
    "/cgi-bin/atcmd",
]

def probar_puerto(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        s.connect((HOST, port))
        # si conecta, leemos el banner (si manda algo)
        banner = ""
        try:
            s.settimeout(2)
            banner = s.recv(128).decode("latin1", "replace").strip()
        except Exception:
            pass
        return True, banner
    except Exception:
        return False, ""
    finally:
        s.close()

def probar_endpoint(path):
    url = f"http://{HOST}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            data = r.read(600)
            tipo = r.headers.get("Content-Type", "")
            return r.status, tipo, data[:200]
    except urllib.error.HTTPError as e:
        return e.code, "", b""
    except Exception as e:
        return None, "", str(e).encode()

def main():
    print(f"=== SONDA B612s-51d en {HOST} ===\n")

    print("-- PUERTOS TCP --")
    abiertos = []
    for p in PUERTOS:
        ok, banner = probar_puerto(p)
        estado = "ABIERTO" if ok else "cerrado"
        print(f"  {p:>5}: {estado}" + (f"  banner={banner[:60]!r}" if ok and banner else ""))
        if ok:
            abiertos.append(p)

    print("\n-- ENDPOINTS WEBUI --")
    interesantes = []
    for ep in ENDPOINTS:
        codigo, tipo, data = probar_endpoint(ep)
        if codigo in (200, 401):
            print(f"  {ep:45} -> {codigo}  {tipo[:30]}")
            interesantes.append((ep, codigo, data))
        else:
            print(f"  {ep:45} -> {codigo}")

    print("\n-- RESUMEN --")
    if abiertos:
        print("  Puertos abiertos:", abiertos)
    else:
        print("  Ningun puerto extra abierto (solo lo que responda el 80).")
    if interesantes:
        print("  Endpoints con respuesta:")
        for ep, codigo, data in interesantes:
            txt = data.decode("latin1", "replace")[:150].replace("\n", " ")
            print(f"    {ep} ({codigo}): {txt}")
    else:
        print("  WebUI no responde o sin endpoints ocultos detectados.")

    print("""
INTERPRETACION:
- Si el puerto 5555 responde con "connected": ADB abierto -> prueba
  R0rt1z2/huawei-unlock (CVE-2019-2215) SIN flashear.
- Si algun endpoint de 'atcmd'/'at' responde 200: probar enviar
  AT^VERSION=INI,B612s-25dCUST-B00C00 por POST con token de SesTokInfo.
- Si nada responde: el firmware Entel esta cerrado de fabrica -> M_AT.
""")

if __name__ == "__main__":
    main()
