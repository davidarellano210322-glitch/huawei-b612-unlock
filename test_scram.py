#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_scram.py — Verificación OFFLINE del login SCRAM (sin router)
================================================================
El login SCRAM (challenge_login + authentication_login) solo se ha
probado contra el router real, donde el error 108006 es el MISMO para
"contraseña incorrecta" y para "prueba mal calculada": con 108006 no
se puede saber si el cliente SCRAM es correcto. Este test levanta un
servidor MOCK que replica el lado servidor del firmware (PBKDF2-SHA256,
serversignature, rotación del token CSRF, state-login) con una
contraseña CONOCIDA y comprueba el cliente de webui_update.py
end-to-end:

    python test_scram.py

Chequeos:
  1. login_scram con la contraseña correcta -> True (State=0)
  2. El token CSRF rotado por authentication_login (primeros 32 chars
     del header __RequestVerificationToken, como getTokenFromHeader)
     se adopta para la siguiente petición
  3. Contraseña incorrecta -> False (código 108006)
  4. Un token CSRF viejo es rechazado (125003)

Fidelidad al firmware real (replicado de los .lua extraídos):
  - challenge_login.lua: NO rota el token (solo responde salt/iter/sn)
  - authentication_login.lua: al validar la prueba rota el token con
    web.setHeaderRequestVerificationToken(token,"one"/"two") y deja el
    pool en "__RequestVerificationToken" (tokens separados por '#').
    El cliente toma los primeros 32 chars (getTokenFromHeader).
  - Lado servidor de SCRAM (scram.js / web.nonce):
      authMsg = firstnonce + "," + servernonce + "," + servernonce
      saltedPassword = PBKDF2-HMAC-SHA256(password, hex(salt), iter, 32)
      clientKey = HMAC(salted, "Client Key"); storedKey = SHA256(clientKey)
      clientSig = HMAC(storedKey, authMsg); proof = clientKey XOR clientSig
      serverKey = HMAC(salted, "Server Key")
      serverSig = HMAC(serverKey, authMsg)  -> <serversignature>
"""
import re
import os
import sys
import hmac
import hashlib
import threading
import socketserver
from http.server import BaseHTTPRequestHandler

import webui_update
from webui_update import Router

PASSWORD = "ClaveDePruebaDelSticker-2026"   # "contraseña del sticker" conocida
ITERATIONS = 500
PUBLIC = {"/api/webserver/SesTokInfo"}


def new_token():
    return os.urandom(16).hex()             # token CSRF de 32 hex (web.getcsrf)


def new_session():
    return os.urandom(16).hex()             # SesInfo


def new_session_state():
    full = new_token() + new_token()        # TokInfo de 64 hex
    return {
    "full": full,               # 64 hex
    # el cliente envía el token completo (64) o su CSRF (substr(32) = 2ª mitad)
    "tokens": {full, full[32:], full[:32]},
        "logged_in": False,
        "challenge": None,
    }


def server_side(password, salt, iterations, auth_msg):
    """Lado servidor de SCRAM-SHA-256 (igual que scram.js del firmware).
    Devuelve (proof_esperada, serversignature)."""
    salted = hashlib.pbkdf2_hmac("sha256", password.encode(),
                                 bytes.fromhex(salt), iterations, dklen=32)
    client_key = hmac.new(salted, b"Client Key", hashlib.sha256).digest()
    stored_key = hashlib.sha256(client_key).digest()
    client_sig = hmac.new(stored_key, auth_msg.encode(), hashlib.sha256).digest()
    expected_proof = bytes(a ^ b for a, b in zip(client_key, client_sig)).hex()
    server_key = hmac.new(salted, b"Server Key", hashlib.sha256).digest()
    server_sig = hmac.new(server_key, auth_msg.encode(), hashlib.sha256).digest().hex()
    return expected_proof, server_sig


SESSIONS = {}   # sid -> estado de sesión (por cookie, como el router real)


class MockB612(BaseHTTPRequestHandler):
    server_version = "MockB612/1.0"
    protocol_version = "HTTP/1.0"

    def log_message(self, fmt, *args):
        pass

    def _reply(self, body, headers=None):
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/xml")
        self.send_header("Content-Length", str(len(data)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _error(self, code):
        self._reply('<?xml version="1.0" encoding="UTF-8"?>'
                    "<error><code>%d</code></error>" % code)

    def _sid(self):
        raw = self.headers.get("Cookie", "")
        m = re.search(r"(?:^|;\s*)SessionID=([A-Fa-f0-9]+)", raw)
        return m.group(1) if m else None

    def _session(self, create=False):
        sid = self._sid()
        if sid and sid in SESSIONS:
            return SESSIONS[sid]
        if create:
            sid = new_session()
            SESSIONS[sid] = new_session_state()
            self._created_sid = sid
            return SESSIONS[sid]
        return None

    def _check_token(self, st):
        return self.headers.get("__RequestVerificationToken", "") in st["tokens"]

    def _rotate(self, st):
        """Rotación del authentication_login.lua: one/two + pool en el header
        principal (los 32 primeros chars del valor = primer token del pool)."""
        t1, t2 = new_token(), new_token()
        pool = [new_token() for _ in range(5)]
        st["tokens"] = set([t1, t2] + pool)
        return {
            "__RequestVerificationTokenone": t1,
            "__RequestVerificationTokentwo": t2,
            "__RequestVerificationToken": "#".join([t1, t2] + pool),
        }

    def _path(self):
        return self.path.split("?")[0]

    def do_GET(self):
        p = self._path()
        if p == "/api/webserver/SesTokInfo":
            st = self._session(create=True)
            sid = getattr(self, "_created_sid", self._sid())
            body = ('<?xml version="1.0" encoding="UTF-8"?>'
                    "<response><SesInfo>%s</SesInfo><TokInfo>%s</TokInfo></response>"
                    % (sid, st["full"]))
            return self._reply(body)
        st = self._session()
        if not st:
            return self._error(100003)
        if not self._check_token(st):
            return self._error(125003)
        if p == "/api/webserver/token":
            return self._reply('<?xml version="1.0" encoding="UTF-8"?>'
                               "<response><token>%s</token></response>" % st["full"])
        if p == "/api/user/state-login":
            state = "0" if st["logged_in"] else "-1"
            return self._reply('<?xml version="1.0" encoding="UTF-8"?>'
                               "<response><State>%s</State><firstlogin>1</firstlogin>"
                               "<userlevel>0</userlevel></response>" % state)
        return self._error(100003)

    def do_POST(self):
        p = self._path()
        st = self._session()
        if not st:
            return self._error(100003)
        if not self._check_token(st):
            return self._error(125003)
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8", "replace")

        if p == "/api/user/challenge_login":
            m_user = re.search(r"<username>(.*?)</username>", raw, re.S)
            m_nonce = re.search(r"<firstnonce>(.*?)</firstnonce>", raw, re.S)
            if not m_user or not m_nonce:
                return self._error(108006)
            salt = os.urandom(16).hex()
            servernonce = os.urandom(24).hex()
            st["challenge"] = {
                "username": m_user.group(1),
                "firstnonce": m_nonce.group(1),
                "salt": salt,
                "iterations": ITERATIONS,
                "servernonce": servernonce,
            }
            # el router REAL (build Entel) rota el token en el challenge
            # (verificado en vivo con intento_login.py: header 32 chars)
            t1 = new_token()
            st["tokens"] = set([t1])
            body = ('<?xml version="1.0" encoding="UTF-8"?>'
                    "<response>OK</response>"
                    "<salt>%s</salt><iterations>%d</iterations>"
                    "<servernonce>%s</servernonce><modeselected>1</modeselected>"
                    % (salt, ITERATIONS, servernonce))
            return self._reply(body, headers={"__RequestVerificationToken": t1})

        if p == "/api/user/authentication_login":
            ch = st["challenge"]
            m_proof = re.search(r"<clientproof>(.*?)</clientproof>", raw, re.S)
            m_final = re.search(r"<finalnonce>(.*?)</finalnonce>", raw, re.S)
            if not ch or not m_proof or not m_final:
                return self._error(108006)
            if m_final.group(1) != ch["servernonce"]:
                return self._error(108006)
            auth_msg = "%s,%s,%s" % (ch["firstnonce"], ch["servernonce"], ch["servernonce"])
            expected, server_sig = server_side(PASSWORD, ch["salt"],
                                               ch["iterations"], auth_msg)
            if m_proof.group(1) != expected:
                # authentication_login.lua también rota en el fallo
                return self._reply('<?xml version="1.0" encoding="UTF-8"?>'
                                   "<error><code>108006</code><count>1</count></error>",
                                   headers=self._rotate(st))
            st["logged_in"] = True
            body = ('<?xml version="1.0" encoding="UTF-8"?>'
                    "<response>OK</response><serversignature>%s</serversignature>"
                    "<rsapubkeysignature>x</rsapubkeysignature>"
                    "<rsan>x</rsan><rsae>x</rsae>" % server_sig)
            return self._reply(body, headers=self._rotate(st))

        return self._error(100003)


class ThreadingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    srv = ThreadingServer(("127.0.0.1", 0), MockB612)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    host = "127.0.0.1:%d" % port
    print("=== test_scram.py — mock B612 SCRAM en %s ===" % host)
    print("    contraseña del 'sticker': %r  | iterations=%d\n" % (PASSWORD, ITERATIONS))

    fails = 0

    # 1) contraseña correcta -> login OK (State=0)
    r = Router(host)
    assert r.get_session(), "no se obtuvo sesión del mock"
    initial_token = r.token
    ok = r.login_scram("admin", PASSWORD)
    print("[%s] login SCRAM con contraseña CORRECTA -> %r (esperado True)"
          % ("OK" if ok else "FALLO", ok))
    fails += 0 if ok else 1

    # 2) rotación de token CSRF: tras authentication_login el cliente debe
    #    usar los primeros 32 chars del header rotado (getTokenFromHeader)
    rotated = bool(r.token) and len(r.token) == 32 and r.token != initial_token
    print("[%s] token CSRF rotado por authentication_login adoptado (32 chars)"
          % ("OK" if rotated else "FALLO"))
    fails += 0 if rotated else 1

    # 3) contraseña incorrecta -> False (108006)
    r2 = Router(host)
    assert r2.get_session(), "no se obtuvo sesión del mock (r2)"
    bad = r2.login_scram("admin", "clave-equivocada")
    print("[%s] login SCRAM con contraseña INCORRECTA -> %r (esperado False/108006)"
          % ("OK" if not bad else "FALLO", bad))
    fails += 0 if not bad else 1

    # 4) un token CSRF viejo debe ser rechazado (125003)
    r.token = initial_token
    st, resp = r.http("GET", "/api/user/state-login")
    txt = resp.decode("utf-8", "replace") if isinstance(resp, bytes) else str(resp)
    old_rejected = st == 200 and "125003" in txt
    print("[%s] token CSRF viejo rechazado (125003): HTTP %s %r"
          % ("OK" if old_rejected else "FALLO", st, txt[:80]))
    fails += 0 if old_rejected else 1

    srv.shutdown()
    print("\nRESULTADO: %s" % ("TODOS LOS CHECKS OK" if fails == 0 else "%d FALLOS" % fails))
    sys.exit(0 if fails == 0 else 1)


if __name__ == "__main__":
    main()
