#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prueba de acceso por API - Huawei B612s-51d (firmware Entel)
============================================================
Objetivo: ver si con sesión REAL de admin la API del WebUI permite
comandos AT / NVRAM (puerta B) sin flashear nada.

IMPORTANTE (hallazgo de la ronda): el login admin/admin NUNCA estableció
sesión — este firmware usa login SCRAM (extern_password_type=1) y la
contraseña real está en la ETIQUETA (sticker) de la parte inferior del
router, NO es "admin". Todas las pruebas antiguas con admin/admin se
hicieron con sesión FALSA (state-login State=-1). Este script usa el
login SCRAM real de webui_update.Router.

Uso:
    python api_b612.py --password <clave-del-sticker>
    python api_b612.py --password <clave> at "AT^VERSION=INI,B612s-25dCUST-B00C00"
    python api_b612.py --password <clave> --host 192.168.1.1

Requiere la PC conectada al router (192.168.8.x).
"""
import sys
import argparse

import webui_update
from webui_update import Router


def sondeo(r):
    endpoints = [
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
        "/api/config/global",
        "/api/ntwk/lte_info",
        "/api/device/basic_information",
        "/api/upgrade/state",
        "/api/device/control",
        "/api/net/current-plmn",
        "/api/global/operator",
    ]
    print("\n-- SONDEO CON SESION REAL --")
    for ep in endpoints:
        st, resp = r.http("GET", ep)
        txt = resp.decode("utf-8", "replace") if isinstance(resp, bytes) else str(resp)
        one = " ".join(txt.split())[:110]
        marca = "*** VIVO ***" if "100003" not in txt else ""
        print("  %-42s -> %s  %s %s" % (ep, st, one, marca))


def enviar_at(r, comando):
    variantes = [
        "<request><atcmd>%s</atcmd></request>" % comando,
        "<request><cmd>%s</cmd></request>" % comando,
        "<request><command>%s</command></request>" % comando,
        "<request><at>%s</at></request>" % comando,
    ]
    for ep in ["/api/system/atcmd", "/api/atcmd", "/api/device/at",
               "/api/set/atcmd", "/api/ntwk/atcmd", "/api/system/atcommand"]:
        for v in variantes:
            st, resp = r.http("POST", ep, body=v.encode(),
                              headers={"_ResponseSource": "Broswer"})
            txt = resp.decode("utf-8", "replace") if isinstance(resp, bytes) else str(resp)
            one = " ".join(txt.split())[:120]
            if "<response>OK</response>" in txt or "<code>0</code>" in txt:
                print("  *** ¡RESPUESTA POSITIVA! POST %s %r" % (ep, v[:50]))
                return True
            if "100003" not in txt:
                print("  >> POST %-28s -> %s" % (ep, one))
    return False


def main():
    ap = argparse.ArgumentParser(description="API B612s-51d con sesión admin real (SCRAM)")
    ap.add_argument("--password", required=True, help="contraseña admin (sticker del router)")
    ap.add_argument("--username", default="admin")
    ap.add_argument("--host", default=None)
    ap.add_argument("cmd", nargs="?", default=None,
                    help="'at' para enviar un comando AT (o nada para sondeo)")
    ap.add_argument("atcmd", nargs="?", default=None,
                    help="el comando AT (solo con 'at')")
    args = ap.parse_args()

    host = args.host or webui_update.detect_host() or "192.168.8.1"
    print("=== api_b612.py — %s (user=%s, login SCRAM real) ===" % (host, args.username))
    r = Router(host)
    if not r.get_session():
        print("  No se obtuvo sesión. ¿Estás conectado al router?")
        sys.exit(1)

    print("-- LOGIN SCRAM --")
    if not r.login_scram(args.username, args.password):
        print("  Login falló: contraseña incorrecta o aún bloqueado (waittime).")
        print("  Revisa la ETIQUETA (sticker) del router: 'WebUI password' / 'Password'.")
        sys.exit(2)
    print("  Sesión REAL verificada (state-login State=0).\n")

    if args.cmd == "at":
        comando = args.atcmd or "AT^VERSION=INI,B612s-25dCUST-B00C00"
        print("-- ENVIANDO COMANDO AT: %s --" % comando)
        enviar_at(r, comando)
    else:
        sondeo(r)

    print("""
INTERPRETACION:
- Si los endpoints AT siguen en 100003 CON sesión real: el firmware Entel
  los deshabilitó -> no hay puerta B por API.
- Si algún endpoint devuelve datos o <response>OK</response>: hay puerta.
""")


if __name__ == "__main__":
    main()
