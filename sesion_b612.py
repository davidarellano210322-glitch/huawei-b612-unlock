#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sesion_b612.py — Re-test COMPLETO con sesión admin REAL (login SCRAM)
====================================================================
HALLAZGO DE LA RONDA: todas las pruebas anteriores (endpoints 100003,
handlers "muertos", uploads rechazados) se hicieron con una sesión
FALSA: el login admin/admin nunca estableció sesión (el firmware usa
login SCRAM, extern_password_type=1, y la contraseña real está en el
sticker del router, NO es admin).

Con una sesión REAL, los handlers podrían estar VIVOS. Este script:
  1. Login SCRAM (challenge_login + authentication_login, PBKDF2)
  2. Verifica la sesión (state-login State=0)
  3. Re-prueba TODO lo que daba 100003:
     - /api/filemanager/upload (el update local de inst_webui)
     - Endpoints de comando AT (posible desbloqueo SIN flashear)
     - Diagnóstico, módulos, online-update, logout, etc.

Uso:
    python sesion_b612.py --password <contraseña-del-sticker>
    python sesion_b612.py --password <clave> --username user
    python sesion_b612.py --password <clave> --at "AT^NVWREX=8268,0,12,1,0,0,0,2,0,0,0,A,0,0,0"
"""
import sys
import re
import argparse
import urllib.request
import urllib.error
import webui_update
from webui_update import Router, build_multipart


def main():
    ap = argparse.ArgumentParser(description="Re-test con sesión admin real (SCRAM)")
    ap.add_argument("--password", required=True, help="contraseña admin (sticker del router)")
    ap.add_argument("--username", default="admin")
    ap.add_argument("--host", default=None)
    ap.add_argument("--at", default=None, help="enviar un comando AT a los endpoints atcmd")
    args = ap.parse_args()

    host = args.host or webui_update.detect_host() or "192.168.8.1"
    print("=== sesion_b612.py — %s (login SCRAM real) ===" % host)
    r = Router(host)
    if not r.get_session():
        print("  No hay sesión. ¿Router conectado?")
        sys.exit(1)

    print("-- LOGIN SCRAM --")
    if not r.login_scram(args.username, args.password):
        print("  Login falló: contraseña incorrecta o aún bloqueado (waittime).")
        print("  Revisa la ETIQUETA (sticker) del router: 'WebUI password' / 'Password'.")
        sys.exit(2)
    print("  Sesión REAL verificada (state-login State=0).\n")

    if args.at:
        print("-- ENVIAR COMANDO AT --")
        comando = args.at
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
                elif "100003" not in txt:
                    print("  >> POST %-28s -> %s" % (ep, one))
        sys.exit(0)

    print("-- 1) ENDPOINTS DE SUBIDA (update local) --")
    token = r.get_token()
    fields = {"csrf_token": "csrf:" + token[32:], "cur_path": "OU:probe.bin"}
    body = build_multipart(fields, "probe.bin", b"probe", "----SesionProbe")
    hdrs = {"Content-Type": "multipart/form-data; boundary=----SesionProbe",
            "_ResponseSource": "Broswer"}
    for ep in ["/api/filemanager/upload", "/api/update/upgrade-file",
               "/api/upgrade/upload", "/api/device/upgrade"]:
        st, resp = r.http("POST", ep, body=body, headers=hdrs, timeout=30)
        txt = resp.decode("utf-8", "replace") if isinstance(resp, bytes) else str(resp)
        one = " ".join(txt.split())[:110]
        marca = "*** VIVO ***" if "100003" not in txt else ""
        print("  POST %-30s -> %s %s" % (ep, one, marca))

    print("\n-- 2) ENDPOINTS AT / SISTEMA --")
    for ep in ["/api/system/atcmd", "/api/atcmd", "/api/device/at", "/api/set/atcmd",
               "/api/ntwk/atcmd", "/api/system/deviceinfo", "/api/device/control",
               "/api/device/information"]:
        st, resp = r.http("GET", ep)
        txt = resp.decode("utf-8", "replace") if isinstance(resp, bytes) else str(resp)
        one = " ".join(txt.split())[:110]
        marca = "*** VIVO ***" if "100003" not in txt else ""
        print("  GET  %-30s -> %s %s" % (ep, one, marca))

    print("\n-- 3) ESCRITURA / CONFIG --")
    for ep, b in [
        ("/api/global/module-switch", "<request><localupdate_enabled>1</localupdate_enabled></request>"),
        ("/api/user/logout", "<request></request>"),
        ("/api/online-update/check-new-version", "<request></request>"),
    ]:
        st, resp = r.http("POST", ep, body=b.encode(), headers={"_ResponseSource": "Broswer"})
        txt = resp.decode("utf-8", "replace") if isinstance(resp, bytes) else str(resp)
        one = " ".join(txt.split())[:110]
        marca = "*** VIVO ***" if "100003" not in txt else ""
        print("  POST %-30s -> %s %s" % (ep, one, marca))

    print("""
INTERPRETACIÓN:
- Si filemanager/upload o los endpoints AT responden distinto de 100003
  CON SESIÓN REAL: la web NO estaba muerta, solo requería login.
  -> el desbloqueo por web es posible (webui_update.py --password ...)
- Si siguen en 100003 con sesión real: confirmado que la build Entel
  los arrancó de verdad -> USB (kit_flasheo) o NCK de Entel.
""")


if __name__ == "__main__":
    main()
