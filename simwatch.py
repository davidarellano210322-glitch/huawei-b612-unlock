#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor en vivo del estado SIM/simlock del B612s-51d.
Escribe a simlog.txt cada 2 segundos durante 5 minutos.
Uso: python simwatch.py
"""
import urllib.request, time, datetime, sys

HOST = "192.168.8.1"
LOG = "simlog.txt"

def get(path, cookie=None, token=None):
    headers = {"User-Agent":"Mozilla/5.0"}
    if cookie: headers["Cookie"] = cookie
    if token: headers["__RequestVerificationToken"] = token
    req = urllib.request.Request(f"http://{HOST}{path}", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.read(1500).decode("utf-8","replace")
    except Exception:
        return ""

def tag(xml, name):
    try:
        return xml.split("<"+name+">")[1].split("</"+name+">")[0].strip()
    except Exception:
        return "?"

def main():
    cookie, token = None, None
    t_end = time.time() + 300
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"\n=== MONITOR INICIADO {datetime.datetime.now().isoformat()} ===\n")
        while time.time() < t_end:
            if cookie is None:
                b = get("/api/webserver/SesTokInfo")
                if "<SesInfo>" in b:
                    cookie = "SessionID=" + tag(b, "SesInfo")
                    token = tag(b, "TokInfo")
                else:
                    f.write(f"{time.time():.0f} sin-sesion (router apagado/reiniciando?)\n")
                    f.flush()
                    time.sleep(3)
                    continue
            conv = get("/api/monitoring/converged-status", cookie, token)
            siml = get("/api/pin/simlock", cookie, token)
            plmn = get("/api/net/current-plmn", cookie, token)
            mon  = get("/api/monitoring/status", cookie, token)
            if "SimState" not in conv and "SimState" not in mon:
                # sesion muerta o router reiniciando
                cookie = None
                f.write(f"{time.time():.0f} router-no-responde (reiniciando?)\n")
                f.flush()
                time.sleep(3)
                continue
            linea = (f"{time.time():.0f} conv[SimState={tag(conv,'SimState')} SimLockEnable={tag(conv,'SimLockEnable')}] "
                     f"simlock[Enable={tag(siml,'SimLockEnable')} Remain={tag(siml,'SimLockRemainTimes')}] "
                     f"plmn[State={tag(plmn,'State')} {tag(plmn,'FullName')} {tag(plmn,'ShortName')}] "
                     f"mon[Conn={tag(mon,'ConnectionStatus')}]")
            print(linea, flush=True)
            f.write(linea + "\n")
            f.flush()
            time.sleep(2)

if __name__ == "__main__":
    main()
