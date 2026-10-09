"""Convierte los documentos ficticios en Word y PDF, para probar el tachado dentro del archivo original."""
import sys
from pathlib import Path

import fitz  # PyMuPDF
from docx import Document
from docx.shared import Pt

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from corpus import DOCUMENTOS, RESERVA  # noqa: E402

dest = AQUI / "archivos"
dest.mkdir(exist_ok=True)
for doc in DOCUMENTOS + RESERVA:
    d = Document()
    d.core_properties.author = "Autor de prueba"
    for par in doc["texto"].strip().split("\n"):
        p = d.add_paragraph(par)
        for r in p.runs:
            r.font.size = Pt(11)
    d.save(dest / f"{doc['id']}.docx")

    pdf = fitz.open()
    lineas = doc["texto"].strip().split("\n")
    pagina, y = None, 0
    for linea in lineas:
        trozos = [linea[i:i + 95] for i in range(0, max(len(linea), 1), 95)] if linea else [""]
        # corta en palabras para no partir nombres
        trozos, actual = [], ""
        for w in linea.split(" "):
            if len(actual) + len(w) + 1 > 95:
                trozos.append(actual)
                actual = w
            else:
                actual = f"{actual} {w}".strip()
        trozos.append(actual)
        for t in trozos:
            if pagina is None or y > 800:
                pagina, y = pdf.new_page(width=595, height=842), 60
            pagina.insert_text((50, y), t, fontsize=10, fontname="helv")
            y += 14
    pdf.set_metadata({"author": "Autor de prueba", "title": doc["titulo"]})
    pdf.save(dest / f"{doc['id']}.pdf")
print("ok", len(list(dest.iterdir())))
