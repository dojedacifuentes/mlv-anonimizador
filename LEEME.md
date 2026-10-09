# Anonimizador Jurídico MLV · prueba de concepto (Fase 0)

> Nombre visible: **Tachador Jurídico**. Seudonimiza (cambia datos por etiquetas), no anonimiza: la copia sigue siendo un dato personal. El nombre del repositorio y el sufijo técnico `.anonymized` de los archivos vienen del programa original.

Prueba hecha el 09-10-2026: el anonimizador de código abierto [arcane-tl/anonymizer](https://github.com/arcane-tl/anonymizer)
(licencia MIT), con español y un **Paquete Chile**. Todo corre en este computador; no se envía nada a internet.

**No contiene datos reales.** Los documentos de `pruebas/` son ficticios: personas, RUT, causas y empresas inventados.
Repositorio: github.com/dojedacifuentes/mlv-anonimizador (debe ser **privado**). No mezclarlo con el repositorio público `mlv.abogados`. Los cambios al programa original están también en `motor-cambios-mlv.patch`.

## Qué hay

| Carpeta | Qué es |
|---|---|
| `motor/` | Copia del programa original (commit `5b8b7d1`, 03-10-2026; licencia MIT en `motor/LICENSE`) con cuatro cambios: español, filtros finales por configuración y el arreglo de un error del original (al procesar archivos ignoraba los tipos de dato de los complementos) |
| `paquete-chile/` | `chile.py` (RUT con dígito verificador, roles de causa, propiedad, patentes, cuentas, teléfonos, direcciones, empresas, comunas, personas con el diccionario chileno y filtro de vocabulario jurídico), `listas.json` (nombres y apellidos, sacados del tachador de MLV) y `config-mlv.yaml` |
| `pruebas/` | Documentos ficticios (`corpus.py`), medición (`medir.py`), archivos Word y PDF (`archivos/`), tachados (`tachados/`) y verificación (`verificar_archivos.py`) |
| `app/` | La ventana del programa (`servidor.py` + `index.html`) |
| `informe.html` | Resumen para la reunión con las cifras |

## Cómo se usa

**Sin comandos:** en el Escritorio hay dos accesos directos.
- **Tachador Jurídico (MLV):** abre la ventana del programa en el navegador. Funciona sin internet: sólo
  escucha en este computador (127.0.0.1). Arrastras un PDF o Word y muestra el antes y el después, la lista de lo
  tachado, las alertas de datos sensibles y el botón para descargar la copia. Se apaga solo al cerrar la pestaña
  (o con el botón «Cerrar») y borra sus archivos de trabajo (`.trabajo/`). Código en `app/`.
- **Probar tachador (ejemplos):** tacha los 12 archivos ficticios, comprueba que no quede nada a la vista y abre
  el informe y las carpetas de antes y después.
- `Tachar documento.bat` (en esta carpeta) sigue sirviendo para arrastrar varios archivos de una vez, en la ventana negra.

Por comandos:

```bash
.venv/Scripts/python -c "from anonymizer.cli import run; run()" documento.pdf --config paquete-chile/config-mlv.yaml --format md,source --out-dir salida
```

Genera el PDF o Word tachado (mismo formato) y una versión en texto. Para volver a medir:

```bash
.venv/Scripts/python pruebas/medir.py            # 4 documentos de ajuste
.venv/Scripts/python pruebas/medir.py --reserva  # 2 documentos nuevos
.venv/Scripts/python pruebas/verificar_archivos.py
```

(En Windows, anteponer `PYTHONIOENCODING=utf-8` si la consola muestra mal las tildes.)

## Instalación desde cero

Python 3.11 o superior; luego, en esta carpeta:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e "./motor[dev]"
.venv/Scripts/python -m spacy download es_core_news_lg
.venv/Scripts/python -m spacy download en_core_web_sm
```

El modelo de español pesa unos 570 MB.

## Lo que falta (Fase 1)

- Alertas de datos sensibles: la ventana ya las muestra (por palabras clave); falta poder tacharlas con un clic.
- Etiquetas en español (`[PERSONA_1]` en vez de `[PERSON_1]`).
- Más documentos de prueba, en especial escaneados (OCR), tablas y notas al pie.
- Las 6 pruebas propias del programa que fallan en Windows (por la carpeta de usuario `~`) también fallan sin nuestros cambios.
