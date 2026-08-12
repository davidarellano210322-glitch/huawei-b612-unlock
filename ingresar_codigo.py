#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ingresar el codigo de desbloqueo (NCK) del Huawei B612s-51d por API.

Uso:
    python ingresar_codigo.py 1234567890123456

IMPORTANTE:
- Solo quedan 2 intentos. Usa SOLO un codigo que venga de Entel (800 367 626)
  o del que estes 100% seguro. Un codigo equivocado gasta 1 intento.
- El router debe estar encendido con la SIM de la otra compania puesta
  (para que aparezca el bloqueo activo).
"""
import sys, urllib.request

HOST = "192.168.8.1"

def get(path, cookie=None, token=None):
    headers = {"User-Agent":"Mozilla/5.0"}
    if cookie: headers["Cookie"] = cookie
    if token: headers["__RequestVerificationToken"] = token
    req = urllib.request.Request(f"http://{HOST}{path}", headers=headers)
    with urllib.request.urlopen(req, timeout=8) as r:
        return r.read().decode("utf-8","replace")

def main():
    if len(sys.argv) != 2 or not sys.argv[1].isdigit() or len(sys.argv[1]) not in (8, 16):
        print("Uso: python ingresar_codigo.py <codigo de 16 digitos>")
        return
    codigo = sys.argv[1]

    b = get("/api/webserver/SesTokInfo")
    cookie = "SessionID=" + b.split("<SesInfo>")[1].split("</SesInfo>")[0].strip()
    token = b.split("<TokInfo>")[1].split("</TokInfo>")[0].strip()

    # estado actual
    sim = get("/api/pin/simlock", cookie, token)
    import re
    enable = re.search(r"<SimLockEnable>(\d)</SimLockEnable>", sim)
    remain = re.search(r"<SimLockRemainTimes>(\d+)</SimLockRemainTimes>", sim)
    print(f"Estado actual: SimLockEnable={enable.group(1) if enable else '?'}  "
          f"intentos restantes={remain.group(1) if remain else '?'}")

    if enable and enable.group(1) == "0":
        print("El router reporta que NO esta bloqueado. Revisa que este la SIM de la otra compania.")
        return
    if remain and int(remain.group(1)) < 1:
        print("No quedan intentos (hard-lock). Solo se recupera flasheando por USB (kit_flasheo).")
        return

    body = ('<?xml version="1.0" encoding="UTF-8"?>'
            f"<request><SimLockCode>{codigo}</SimLockCode></request>")
    req = urllib.request.Request(f"http://{HOST}/api/pin/verify-simlock", data=body.encode(),
        method="POST",
        headers={"Cookie":cookie,"__RequestVerificationToken":token,
                 "Content-Type":"application/x-www-form-urlencoded","User-Agent":"Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            resp = r.read(600).decode("utf-8","replace")
    except urllib.error.HTTPError as e:
        resp = e.read(600).decode("utf-8","replace")

    print("Respuesta del router:", resp[:300])
    if "<response>OK</response>" in resp:
        print("\n¡CODIGO CORRECTO! El router quedo desbloqueado. Reinicia y lista.")
    else:
        m = re.search(r"<code>(\d+)</code>", resp)
        print(f"\nRespuesta con codigo de error: {m.group(1) if m else '?'}")
        print("Si es 'un error de codigo': el codigo fue rechazado y gastaste 1 intento. NO sigas probando.")
        sim2 = get("/api/pin/simlock", cookie, token)
        r2 = re.search(r"<SimLockRemainTimes>(\d+)</SimLockRemainTimes>", sim2)
        print(f"Intentos restantes ahora: {r2.group(1) if r2 else '?'}")

if __name__ == "__main__":
    main()
