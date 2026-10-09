"""Abre cada PDF y Word tachado y busca datos que hayan quedado: en el texto y en los metadatos."""
import json
import sys
from pathlib import Path

import pymupdf
from docx import Document

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from corpus import DOCUMENTOS, RESERVA  # noqa: E402
from medir import fugas  # noqa: E402


def texto_pdf(p: Path) -> tuple[str, str]:
    d = pymupdf.open(p)
    return "\n".join(pg.get_text() for pg in d), json.dumps(d.metadata, ensure_ascii=False)


def texto_docx(p: Path) -> tuple[str, str]:
    d = Document(p)
    cp = d.core_properties
    meta = json.dumps({"author": cp.author, "last_modified_by": cp.last_modified_by, "title": cp.title}, ensure_ascii=False)
    return "\n".join(par.text for par in d.paragraphs), meta


resumen = []
total = ok = 0
for doc in DOCUMENTOS + RESERVA:
    for ext, leer in ((".pdf", texto_pdf), (".docx", texto_docx)):
        p = AQUI / "tachados" / f"{doc['id']}.anonymized{ext}"
        txt, meta = leer(p)
        plano = " ".join(txt.split())
        quedan = []
        for dato, tipo in doc["debe"]:
            total += 1
            f = [dato] if " ".join(dato.split()) in plano else fugas(dato, " ".join(doc["texto"].split()), plano)
            if f:
                quedan.append(f"[{tipo}] {dato} → {', '.join(f)}")
            else:
                ok += 1
        autor = "Autor de prueba" in meta
        resumen.append({"archivo": p.name, "fugas": quedan, "autor_en_metadatos": autor})
        estado = "OK" if not quedan and not autor else "REVISAR"
        print(f"{estado:8s}{p.name}" + "".join(f"\n          {q}" for q in quedan) + ("\n          autor en metadatos" if autor else ""))
print(f"\nDatos tachados dentro de los archivos: {ok}/{total}")
(AQUI / "resultados-archivos.json").write_text(json.dumps({"ok": ok, "total": total, "archivos": resumen}, ensure_ascii=False, indent=1), encoding="utf-8")
