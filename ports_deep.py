#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Barrido profundo TCP/UDP del B612s-51d."""
import socket, time

HOST = "192.168.8.1"

TCP_PORTS = [21,22,23,53,69,80,81,88,123,135,139,161,443,445,500,502,515,631,993,
             1080,1433,1723,1900,2323,3128,3306,3389,37215,4444,5000,5431,5555,5510,
             5540,6000,6379,6666,7547,8000,8080,8081,8088,8443,8888,9000,9090,10000,
             11211,27017,32768,49152,50000,55555]

UDP_PORTS = [53,67,68,69,123,137,138,161,162,500,514,623,1900,2049,33434,4500,5353]

def tcp(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((HOST, port))
        banner = b""
        try:
            s.settimeout(1.5)
            banner = s.recv(80)
        except Exception:
            pass
        return banner[:60]
    except Exception:
        return None
    finally:
        s.close()

def udp(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(2)
    try:
        if port == 161:
            # SNMP GET sysDescr con comunidad "public"
            pkt = bytes.fromhex("302602010104067075626c6963a01c020400000001020100020100300e300c06082b060102010100000500")
            s.sendto(pkt, (HOST, port))
            data, _ = s.recvfrom(400)
            return data[:80]
        elif port == 1900:
            s.sendto(b"M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: \"ssdp:discover\"\r\nMX: 2\r\nST: ssdp:all\r\n\r\n", (HOST, port))
            data, _ = s.recvfrom(1000)
            return data[:120]
        elif port == 69:
            # RRQ de un archivo de config (no deberia responder si esta cerrado)
            s.sendto(bytes([0,1]) + b"config\x00netascii\x00", (HOST, port))
            data, _ = s.recvfrom(200)
            return data[:80]
        else:
            s.sendto(b"probe", (HOST, port))
            data, _ = s.recvfrom(200)
            return data[:80]
    except Exception:
        return None
    finally:
        s.close()

print("===== TCP (extra) =====")
for p in TCP_PORTS:
    b = tcp(p)
    if b is not None:
        print(f"  TCP {p:6} ABIERTO banner={b!r}")

print("\n===== UDP =====")
for p in UDP_PORTS:
    b = udp(p)
    if b is not None:
        print(f"  UDP {p:6} RESPUESTA {b!r}")
print("\nFIN")
