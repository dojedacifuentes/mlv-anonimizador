"""Copia las listas chilenas (nombres, apellidos, palabras que cortan) desde el tachador de MLV.

Uso: python herramientas/extraer_listas.py ../mlv.abogados/herramientas/tachar.html paquete-chile/listas.json
"""
import json
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
html = open(src, encoding="utf-8").read()


def bloque(nombre: str) -> list[str]:
    m = re.search(rf"const {nombre} = set\(`(.*?)`\);", html, re.S)
    if not m:
        raise SystemExit(f"No encontré la lista {nombre} en {src}")
    cuerpo = re.sub(r"\$\{[^}]*\}", " ", m.group(1))
    return sorted(set(cuerpo.split()))


listas = {k.lower(): bloque(k) for k in ("AMBIGUOS", "NOMBRES", "APELLIDOS", "STOP")}
listas["nombres"] = sorted(set(listas["nombres"]) | set(listas["ambiguos"]))
json.dump(listas, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print({k: len(v) for k, v in listas.items()})
