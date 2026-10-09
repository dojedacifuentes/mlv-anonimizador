"""Mide qué tacha el anonimizador en los documentos ficticios.

Uso: python pruebas/medir.py [--solo mlv]
Escribe pruebas/resultados.json y los textos tachados en pruebas/salida/.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))

from corpus import DOCUMENTOS, RESERVA  # noqa: E402

from anonymizer.anonymize.config import AnonymizerConfig, load_config  # noqa: E402
from anonymizer.anonymize.engine import DocumentAnonymizer  # noqa: E402

logging.disable(logging.WARNING)


def variantes() -> dict[str, tuple[str, AnonymizerConfig, str]]:
    original = AnonymizerConfig()
    original.lang = "en,fi"  # lo que el programa trae: inglés y finés
    solo_es = AnonymizerConfig()
    solo_es.lang = "es"
    solo_es.spacy_models = {"es": "es_core_news_lg"}
    mlv = load_config(RAIZ / "paquete-chile" / "config-mlv.yaml")
    return {
        "original": ("Programa original (inglés y finés)", original, "en,fi"),
        "espanol": ("Con español, sin Paquete Chile", solo_es, "es"),
        "mlv": ("Con español y Paquete Chile", mlv, "es"),
    }


# Palabras genéricas que pueden quedar a la vista sin identificar a nadie
GENERICAS = {
    "los", "las", "del", "de", "la", "el", "depto", "departamento", "oficina", "calle", "avenida", "av", "pasaje",
    "comuna", "villa", "limitada", "ltda", "spa", "servicios", "constructora", "inversiones", "transportes",
    "sociedad", "fojas", "número", "numero",
}


def _veces(pieza: str, texto: str) -> int:
    return len(re.findall(rf"(?<!\w){re.escape(pieza)}(?!\w)", texto))


def fugas(dato: str, original: str, salida: str) -> list[str]:
    """Pedazos del dato que siguen a la vista: palabras de 3+ letras o números de 3+ cifras.

    No cuenta un pedazo que el documento también usa en otra parte («2025» de una fecha, «correo» de un rótulo).
    """
    piezas = re.findall(r"[^\W\d_]{3,}|\d{3,}", dato)
    otras_partes = original.replace(dato, " ")
    return [
        p for p in piezas
        if p.lower() not in GENERICAS and _veces(p, otras_partes) == 0 and _veces(p, salida) > 0
    ]


def evaluar(doc: dict, salida: str) -> dict:
    original = doc["texto"]
    debe = []
    for t, k in doc["debe"]:
        f = fugas(t, original, salida) if t not in salida else [t]
        debe.append({"texto": t, "tipo": k, "tachado": not f, "fugas": f,
                     "estado": "completo" if not f else ("escapado" if t in salida else "parcial")})
    queda = [{"texto": t, "intacto": t in salida} for t in doc["queda"]]
    sensibles = [{"texto": t, "presente": t in salida} for t in doc.get("sensibles", [])]
    return {"debe": debe, "queda": queda, "sensibles": sensibles}


def main() -> None:
    elegidas = sys.argv[sys.argv.index("--solo") + 1].split(",") if "--solo" in sys.argv else None
    reserva = "--reserva" in sys.argv
    documentos = RESERVA if reserva else DOCUMENTOS
    (AQUI / "salida").mkdir(exist_ok=True)
    resultados: dict = {"variantes": {}}
    for clave, (nombre, cfg, lang) in variantes().items():
        if elegidas and clave not in elegidas:
            continue
        motor = DocumentAnonymizer(cfg)
        docs = []
        for doc in documentos:
            r = motor.anonymize_text(doc["texto"], lang_flag=lang)
            (AQUI / "salida" / f"{doc['id']}.{clave}.txt").write_text(r.anonymized_text, encoding="utf-8")
            ev = evaluar(doc, r.anonymized_text)
            ev.update(id=doc["id"], titulo=doc["titulo"], conteo=r.entity_counts)
            docs.append(ev)
        tot = sum(len(d["debe"]) for d in docs)
        ok = sum(x["tachado"] for d in docs for x in d["debe"])
        qtot = sum(len(d["queda"]) for d in docs)
        qok = sum(x["intacto"] for d in docs for x in d["queda"])
        resultados["variantes"][clave] = {
            "nombre": nombre, "docs": docs,
            "tachados": ok, "total": tot, "intactos": qok, "total_queda": qtot,
        }
        print(f"{nombre:40s} tachó {ok}/{tot} ({100 * ok / tot:.0f} %) · respetó {qok}/{qtot}")
        for d in docs:
            for x in d["debe"]:
                if not x["tachado"]:
                    print(f"    {x['estado']}: [{x['tipo']}] {x['texto']}  → quedó a la vista: {', '.join(x['fugas'])}  ({d['id']})")
            for x in d["queda"]:
                if not x["intacto"]:
                    print(f"    tachó de más: {x['texto']}  ({d['id']})")
    (AQUI / ("resultados-reserva.json" if reserva else "resultados.json")).write_text(json.dumps(resultados, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
