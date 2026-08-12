#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
intento_login.py — intento de login SCRAM con LOG COMPLETO
===========================================================
Imprime: contraseña exacta usada (repr), reto del servidor (salt,
iterations, servernonce), proof calculado (hex), y la respuesta CRUDA
de authentication_login (con failcount si el servidor lo manda).

Uso:  python intento_login.py [host]
"""
import sys
import re
import os
import hmac
import hashlib
import urllib.request
import urllib.error
import gzip

HOST = sys.argv[1] if len(sys.argv) > 1 else "192.168.8.1"
USERNAME = sys.argv[2] if len(sys.argv) > 2 else "admin"
PASSWORD = sys.argv[3] if len(sys.argv) > 3 else "210322Cd.."


def http(method, path, body=None, cookie=None, token=None):
    url = "http://%s%s" % (HOST, path)
    h = {"User-Agent": "Mozilla/5.0", "_ResponseSource": "Broswer"}
    if cookie:
        h["Cookie"] = cookie
    if token:
        h["__RequestVerificationToken"] = token
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
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
    print("=== intento_login.py — %s ===" % HOST)
    print("usuario   : %r" % USERNAME)
    print("password  : %r  (len %d)" % (PASSWORD, len(PASSWORD)))

    st, data, _ = http("GET", "/api/webserver/SesTokInfo")
    txt = decomp(data)
    sid = re.search(r"<SesInfo>(.*?)</SesInfo>", txt, re.S)
    tok = re.search(r"<TokInfo>(.*?)</TokInfo>", txt, re.S)
    cookie = "SessionID=" + sid.group(1).strip() if sid else None
    token = tok.group(1).strip() if tok else None
    print("\nSesTokInfo -> HTTP %s  token_len=%s" % (st, len(token) if token else None))

    # 1) challenge (no gasta intentos)
    first_nonce = os.urandom(32).hex()
    body = ('<?xml version="1.0" encoding="UTF-8"?>'
            "<request><username>%s</username><firstnonce>%s</firstnonce>"
            "<mode>1</mode></request>" % (USERNAME, first_nonce)).encode()
    st, data, hdrs = http("POST", "/api/user/challenge_login", body=body,
                          cookie=cookie, token=token)
    ctxt = decomp(data)
    print("\nchallenge_login -> HTTP %s" % st)
    print("  %s" % " ".join(ctxt.split()))
    for k, v in hdrs.items():
        if "token" in k.lower():
            print("  header %s -> %s" % (k, v[:70]))
    # adoptar la rotación como hace login_scram (getTokenFromHeader: 32 chars)
    new_tok = None
    for k, v in hdrs.items():
        if k.lower().replace("_", "").endswith("requestverificationtoken"):
            new_tok = v[:32]
            break
    if new_tok:
        print("  token rotado adoptado: %s" % new_tok)
        token = new_tok
    else:
        print("  (sin header de rotación en challenge)")
    salt = re.search(r"<salt>(.*?)</salt>", ctxt, re.S)
    iters = re.search(r"<iterations>(.*?)</iterations>", ctxt, re.S)
    sn = re.search(r"<servernonce>(.*?)</servernonce>", ctxt, re.S)
    if not (salt and iters and sn):
        print("  ¡challenge sin salt/iterations/servernonce! Aborto (no se gastó intento).")
        return
    salt_v, iter_v, sn_v = salt.group(1), int(iters.group(1)), sn.group(1)

    # 2) proof (mismo algoritmo que scram.js del firmware)
    auth_msg = first_nonce + "," + sn_v + "," + sn_v
    salted = hashlib.pbkdf2_hmac("sha256", PASSWORD.encode(),
                                 bytes.fromhex(salt_v), iter_v, dklen=32)
    client_key = hmac.new(salted, b"Client Key", hashlib.sha256).digest()
    stored_key = hashlib.sha256(client_key).digest()
    client_sig = hmac.new(stored_key, auth_msg.encode(), hashlib.sha256).digest()
    proof = bytes(a ^ b for a, b in zip(client_key, client_sig)).hex()
    print("\nproof calculado: %s" % proof)
    print("authMsg        : %s" % auth_msg)

    # 3) authentication (SÍ cuenta como intento)
    body = ('<?xml version="1.0" encoding="UTF-8"?>'
            "<request><clientproof>%s</clientproof><finalnonce>%s</finalnonce></request>"
            % (proof, sn_v)).encode()
    st, data, hdrs = http("POST", "/api/user/authentication_login", body=body,
                          cookie=cookie, token=token)
    atxt = decomp(data)
    print("\nauthentication_login -> HTTP %s" % st)
    print("  %s" % " ".join(atxt.split()))
    for k, v in hdrs.items():
        if "token" in k.lower():
            print("  header %s -> %s" % (k, v[:60]))

    c = re.search(r"<code>(\d+)</code>", atxt)
    cnt = re.search(r"<count>(\d+)</count>", atxt)
    print("\nRESULTADO: código %s%s" % (c.group(1) if c else "?",
                                        (" (fallo #%s de la ventana)" % cnt.group(1)) if cnt else ""))
    if c and c.group(1) == "108006":
        print("  Contraseña rechazada por el router con esta clave EXACTA.")


if __name__ == "__main__":
    main()
