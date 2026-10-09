"""Anonimizador Jurídico MLV: ventana local (se abre en el navegador, sin internet).

Sólo escucha en 127.0.0.1: ningún otro equipo puede conectarse. Los documentos se procesan en la
carpeta .trabajo/, que se borra al abrir y al cerrar el programa. Se cierra solo cuando se cierra la pestaña.

Uso: .venv/Scripts/pythonw.exe app/servidor.py
"""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import sys
import threading
import time
import unicodedata
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

# pythonw no tiene consola: lo que el motor imprima va a la nada
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
APP = Path(__file__).resolve().parent
TRABAJO = RAIZ / ".trabajo"
CONFIG = RAIZ / "paquete-chile" / "config-mlv.yaml"
PUERTO = 8765
MAX_BYTES = 60 * 1024 * 1024
TIPOS = {".pdf", ".docx", ".txt", ".md"}

ETIQUETAS = {
    "PERSON": "Persona", "RUT": "RUT o documento", "ORG": "Empresa", "STREET": "Dirección",
    "CITY": "Comuna o lugar", "LOCATION": "Lugar", "PHONE": "Teléfono", "EMAIL": "Correo",
    "CAUSA": "Rol de causa", "PROPIEDAD": "Propiedad", "PATENTE": "Patente", "CUENTA": "Cuenta bancaria",
    "URL": "Enlace", "IP": "Dirección IP", "CREDIT_CARD": "Tarjeta", "IBAN": "Cuenta bancaria",
}

# Alertas de datos sensibles (art. 2 Ley 19.628 reformada): no se tachan solos, se avisan para revisión.
SENSIBLES = [
    ("Salud", r"licencias?\s+m[eé]dicas?|diagn[oó]stic\w*|trastorno\w*|enfermedad\w*|tratamiento\s+(?:m[eé]dico|psiqui[aá]tric\w*|psicol[oó]gic\w*)|"
              r"psiqui[aá]tr\w*|psicol[oó]g\w*|depresi[oó]n|ansiedad|ansios\w*|embaraz\w*|discapacidad|vih|c[aá]ncer|"
              r"licencia\s+por\s+\w+|hospitaliza\w*|cirug[ií]a|medicamento\w*|ficha\s+cl[ií]nica"),
    ("Afiliación sindical", r"sindica\w*|afiliad[oa]s?\s+al\s+sindicato|dirigente\s+sindical"),
    ("Religión o creencias", r"religi[oó]n|religios\w*|cat[oó]lic\w*|evang[eé]lic\w*|creencias?"),
    ("Vida u orientación sexual", r"orientaci[oó]n\s+sexual|homosexual\w*|lesbiana|bisexual\w*|identidad\s+de\s+g[eé]nero|trans(?:g[eé]nero|exual)\w*"),
    ("Origen étnico", r"origen\s+(?:[eé]tnico|racial)|ind[ií]gena|mapuche|aymara|rapa\s?nui"),
    ("Antecedentes penales", r"antecedentes\s+penales|condena\w*|privad[oa]\s+de\s+libertad"),
    ("Datos biométricos", r"huella\s+(?:digital|dactilar)|biom[eé]tric\w*|reconocimiento\s+facial"),
    ("Niños, niñas y adolescentes", r"menor(?:es)?\s+de\s+edad|ni[ñn][oa]s?\b|adolescente\w*"),
]

CANDADO = threading.Lock()
ULTIMO_LATIDO = [0.0]


def plegar(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def limpiar_trabajo() -> None:
    shutil.rmtree(TRABAJO, ignore_errors=True)


def calentar_motor() -> None:
    """Carga el modelo de español en segundo plano para que el primer documento sea rápido."""
    try:
        from anonymizer.anonymize.config import load_config
        from anonymizer.anonymize.engine import DocumentAnonymizer

        with CANDADO:
            DocumentAnonymizer(load_config(CONFIG)).anonymize_text("Contrato entre don Juan Pérez Soto y la empresa.", lang_flag="es")
    except Exception:  # noqa: BLE001
        pass


def texto_de(path: Path) -> str:
    suf = path.suffix.lower()
    if suf == ".pdf":
        import pymupdf

        with pymupdf.open(path) as d:
            return "\n".join(p.get_text() for p in d)
    if suf == ".docx":
        from docx import Document

        return "\n".join(p.text for p in Document(path).paragraphs)
    return path.read_text(encoding="utf-8", errors="replace")


def vistas_pdf(origen: Path, destino: Path, prefijo: str, max_paginas: int = 8) -> list[str]:
    import pymupdf

    nombres = []
    with pymupdf.open(origen) as d:
        for i, pagina in enumerate(d):
            if i >= max_paginas:
                break
            nombre = f"{prefijo}-{i + 1}.png"
            pagina.get_pixmap(dpi=110).save(destino / nombre)
            nombres.append(nombre)
    return nombres


def alertas_sensibles(texto: str) -> list[dict]:
    """Busca en el texto YA tachado palabras de datos sensibles y devuelve un trozo de contexto."""
    plano = " ".join(texto.split())
    out = []
    for categoria, patron in SENSIBLES:
        # Junta los hallazgos cercanos de una misma categoría en un solo aviso
        grupos: list[list[re.Match]] = []
        for m in re.finditer(rf"(?i)(?<!\w)(?:{patron})", plano):
            if grupos and m.start() - grupos[-1][-1].end() < 90:
                grupos[-1].append(m)
            else:
                grupos.append([m])
        for g in grupos:
            a, b = max(0, g[0].start() - 70), min(len(plano), g[-1].end() + 70)
            # No cortar una etiqueta [PERSON_4] por la mitad en los bordes
            # Empieza y termina en palabra completa
            while 0 < a < len(plano) and plano[a - 1].isalnum():
                a += 1
            while b < len(plano) and plano[b].isalnum():
                b += 1
            if plano.rfind("[", 0, a) > plano.rfind("]", 0, a):
                a = plano.rfind("[", 0, a)
            if plano.find("]", b) != -1 and (plano.find("[", b) == -1 or plano.find("]", b) < plano.find("[", b)):
                b = plano.find("]", b) + 1
            partes, cursor = [], a
            for m in g:
                partes.append({"texto": plano[cursor:m.start()], "marca": False})
                partes.append({"texto": m.group(0), "marca": True})
                cursor = m.end()
            partes.append({"texto": plano[cursor:b], "marca": False})
            partes[0]["texto"] = ("…" if a > 0 else "") + partes[0]["texto"]
            partes[-1]["texto"] += "…" if b < len(plano) else ""
            out.append({"categoria": categoria, "partes": partes})
    return out


def tachar(nombre: str, datos: bytes) -> dict:
    from anonymizer import cli

    suf = Path(nombre).suffix.lower()
    if suf not in TIPOS:
        raise ValueError("Sólo se aceptan PDF, Word (.docx) o texto.")
    ident = uuid.uuid4().hex[:12]
    carpeta = TRABAJO / ident
    carpeta.mkdir(parents=True)
    limpio = re.sub(r"[^\w.\- ]", "_", Path(nombre).name).strip() or f"documento{suf}"
    original = carpeta / limpio
    original.write_bytes(datos)
    mapa = carpeta / "mapa.json"
    inicio = time.time()
    with CANDADO:
        cli._run_pipeline(  # noqa: SLF001 — mismo camino que la línea de comandos
            original, mode="strict", output=None, out_dir=carpeta, map_path=mapa, lang="es", config=CONFIG,
            entities=None, score_threshold=None, include_dates=False, force_ocr=False, no_ocr=False,
            keep_headers=False, review=False, review_cli=False, review_window=False, reject=None,
            redact_style=None, output_format="md,source", llm=False, llm_provider=None, llm_model=None,
            offline=True, quiet=True, verbose=False,
        )
    segundos = round(time.time() - inicio, 1)
    stem = original.stem
    tachado = next((p for p in carpeta.glob(f"{stem}.anonymized{suf}")), None)
    md = carpeta / f"{stem}.anonymized.md"
    texto_tachado = md.read_text(encoding="utf-8").split("---", 2)[-1].strip() if md.exists() else ""
    reemplazos = json.loads(mapa.read_text(encoding="utf-8")) if mapa.exists() else {}

    # Agrupa por dato: [PERSON_1] → «Persona 1»
    hallazgos = []
    for marca, valor in reemplazos.items():
        m = re.fullmatch(r"\[(.+)_(\d+)\]", marca)
        base = m.group(1) if m else marca.strip("[]")
        hallazgos.append({"marca": marca, "tipo": ETIQUETAS.get(base, base.title()), "valor": valor,
                          "n": int(m.group(2)) if m else 0})
    # Un mismo dato con dos etiquetas («Viña del Mar» como lugar y como empresa) se cuenta una vez
    unicos, vistos = [], set()
    for h in hallazgos:
        clave = " ".join(h["valor"].casefold().split())
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(h)
    conteo: dict[str, int] = {}
    for h in unicos:
        conteo[h["tipo"]] = conteo.get(h["tipo"], 0) + 1

    res = {
        "id": ident, "nombre": limpio, "formato": suf.lstrip("."), "segundos": segundos,
        "descarga": tachado.name if tachado else None, "conteo": conteo, "hallazgos": hallazgos, "unicos": unicos,
        "texto_original": texto_de(original), "texto_tachado": texto_tachado,
        "sensibles": alertas_sensibles(texto_tachado), "vistas_antes": [], "vistas_despues": [],
    }
    if suf == ".pdf" and tachado:
        res["vistas_antes"] = vistas_pdf(original, carpeta, "antes")
        res["vistas_despues"] = vistas_pdf(tachado, carpeta, "despues")
    # El mapa tiene los datos reales: no queda en disco más de lo necesario
    mapa.unlink(missing_ok=True)
    return res


class Manejador(BaseHTTPRequestHandler):
    def log_message(self, *args) -> None:  # noqa: ANN002 — sin registro: las rutas podrían llevar nombres
        return

    def _enviar(self, codigo: int, cuerpo: bytes, tipo: str, extra: dict | None = None) -> None:
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(cuerpo)

    def _json(self, codigo: int, datos: dict) -> None:
        self._enviar(codigo, json.dumps(datos, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _archivo_trabajo(self, ident: str, nombre: str) -> Path | None:
        if not re.fullmatch(r"[0-9a-f]{12}", ident):
            return None
        p = (TRABAJO / ident / nombre).resolve()
        return p if p.is_file() and p.parent == (TRABAJO / ident).resolve() else None

    def do_GET(self) -> None:  # noqa: N802
        ruta = unquote(self.path.split("?", 1)[0])
        if ruta in ("/", "/index.html"):
            self._enviar(200, (APP / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif ruta == "/latido":
            ULTIMO_LATIDO[0] = time.time()
            self._json(200, {"ok": True})
        elif ruta.startswith("/archivo/"):
            partes = ruta.split("/", 3)
            p = self._archivo_trabajo(partes[2], partes[3]) if len(partes) == 4 else None
            if not p:
                self._json(404, {"error": "No encontrado"})
                return
            tipos = {".png": "image/png", ".pdf": "application/pdf",
                     ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                     ".md": "text/markdown; charset=utf-8", ".txt": "text/plain; charset=utf-8"}
            extra = {}
            if p.suffix != ".png":
                bonito = p.name.replace(".anonymized", " (tachado)")
                ascii_ = plegar(bonito).encode("ascii", "replace").decode().replace('"', "")
                extra["Content-Disposition"] = f"attachment; filename=\"{ascii_}\"; filename*=UTF-8''{_quote(bonito)}"
            self._enviar(200, p.read_bytes(), tipos.get(p.suffix, "application/octet-stream"), extra)
        else:
            self._json(404, {"error": "No encontrado"})

    def do_POST(self) -> None:  # noqa: N802
        ruta = self.path.split("?", 1)[0]
        if ruta == "/tachar":
            largo = int(self.headers.get("Content-Length") or 0)
            if largo <= 0 or largo > MAX_BYTES:
                self._json(400, {"error": "El archivo está vacío o pesa más de 60 MB."})
                return
            nombre = unquote(self.headers.get("X-Nombre") or "documento.pdf")
            datos = self.rfile.read(largo)
            try:
                self._json(200, tachar(nombre, datos))
            except SystemExit:
                self._json(500, {"error": "El programa no pudo leer este documento. ¿Está protegido con contraseña o dañado?"})
            except Exception as exc:  # noqa: BLE001
                self._json(500, {"error": f"No se pudo tachar: {exc}"})
        elif ruta.startswith("/abrir/"):
            ident = ruta.split("/")[2]
            carpeta = TRABAJO / ident
            if re.fullmatch(r"[0-9a-f]{12}", ident) and carpeta.is_dir():
                os.startfile(carpeta)  # noqa: S606 — carpeta local generada por este programa
                self._json(200, {"ok": True})
            else:
                self._json(404, {"error": "No encontrado"})
        elif ruta == "/cerrar":
            self._json(200, {"ok": True})
            threading.Thread(target=apagar, daemon=True).start()
        else:
            self._json(404, {"error": "No encontrado"})


def _quote(s: str) -> str:
    from urllib.parse import quote

    return quote(s)


SERVIDOR: list[ThreadingHTTPServer] = []


def apagar() -> None:
    time.sleep(0.3)
    if SERVIDOR:
        SERVIDOR[0].shutdown()


def vigilar() -> None:
    """Se cierra solo si la pestaña lleva 25 segundos cerrada."""
    while True:
        time.sleep(5)
        if ULTIMO_LATIDO[0] and time.time() - ULTIMO_LATIDO[0] > 25:
            apagar()
            return


def main() -> None:
    url = f"http://127.0.0.1:{PUERTO}/"
    try:
        servidor = ThreadingHTTPServer(("127.0.0.1", PUERTO), Manejador)
    except OSError:
        webbrowser.open(url)  # ya estaba abierto: sólo muestra la ventana
        return
    SERVIDOR.append(servidor)
    limpiar_trabajo()
    TRABAJO.mkdir(exist_ok=True)
    threading.Thread(target=calentar_motor, daemon=True).start()
    threading.Thread(target=vigilar, daemon=True).start()
    if not os.environ.get("MLV_SIN_NAVEGADOR"):
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    finally:
        servidor.server_close()
        limpiar_trabajo()


if __name__ == "__main__":
    main()
