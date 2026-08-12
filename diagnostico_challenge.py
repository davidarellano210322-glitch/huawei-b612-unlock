#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnostico_challenge.py — diagnóstico SIN GASTAR INTENTOS de login
=================================================================
1) Descarga el /js/main.js del router EN VIVO y extrae la sección del
   login SCRAM (authMsg, salt, nonce) para compararla con la que
   replicamos en webui_update.login_scram().
2) Hace SOLO el challenge_login (que NO cuenta como intento) e imprime
   la respuesta cruda: salt, iterations, servernonce y los campos
   newType/newSalt/newIterations (indican cambio de contraseña en curso).

Uso:  python diagnostico_challenge.py [host]
"""
import sys
import re
import os
import urllib.request
import urllib.error
import gzip

HOST = sys.argv[1] if len(sys.argv) > 1 else "192.168.8.1"


def http(method, path, body=None, cookie=None, token=None):
    url = "http://%s%s" % (HOST, path)
    h = {"User-Agent": "Mozilla/5.0"}
    if cookie:
        h["Cookie"] = cookie
    if token:
        h["__RequestVerificationToken"] = token
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)
    except Exception as e:
        return None, str(e).encode(), {}


def decomp(data):
    try:
        return gzip.decompress(data).decode("utf-8", "replace")
    except Exception:
        return data.decode("utf-8", "replace")


def main():
    print("=== diagnostico_challenge.py — %s ===" % HOST)

    # 1) main.js del router en vivo
    st, data, _ = http("GET", "/js/main.js")
    print("\n-- 1) /js/main.js del router en vivo (HTTP %s, %d bytes) --" % (st, len(data)))
    if st == 200 and len(data) > 500:
        js = decomp(data)
        # extraer la sección del login SCRAM
        m = re.search(r"function login\(destnation.*?startLogoutTimer", js, re.S)
        sec = m.group(0) if m else js
        i = sec.find("challenge_login")
        if i >= 0:
            print("SECCIÓN SCRAM (login -> challenge -> authentication):")
            print(sec[max(0, i - 1500):i + 2500])
        else:
            print("NO se encontró challenge_login en main.js. Primeros 800 chars:")
            print(js[:800])
    else:
        print("  (no se pudo descargar)")

    # 2) challenge_login sin autenticar (no gasta intentos)
    print("\n-- 2) challenge_login (solo reto, NO autentica) --")
    st, data, _ = http("GET", "/api/webserver/SesTokInfo")
    txt = data.decode("utf-8", "replace")
    sid = re.search(r"<SesInfo>(.*?)</SesInfo>", txt, re.S)
    tok = re.search(r"<TokInfo>(.*?)</TokInfo>", txt, re.S)
    cookie = "SessionID=" + sid.group(1).strip() if sid else None
    token = tok.group(1).strip() if tok else None
    print("  SesTokInfo: st=%s cookie=%r token_len=%r" % (st, bool(cookie), len(token) if token else None))

    first_nonce = os.urandom(32).hex()
    body = ('<?xml version="1.0" encoding="UTF-8"?>'
            "<request><username>admin</username><firstnonce>%s</firstnonce>"
            "<mode>1</mode></request>" % first_nonce).encode()
    st, resp, hdrs = http("POST", "/api/user/challenge_login", body=body,
                          cookie=cookie, token=token)
    rtxt = decomp(resp) if isinstance(resp, bytes) else str(resp)
    print("  challenge_login -> HTTP %s" % st)
    print("  Respuesta cruda: %s" % " ".join(rtxt.split()))
    for k, v in hdrs.items():
        if "token" in k.lower():
            print("  Header %s = %s" % (k, v[:60]))

    print("\nInterpretación:")
    print("  - Si la respuesta trae newType/newSalt/newIterations: hay un")
    print("    CAMBIO de contraseña en curso (el proof va con el salt NUEVO).")
    print("  - Si salt/iterations/servernonce difieren del formato que usa")
    print("    login_scram (hex salt, authMsg nonce,servernonce,servernonce),")
    print("    ese es el motivo del 108006.")


if __name__ == "__main__":
    main()
