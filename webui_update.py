#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
webui_update.py — Actualización LOCAL por WebUI para Huawei B612s-51d
====================================================================
Replica EXACTAMENTE el mecanismo que usa la herramienta "WEB UI Exe
setup" / inst_webui_2019-08-01.rar del canal t.me/huaweiunlock:

  1. Sesión + login (SesTokInfo -> token -> /api/user/login)
  2. POST multipart al endpoint de subida del WebUI genérico:
        /api/filemanager/upload
     con los campos que manda update_local.js del firmware completo:
        csrf_token = "csrf:" + <token de api/webserver/token>
        cur_path   = "OU:" + <nombre del archivo>
        uploadfile = <el zip>
  3. Polling de estado: /api/monitoring/check-notifications y
     /api/online-update/status (OnlineUpdateStatus / CurrentComponentStatus)

El WebUI genérico acepta .zip o .bin. Se sube el ZIP preparado:
   B612-51d_UPDATE_81.201.01.01.234_M_AT_V3.9_para_web.zip
(bin Mod3-9 con cabecera B612__1:81.201.01.01.234 + ReleaseDoc).

Uso:
    python webui_update.py                    # sube el zip preparado
    python webui_update.py --probe            # solo verifica si el handler vive
    python webui_update.py --file ruta.zip    # sube otro archivo
    python webui_update.py --host 192.168.1.1 # otra IP del router

Códigos de estado (misma tabla que update.js / update_local.js):
    10 IDLE | 11 QUERYING | 12 NEWVERSION | 13 QUERY_FAILED | 14 UP_TO_DATE
    20 DOWNLOAD_FAILED | 30 DOWNLOAD_PROGRESSING | 31 PENDING | 40 COMPLETE
    50 READYTO_UPDATE | 52 START_UPDATE | 60 PROGRESSING (instalando)
    70/80 FAILED (con/sin datos) | 90/100 SUCCESS (con/sin datos)

Requiere la PC conectada al router (192.168.8.x por defecto).
"""
import sys
import re
import os
import time
import hmac
import hashlib
import argparse
import urllib.request
import urllib.error
import io

DEFAULT_HOST = "192.168.8.1"
USER = "admin"
PASS = "admin"
DEFAULT_FILE = "B612-51d_UPDATE_81.201.01.01.234_M_AT_V3.9_para_web.zip"

STATUS = {
    10: "IDLE", 11: "QUERYING", 12: "NEW_VERSION_FOUND", 13: "QUERY_FAILED",
    14: "UP_TO_DATE", 20: "DOWNLOAD_FAILED", 30: "DOWNLOAD_PROGRESSING",
    31: "DOWNLOAD_PENDING", 40: "DOWNLOAD_COMPLETE", 50: "READY_TO_UPDATE",
    52: "START_UPDATE", 60: "PROGRESSING (instalando)", 70: "FAILED_HAVEDATA",
    80: "FAILED_NODATA", 90: "SUCCESS_HAVEDATA", 100: "SUCCESS_NODATA",
}


def sha256_hex(s):
    return hashlib.sha256(s.encode()).hexdigest()


def build_multipart(fields, filename, filebytes, boundary):
    """Arma un body multipart/form-data como el de jquery.form."""
    out = io.BytesIO()
    bnd = boundary.encode()
    for name, value in fields.items():
        out.write(b"--" + bnd + b"\r\n")
        out.write(b'Content-Disposition: form-data; name="%s"\r\n\r\n' % name.encode())
        out.write(value.encode() if isinstance(value, str) else value)
        out.write(b"\r\n")
    out.write(b"--" + bnd + b"\r\n")
    out.write(
        ('Content-Disposition: form-data; name="uploadfile"; filename="%s"\r\n'
         % filename).encode()
    )
    out.write(b"Content-Type: application/octet-stream\r\n\r\n")
    out.write(filebytes)
    out.write(b"\r\n--" + bnd + b"--\r\n")
    return out.getvalue()


class Router:
    def __init__(self, host):
        self.host = host
        self.cookie = None
        self.token = None
        self.logged_in = False

    def http(self, method, path, body=None, headers=None, timeout=15):
        url = "http://%s%s" % (self.host, path)
        h = {"User-Agent": "Mozilla/5.0"}
        if self.cookie:
            h["Cookie"] = self.cookie
        if self.token:
            h["__RequestVerificationToken"] = self.token
        if headers:
            h.update(headers)
        req = urllib.request.Request(url, data=body, headers=h, method=method)
        self.last_headers = {}
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                self.last_headers = dict(r.headers)
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            self.last_headers = dict(e.headers)
            return e.code, e.read()
        except Exception as e:
            return None, str(e).encode()

    def rotated_token(self):
        """Token CSRF rotado en los headers de la última respuesta."""
        for k, v in self.last_headers.items():
            if k.lower().replace("_", "").endswith("requestverificationtoken"):
                return v[:32]
        return None

    def get_session(self):
        st, body = self.http("GET", "/api/webserver/SesTokInfo")
        if st != 200:
            print("  [!] SesTokInfo falló: %s %s" % (st, body[:120]))
            return False
        txt = body.decode("utf-8", "replace")
        if "<SesInfo>" in txt and "<TokInfo>" in txt:
            self.cookie = "SessionID=" + txt.split("<SesInfo>")[1].split("</SesInfo>")[0].strip()
            self.token = txt.split("<TokInfo>")[1].split("</TokInfo>")[0].strip()
            return True
        return False

    def login(self):
        pw = sha256_hex(PASS)
        body = ('<?xml version="1.0" encoding="UTF-8"?>'
                "<request><username>%s</username><password>%s</password>"
                "<password_type>4</password_type></request>" % (USER, pw))
        st, resp = self.http("POST", "/api/user/login", body=body.encode())
        ok = st == 200 and "<response>OK</response>" in resp.decode("utf-8", "replace")
        print("  POST /api/user/login -> %s %s" % (st, "OK" if ok else resp[:120]))
        return ok

    def get_token(self):
        """Token fresco de api/webserver/token (el que usa getAjaxToken)."""
        st, body = self.http("GET", "/api/webserver/token")
        if st != 200:
            return None
        txt = body.decode("utf-8", "replace")
        if "<token>" in txt:
            return txt.split("<token>")[1].split("</token>")[0].strip()
        return None

    def login_scram(self, username="admin", password=None):
        """Login SCRAM real (challenge_login + authentication_login), como main.js.
        Devuelve True si la sesión quedó establecida (State=0).
        """
        if password is None:
            password = PASS
        # token inicial (el JS hace substr(32))
        t = self.get_token()
        if not t:
            return False
        tok = t[32:]
        # challenge
        first_nonce = os.urandom(32).hex()
        body = ('<?xml version="1.0" encoding="UTF-8"?>'
                "<request><username>%s</username><firstnonce>%s</firstnonce>"
                "<mode>1</mode></request>" % (username, first_nonce))
        st, resp = self.http("POST", "/api/user/challenge_login", body=body.encode(),
                             headers={"_ResponseSource": "Broswer"}, timeout=20)
        txt = resp.decode("utf-8", "replace") if isinstance(resp, bytes) else str(resp)
        if "<error>" in txt or "<salt>" not in txt:
            print("  [!] challenge_login falló: %s" % " ".join(txt.split())[:120])
            return False
        salt = re.search(r"<salt>(.*?)</salt>", txt, re.S).group(1)
        iterations = int(re.search(r"<iterations>(.*?)</iterations>", txt, re.S).group(1))
        servernonce = re.search(r"<servernonce>(.*?)</servernonce>", txt, re.S).group(1)
        # si el servidor rotara el token CSRF en la respuesta, adoptarlo
        # (challenge_login.lua no rota; la lectura es inofensiva)
        new_tok = self.rotated_token()
        if new_tok:
            self.token = new_tok
        # client proof (SCRAM-SHA-256, mismo algoritmo que scram.js)
        auth_msg = first_nonce + "," + servernonce + "," + servernonce
        salted = hashlib.pbkdf2_hmac("sha256", password.encode(),
                                     bytes.fromhex(salt), iterations, dklen=32)
        client_key = hmac.new(salted, b"Client Key", hashlib.sha256).digest()
        stored_key = hashlib.sha256(client_key).digest()
        client_sig = hmac.new(stored_key, auth_msg.encode(), hashlib.sha256).digest()
        client_proof = bytes(a ^ b for a, b in zip(client_key, client_sig)).hex()
        # authentication
        body = ('<?xml version="1.0" encoding="UTF-8"?>'
                "<request><clientproof>%s</clientproof><finalnonce>%s</finalnonce></request>"
                % (client_proof, servernonce))
        st, resp = self.http("POST", "/api/user/authentication_login", body=body.encode(),
                             headers={"_ResponseSource": "Broswer"}, timeout=20)
        txt = resp.decode("utf-8", "replace") if isinstance(resp, bytes) else str(resp)
        if "<error>" in txt:
            code = re.search(r"<code>(.*?)</code>", txt)
            wait = re.search(r"<waittime>(.*?)</waittime>", txt)
            c = code.group(1) if code else "?"
            w = wait.group(1) if wait else "0"
            print("  [!] authentication_login falló (código %s, waittime %s min)" % (c, w))
            return False
        # authentication_login.lua del firmware TAMBIÉN rota el token CSRF
        # en la respuesta (getcsrf -> __RequestVerificationToken...): sin esto,
        # la verificación state-login siguiente iría con token viejo -> 125003.
        new_tok = self.rotated_token()
        if new_tok:
            self.token = new_tok
        # verificar sesión real
        st, resp = self.http("GET", "/api/webserver/SesTokInfo")
        txt = resp.decode("utf-8", "replace")
        m = re.search(r"<SesInfo>(.*?)</SesInfo>", txt, re.S)
        if m and m.group(1).strip():
            self.cookie = "SessionID=" + m.group(1).strip()
        st, resp = self.http("GET", "/api/user/state-login")
        txt = resp.decode("utf-8", "replace")
        state = re.search(r"<State>(.*?)</State>", txt)
        self.logged_in = bool(state and state.group(1).strip() == "0")
        return self.logged_in

    def upload(self, path_to_file):
        """Sube el archivo por /api/filemanager/upload (mecánica de update_local.js)."""
        filename = path_to_file.split("/")[-1].split("\\")[-1]
        with open(path_to_file, "rb") as f:
            data = f.read()
        token = self.get_token() or self.token
        if not token:
            print("  [!] No hay token CSRF")
            return None
        # update_local.js usa getAjaxToken() = token.substr(32): el token
        # de /api/webserver/token es de 64 chars y el CSRF es la 2ª mitad.
        csrf = token[32:] if len(token) >= 64 else token
        fields = {
            "csrf_token": "csrf:" + csrf,
            "cur_path": "OU:" + filename,
        }
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = build_multipart(fields, filename, data, boundary)
        hdrs = {"Content-Type": "multipart/form-data; boundary=%s" % boundary}
        print("  Subiendo %s (%.1f MB) a /api/filemanager/upload ..."
              % (filename, len(data) / 1024.0 / 1024.0))
        t0 = time.time()
        st, resp = self.http("POST", "/api/filemanager/upload", body=body, headers=hdrs, timeout=600)
        el = time.time() - t0
        txt = resp.decode("utf-8", "replace") if isinstance(resp, bytes) else str(resp)
        print("  Respuesta (%ds): HTTP %s -> %r" % (int(el), st, txt[:200]))
        # update_local.js: el éxito es que la respuesta contenga 'ok'
        if txt and "ok" in txt.lower():
            print("  >>> SUBIDA ACEPTADA por el handler (contiene 'ok').")
            return True
        if "<code>100003</code>" in txt or "100003" in txt:
            print("  >>> 100003: handler de subida MUERTO en este firmware Entel.")
        return False

    def poll_status(self, seconds=300):
        """Polling de estado post-subida (check-notifications + online-update/status)."""
        t0 = time.time()
        last = None
        while time.time() - t0 < seconds:
            st, body = self.http("GET", "/api/monitoring/check-notifications")
            if st == 200:
                txt = body.decode("utf-8", "replace")
                if "<OnlineUpdateStatus>" in txt:
                    v = txt.split("<OnlineUpdateStatus>")[1].split("</OnlineUpdateStatus>")[0].strip()
                    try:
                        code = int(v)
                    except ValueError:
                        code = -1
                    name = STATUS.get(code, "?")
                    if code != last:
                        print("  [%ds] OnlineUpdateStatus = %s (%s)" % (int(time.time() - t0), code, name))
                        last = code
                    if code in (20, 70, 80):
                        print("  >>> UPDATE FALLÓ.")
                        return False
                    if code in (90, 100):
                        print("  >>> UPDATE COMPLETADO CON ÉXITO.")
                        return True
                    if code in (60,):
                        # instalando: consultar el detalle del componente
                        st2, b2 = self.http("GET", "/api/online-update/status")
                        if st2 == 200:
                            t2 = b2.decode("utf-8", "replace")
                            prog = "?"
                            if "<DownloadProgress>" in t2:
                                prog = t2.split("<DownloadProgress>")[1].split("</DownloadProgress>")[0].strip()
                            print("      (instalando... DownloadProgress=%s)" % prog)
            time.sleep(3)
        print("  [!] Timeout de polling (%ds) — revisa el router manualmente." % seconds)
        return None

    def probe(self):
        """Verifica si el handler de subida vive, sin mandar nada grande."""
        print("-- PROBE: /api/filemanager/upload --")
        # 1) GET simple
        st, resp = self.http("GET", "/api/filemanager/upload")
        txt = resp.decode("utf-8", "replace") if isinstance(resp, bytes) else str(resp)
        print("  GET  -> HTTP %s %r" % (st, txt[:150]))
        # 2) POST multipart con archivo mínimo
        fields = {"csrf_token": "csrf:" + (self.token or ""),
                  "cur_path": "OU:probe.txt"}
        body = build_multipart(fields, "probe.txt", b"test", "----ProbeBoundary")
        hdrs = {"Content-Type": "multipart/form-data; boundary=----ProbeBoundary"}
        st, resp = self.http("POST", "/api/filemanager/upload", body=body, headers=hdrs, timeout=30)
        txt = resp.decode("utf-8", "replace") if isinstance(resp, bytes) else str(resp)
        print("  POST-> HTTP %s %r" % (st, txt[:150]))
        alive = st is not None and ("ok" in txt.lower() or ("<error>" in txt and "100003" not in txt))
        print("  >>> Handler %s" % ("VIVO" if alive else "MUERTO (100003 o sin respuesta)"))
        return alive


def detect_host():
    """Prueba IPs típicas del router B612 (puede cambiar tras flashear)."""
    import socket
    for ip in ("192.168.8.1", "192.168.1.1", "192.168.0.1"):
        try:
            socket.create_connection((ip, 80), timeout=2).close()
            return ip
        except OSError:
            continue
    return None


def main():
    ap = argparse.ArgumentParser(description="Update local por WebUI (replica inst_webui)")
    ap.add_argument("--host", default=None)
    ap.add_argument("--file", default=DEFAULT_FILE)
    ap.add_argument("--probe", action="store_true", help="solo probar si el handler vive")
    ap.add_argument("--password", default=None, help="contraseña admin (sticker si nunca cambió)")
    ap.add_argument("--username", default="admin")
    args = ap.parse_args()

    host = args.host or detect_host() or DEFAULT_HOST
    print("=== webui_update.py — B612s-51d en %s ===" % host)
    r = Router(host)

    if not r.get_session():
        print("  No se obtuvo sesión. ¿Estás conectado al router (cable LAN)?")
        sys.exit(1)
    print("  Sesión OK.")

    if not r.login_scram(args.username, args.password):
        print("\n  Login SCRAM falló. Este firmware usa SCRAM (extern_password_type=1).")
        print("  La contraseña real NO es admin/admin: está en la ETIQUETA (sticker)")
        print("  de la parte inferior del router (nameplate).")
        print("  Intenta:  python webui_update.py --password <la-del-sticker>")
        sys.exit(1)
    print("  Login SCRAM OK como admin (sesión real verificada).\n")

    if args.probe:
        r.probe()
        sys.exit(0)

    print("-- VERIFICACIÓN PREVIA --")
    st, resp = r.http("GET", "/api/pin/simlock")
    if st == 200:
        txt = resp.decode("utf-8", "replace")
        for tag in ("SimLockEnable", "SimLockRemainTimes", "SimLockVersion"):
            if "<%s>" % tag in txt:
                v = txt.split("<%s>" % tag)[1].split("</%s>" % tag)[0].strip()
                print("  %s = %s" % (tag, v))
    st, resp = r.http("GET", "/api/online-update/status")
    if st == 200:
        txt = resp.decode("utf-8", "replace")
        if "<CurrentComponentStatus>" in txt:
            v = txt.split("<CurrentComponentStatus>")[1].split("</CurrentComponentStatus>")[0].strip()
            print("  online-update CurrentComponentStatus = %s (%s)"
                  % (v, STATUS.get(int(v), "?")))
    print()

    print("-- SUBIDA --")
    ok = r.upload(args.file)
    if not ok:
        print("\nLa subida no fue aceptada. Opciones:")
        print("  1. Si dice 100003: la build Entel C110 arrancó el handler;")
        print("     la vía web está cerrada -> USB (kit_flasheo) o NCK Entel.")
        print("  2. Ejecuta  python webui_update.py --probe  para confirmar.")
        sys.exit(2)

    print("\n-- POLLING DE ESTADO (hasta 5 min) --")
    res = r.poll_status()
    if res is True:
        print("\nEl router debería estar instalando/reiniciando. Al volver:")
        print("  - Versión: 81.201.01.01.234, WebUI 81.100.34.01.23")
        print("  - La IP PUEDE cambiar: prueba 192.168.8.1 -> 192.168.1.1 -> 192.168.0.1")
        print("  - Luego el desbloqueo: python desbloquear_b612.py")
    elif res is False:
        print("\nUpdate falló en el lado del router. Revisa que el zip sea")
        print("el preparado (B612__1 en cabecera) y que el WebUI sea el genérico.")
    sys.exit(0)


if __name__ == "__main__":
    main()
