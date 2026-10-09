"""Tacha documentos y cuenta en español lo que se tachó. Lo usan los accesos de doble clic.

Uso: python herramientas/tachar.py ARCHIVO_O_CARPETA [...] [--salida CARPETA]
Sin --salida, cada resultado queda en una carpeta «Tachados» junto al original.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
PROGRAMA = RAIZ / ".venv" / "Scripts" / "anonymize.exe"
CONFIG = RAIZ / "paquete-chile" / "config-mlv.yaml"
TIPOS = {".pdf", ".docx", ".txt", ".md"}

NOMBRES = {
    "PERSON": ("persona", "personas"),
    "CL_RUT": ("RUT o documento", "RUT o documentos"),
    "ORG": ("empresa", "empresas"),
    "STREET": ("dirección", "direcciones"),
    "CITY": ("comuna o lugar", "comunas o lugares"),
    "LOCATION": ("lugar", "lugares"),
    "PHONE_NUMBER": ("teléfono", "teléfonos"),
    "EMAIL_ADDRESS": ("correo", "correos"),
    "CL_CAUSA": ("rol de causa", "roles de causa"),
    "CL_PROPIEDAD": ("dato de propiedad", "datos de propiedad"),
    "CL_PATENTE": ("patente", "patentes"),
    "CL_CUENTA": ("cuenta bancaria", "cuentas bancarias"),
    "URL": ("enlace", "enlaces"),
}


def resumen(conteo: dict[str, int]) -> str:
    partes = []
    for tipo, n in sorted(conteo.items(), key=lambda kv: -kv[1]):
        uno, varios = NOMBRES.get(tipo, (tipo.lower(), tipo.lower()))
        partes.append(f"{n} {uno if n == 1 else varios}")
    return ", ".join(partes) if partes else "no encontró datos personales"


def tachar(archivo: Path, salida: Path) -> bool:
    salida.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run(
        [str(PROGRAMA), str(archivo), "--config", str(CONFIG), "--format", "md,source", "--out-dir", str(salida), "-q"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
    )
    md = salida / f"{archivo.stem}.anonymized.md"
    if r.returncode != 0 or not md.exists():
        print(f"  ✗ {archivo.name}: no se pudo tachar.")
        detalle = (r.stderr or r.stdout).strip().splitlines()
        if detalle:
            print(f"    {detalle[-1]}")
        return False
    cabecera = md.read_text(encoding="utf-8").split("---")[1]
    conteo = (yaml.safe_load(cabecera) or {}).get("entity_counts") or {}
    print(f"  ✓ {archivo.name}")
    print(f"      tachó: {resumen(conteo)}")
    return True


def main() -> None:
    args = sys.argv[1:]
    salida_fija = None
    if "--salida" in args:
        i = args.index("--salida")
        salida_fija = Path(args[i + 1])
        del args[i:i + 2]
    archivos: list[Path] = []
    for a in args:
        p = Path(a)
        if p.is_dir():
            archivos += sorted(x for x in p.iterdir() if x.suffix.lower() in TIPOS)
        elif p.suffix.lower() in TIPOS:
            archivos.append(p)
        else:
            print(f"  · {p.name}: sólo se aceptan PDF, Word (.docx) o texto.")
    hechos = 0
    ultima = None
    for f in archivos:
        destino = salida_fija or (f.parent / "Tachados")
        if tachar(f, destino):
            hechos += 1
            ultima = destino
    print()
    print(f"  {hechos} de {len(archivos)} documentos tachados.")
    if ultima:
        print(f"  Quedaron en: {ultima}")
        # Para que el .bat sepa qué carpeta abrir
        (RAIZ / ".ultima-salida").write_text(str(ultima), encoding="utf-8")


if __name__ == "__main__":
    main()
