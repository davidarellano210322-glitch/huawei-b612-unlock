#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Barrido exhaustivo de endpoints del WebUI B612s-51d.
Extrae las URLs 'api/...' de los JS del router y las prueba con sesion admin.
"""
import re, urllib.request, gzip, sys

HOST = "192.168.8.1"

def fetch(path, cookie=None, token=None):
    headers = {"User-Agent":"Mozilla/5.0","Accept-Encoding":"identity"}
    if cookie: headers["Cookie"] = cookie
    if token: headers["__RequestVerificationToken"] = token
    req = urllib.request.Request(f"http://{HOST}{path}", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.read()
    except Exception as e:
        return str(e).encode()

def decomp(data):
    try:
        return gzip.decompress(data).decode("utf-8","replace")
    except Exception:
        return data.decode("utf-8","replace")

# 1) sesion
b = decomp(fetch("/api/webserver/SesTokInfo"))
cookie = "SessionID=" + b.split("<SesInfo>")[1].split("</SesInfo>")[0].strip()
token = b.split("<TokInfo>")[1].split("</TokInfo>")[0].strip()

# 2) juntar todos los JS
js_files = ["/js/main.js","/js/update.js","/js/redirect.js","/js/format.js","/js/changelang.js",
            "/js/checklogin.js","/js/language.js","/js/customelement.js","/js/display.js"]
todo = ""
for jf in js_files:
    d = fetch(jf)
    if isinstance(d, bytes) and len(d) > 100:
        todo += "\n" + decomp(d)

# 3) extraer rutas api/
urls = set()
for m in re.finditer(r"['\"](?:\.\./)?(api/[A-Za-z0-9_\-/]+)['\"]", todo):
    urls.add(m.group(1))
urls = sorted(urls)
print(f"Endpoints unicos encontrados en JS: {len(urls)}")

# 4) probarlos
print("\n=== RESULTADOS (no-100003 marcados con >>) ===")
vivos = []
for u in urls:
    st, resp = fetch("/" + u, cookie, token), None
    try:
        txt = decomp(st)
    except Exception:
        txt = str(st)
    if "<error>" not in txt or "<code>100003</code>" not in txt:
        vivos.append((u, txt[:120].replace("\n"," ")))
        print(f">> {u:55} {txt[:100]!r}")
    else:
        print(f"   {u}")
print(f"\n=== {len(vivos)} ENDPOINTS VIVOS ===")
for u, t in vivos:
    print(f"  {u}\n     {t}")
