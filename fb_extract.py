import re, html

h = open("C:/Users/davis/AppData/Local/Temp/fb1.html", encoding="utf-8", errors="ignore").read()
texts = re.findall(r'"text":"((?:[^"\\]|\\.)*)"', h)
out = []
for t in texts:
    try:
        t = t.encode().decode("unicode_escape", "ignore")
    except Exception:
        pass
    t = html.unescape(t)
    if any(k in t.lower() for k in ["b612", "desbloqueo", "codigo", "chip", "entel", "wom", "movistar", "sim", "liberad", "bloqueo"]):
        out.append(t)
seen = set()
for t in out:
    if t not in seen and len(t) > 15:
        seen.add(t)
        print("-", t[:350])
        print()
print("total textos:", len(out))
