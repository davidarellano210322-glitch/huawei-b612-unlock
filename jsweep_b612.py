#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detective sweep: descarga los JS de todas las paginas del menu, extrae TODAS
las rutas api/ y url: ... y las prueba con sesion. Busca handlers vivos.
"""
import urllib.request, urllib.error, gzip, re, json

HOST = "192.168.8.1"

PAGES = ["quicksetup","mobileconnection","profilesmgr","mobilenetworksettings",
    "wifinetworks","wifipriority","stationwps","ethernetsettings","ethernetstatus",
    "macclone","volte","vpnstatus","vpnsettings","wlanbasicsettings","wlanadvanced",
    "wlanmacfilter","wps","dhcp","voip","ftpserver","sipbasic","speeddial","voiceprofile",
    "advancecodec","voiceadvanced","pincodemanagement","firewallswitch","macfilter",
    "lanipfilter","virtualserver","specialapplication","dmzsettings","sipalgsettings",
    "upnp","pcp","nat","urlfilter","ddns","certupload","bridgemode","devicemanagement",
    "parentalcontrol","cbssettings","qossettings","bluetooth","bluetoothsetting","vsim",
    "tr069settings","tr069profile","nfcsettings","deviceinformation","modifypassword",
    "diagnosis","restore","reboot","systemsettings","systemlog","timesettings","antenna",
    "appmanagement","statistic","commend","sms","smsinbox","smssent","smsdrafts",
    "messagesettings","phonebook","upgrade","upload","login","index","home"]

def fetch(path, cookie=None, token=None):
    headers = {"User-Agent":"Mozilla/5.0","Accept-Encoding":"identity"}
    if cookie: headers["Cookie"] = cookie
    if token: headers["__RequestVerificationToken"] = token
    req = urllib.request.Request(f"http://{HOST}{path}", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=6) as r:
            return r.read()
    except Exception:
        return b""

def dec(d):
    try:
        return gzip.decompress(d).decode("utf-8","replace")
    except Exception:
        return d.decode("utf-8","replace")

# sesion
b = dec(fetch("/api/webserver/SesTokInfo"))
cookie = "SessionID=" + b.split("<SesInfo>")[1].split("</SesInfo>")[0].strip()
token = b.split("<TokInfo>")[1].split("</TokInfo>")[0].strip()

# 1) juntar todos los JS
todo = ""
hallados = []
for p in PAGES:
    d = fetch(f"/js/{p}.js")
    if len(d) > 50:
        j = dec(d)
        hallados.append((p, len(j)))
        todo += f"\n/* --- {p}.js --- */\n" + j

print(f"JS de paginas encontrados: {len(hallados)}")
for p, l in hallados:
    print(f"   {p:28} {l} bytes")

# 2) extraer rutas
urls = set()
for m in re.finditer(r"['\"](?:\.\./)?(api/[A-Za-z0-9_\-/]+)['\"]", todo):
    urls.add(m.group(1))
for m in re.finditer(r"url\s*[:=]\s*['\"]([^'\"]+)['\"]", todo):
    u = m.group(1)
    if u.startswith("/") and "api" in u.lower():
        urls.add(u.lstrip("/"))
for m in re.finditer(r"getAjaxData\(\s*['\"]([^'\"]+)['\"]", todo):
    u = m.group(1)
    if "api/" in u:
        urls.add(u)
urls = sorted(urls)
print(f"\nEndpoints unicos: {len(urls)}")

# 3) probar
print("\n=== VIVOS (no-100003) ===")
vivos = []
for u in urls:
    d = fetch("/" + u, cookie, token)
    txt = dec(d)
    if "<error>" not in txt or "<code>100003</code>" not in txt:
        vivos.append((u, txt[:150].replace("\n"," ")))
        print(f">> {u:55} {txt[:110]!r}")
    else:
        print(f"   {u}")

print(f"\n=== {len(vivos)} VIVOS ===")
for u, t in vivos:
    print(f"  {u}\n     {t}")
