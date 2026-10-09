"""Paquete Chile: reconocedores de datos personales chilenos para el anonimizador.

Cada clase detecta un tipo de dato. Se cargan desde config-mlv.yaml (sección recognizers).
Las reglas y las listas de nombres vienen del tachador de MLV (tachar.html), pasadas a Python.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import List, Optional

from presidio_analyzer import AnalysisExplanation, EntityRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

_LISTAS = json.loads((Path(__file__).with_name("listas.json")).read_text(encoding="utf-8"))
NOMBRES = set(_LISTAS["nombres"])
AMBIGUOS = set(_LISTAS["ambiguos"])
APELLIDOS = set(_LISTAS["apellidos"])
STOP = set(_LISTAS["stop"])

# Piezas de expresiones (Python no tiene \p{L}: [^\W\d_] es «una letra»)
LET = r"[^\W\d_]"
NOLET = rf"(?<!{LET})"
NOLET_AFTER = rf"(?!{LET})"
MAY = "[A-ZÁÉÍÓÚÑÜ]"
PAL = rf"(?:{LET}|['’-])+"
SP = r"[ \t]+"
NUM = r"(?:N\s?[°º.]\s*|n\s?[°º.]\s*|número\s+|Nro\.?\s*)?:?\s*"
MESES = "(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)"
HONOR = (
    rf"{NOLET}(?:[Dd]on|[Dd]oña|DON|DOÑA|[Ss]eñora|[Ss]eñorita|[Ss]eñor|SEÑORA|SEÑOR|"
    r"[Ss]rta\.|[Ss]ra\.|[Ss]r\.|[Dd]ra\.?|[Dd]r\.|[Ii]ng\.|[Pp]rof\.|[Ll]ic\.)"
)
NOMBRE = rf"{MAY}{PAL}(?:{SP}(?:de{SP}(?:la{SP}|las{SP}|los{SP})?|del{SP})?{MAY}{PAL}){{0,4}}"
NO_SON_NOMBRES = {
    "juez", "jueza", "ministro", "ministra", "presidente", "presidenta", "fiscal", "notario", "notaria",
    "conservador", "secretario", "secretaria", "tribunal", "abogado", "abogada", "defensor", "defensora",
    "receptor", "receptora", "relator", "relatora", "director", "directora", "gerente", "alcalde",
    "alcaldesa", "administrador", "liquidador", "inspector", "inspectora",
}


def plegar(s: str) -> str:
    """Minúsculas y sin tildes («Pérez» → «perez»)."""
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def rut_valido(cuerpo: str, dv: str) -> bool:
    """Dígito verificador del RUT (módulo 11)."""
    s, m = 0, 2
    for d in reversed(cuerpo):
        s += int(d) * m
        m = 2 if m == 7 else m + 1
    r = 11 - (s % 11)
    esperado = "0" if r == 11 else "K" if r == 10 else str(r)
    return esperado == dv.upper()


class _Base(EntityRecognizer):
    """Reconocedor por reglas: (expresión, grupo, puntaje)."""

    ENTIDAD = "CUSTOM"
    REGLAS: list[tuple[re.Pattern[str], int, float]] = []

    def __init__(self) -> None:
        super().__init__(
            supported_entities=[self.ENTIDAD],
            supported_language="en",
            name=type(self).__name__,
        )

    def load(self) -> None:
        return

    def aceptar(self, texto: str, inicio: int, fin: int) -> float | None:
        """Puntaje final para un hallazgo (None = descartarlo)."""
        return 1.0

    def resultado(self, inicio: int, fin: int, puntaje: float, regla: str) -> RecognizerResult:
        return RecognizerResult(
            entity_type=self.ENTIDAD,
            start=inicio,
            end=fin,
            score=puntaje,
            analysis_explanation=AnalysisExplanation(
                recognizer=self.name,
                original_score=puntaje,
                pattern_name=regla,
                pattern=None,
                validation_result=True,
            ),
        )

    def analyze(
        self,
        text: str,
        entities: List[str],
        nlp_artifacts: NlpArtifacts = None,  # noqa: ANN001
        regex_flags: Optional[int] = None,  # noqa: ARG002
    ) -> List[RecognizerResult]:
        if entities and self.ENTIDAD not in entities:
            return []
        out: list[RecognizerResult] = []
        for i, (rx, grupo, puntaje) in enumerate(self.REGLAS):
            for m in rx.finditer(text):
                a, b = m.span(grupo)
                if a < 0 or a >= b:
                    continue
                # Sin espacios ni puntuación sobrantes en los bordes
                while b > a and text[b - 1] in " \t.,;:":
                    b -= 1
                while a < b and text[a] in " \t":
                    a += 1
                factor = self.aceptar(text, a, b)
                if factor is None:
                    continue
                out.append(self.resultado(a, b, round(puntaje * factor, 3), f"{self.name}:{i}"))
        return out


class ClRutRecognizer(_Base):
    """RUT y RUN (con o sin puntos), validados con el dígito verificador; pasaportes con rótulo."""

    ENTIDAD = "CL_RUT"
    _RUT = re.compile(r"(?<![\w.-])(?:\d{1,2}\.\d{3}\.\d{3}|\d{7,8})\s?-\s?[\dkK](?!\w)")
    REGLAS = [
        (_RUT, 0, 0.95),
        (
            re.compile(
                rf"{NOLET}(?:[Pp]asaporte|PASAPORTE|DNI|[Cc]édula de extranjería|[Dd]ocumento de identidad)"
                rf"\s*{NUM}([A-Z0-9][A-Z0-9.-]{{4,15}})"
            ),
            1,
            0.85,
        ),
    ]

    def aceptar(self, texto: str, inicio: int, fin: int) -> float | None:
        s = re.sub(r"[.\s]", "", texto[inicio:fin]).upper()
        if "-" in s and re.fullmatch(r"\d{7,8}-[\dK]", s):
            cuerpo, dv = s.split("-")
            # Un RUT con dígito equivocado igual se tacha, pero con menos certeza (para revisarlo).
            return 1.0 if rut_valido(cuerpo, dv) else 0.65
        return 1.0


class ClCausaRecognizer(_Base):
    """Rol, RIT y RUC de causas judiciales y de fiscalía."""

    ENTIDAD = "CL_CAUSA"
    REGLAS = [
        (
            re.compile(
                rf"{NOLET}(?:RIT|RUC|ROL|Rol|rol|Rit|Ruc)\.?\s*{NUM}"
                r"([A-Za-z]{0,3}-?\s?\d[\d.]*(?:-\d+)*(?:-[\dkK])?)"
            ),
            1,
            0.9,
        ),
        (re.compile(r"(?<![\w-])[A-Z]{1,2}-\d{1,6}-\d{4}(?![\w-])"), 0, 0.85),
        (re.compile(r"(?<![\d.])\d{10}-[\dkK](?!\w)"), 0, 0.85),
    ]

    def aceptar(self, texto: str, inicio: int, fin: int) -> float | None:
        # «Rol de avalúo» es de la propiedad, no de una causa
        antes = texto[max(0, inicio - 30):inicio].lower()
        if "avalúo" in antes or "avaluo" in antes or "sii" in antes:
            return None
        return 1.0


class ClPropiedadRecognizer(_Base):
    """Inscripciones del Conservador y roles de avalúo del SII."""

    ENTIDAD = "CL_PROPIEDAD"
    REGLAS = [
        (
            re.compile(
                # Sólo los números: «del Registro de Propiedad del Conservador…» no identifica a nadie
                r"(?i)fojas\s+\d[\d.]*\s*(?:vuelta\s*)?,?\s*(?:n(?:ú|u)mero|n\s?[°º.])\s*\d[\d.]*"
            ),
            0,
            0.9,
        ),
        (
            re.compile(r"(?i)rol\s+(?:de\s+)?(?:avalúo|avaluo|sii|de\s+avalúo\s+fiscal)\s*(?:n\s?[°º.]\s*)?:?\s*(\d{1,5}-\d{1,4})"),
            1,
            0.9,
        ),
    ]


class ClPatenteRecognizer(_Base):
    """Patentes de vehículos (formato nuevo BBBB·12 y antiguo AA·12·34)."""

    ENTIDAD = "CL_PATENTE"
    REGLAS = [
        (
            re.compile(
                r"(?<![\w-])(?:[B-DF-HJ-LPR-TV-Z]{4}[\s·.-]?\d{2}|[A-Z]{2}[\s·.-]?\d{2}[\s·.-]?\d{2})(?![\w-])"
            ),
            0,
            0.8,
        ),
    ]


class ClCuentaRecognizer(_Base):
    """Cuentas bancarias y tarjetas."""

    ENTIDAD = "CL_CUENTA"
    REGLAS = [
        (
            re.compile(
                r"(?i)(?:cuenta(?:\s+(?:corriente|vista|rut|de\s+ahorros?|bancaria))?|cta\.?\s*cte\.?|"
                r"tarjeta(?:\s+de\s+(?:crédito|débito))?)\s*(?:n\s?[°º.]?|número|nro\.?)?\s*:?\s*(\d[\d\s-]{4,22}\d)"
            ),
            1,
            0.9,
        ),
        (re.compile(r"(?<!\d)(?:\d{4}[\s-]){3}\d{4}(?!\d)"), 0, 0.85),
    ]


class ClTelefonoRecognizer(_Base):
    """Teléfonos chilenos (+56, celulares 9 XXXX XXXX, con rótulo)."""

    ENTIDAD = "PHONE_NUMBER"
    REGLAS = [
        (re.compile(r"(?<![\d+])\+?\s?56[\s-]?\(?\d{1,2}\)?[\s-]?\d{3,4}[\s-]?\d{4}(?!\d)"), 0, 0.9),
        (re.compile(r"\(\d{1,2}\)\s?\d{3,4}[\s-]?\d{4}(?!\d)"), 0, 0.85),
        (re.compile(r"(?<![\d.$])9[\s-]?\d{4}[\s-]?\d{4}(?!\d|\.\d)"), 0, 0.8),
        (
            re.compile(r"(?i)(?:tel[ée]fono|fono|celular|m[óo]vil|whatsapp)\s*(?:n\s?[°º.]\s*)?:?\s*(\+?\d[\d\s-]{6,16}\d)"),
            1,
            0.9,
        ),
    ]


_DEPTO = r"(?:\s*,?\s*(?:depto\.?|departamento|dpto\.?|oficina|of\.|casa|block|torre|piso)\s*[\w-]+)*"


class ClDireccionRecognizer(_Base):
    """Direcciones: «domiciliado en …» y «calle/avenida/pasaje … número»."""

    ENTIDAD = "STREET"
    REGLAS = [
        (
            re.compile(
                r"(?i)(?:domiciliad[oa]s?|con\s+domicilio|domicilio|residente|reside|vive)\s+en\s+"
                rf"([^\n,;()]{{2,60}}?\s(?:n\s?[°º.]\s*)?\d{{1,5}}{_DEPTO})"
            ),
            1,
            0.9,
        ),
        (
            re.compile(
                rf"(?i){NOLET}(?:calle|avenida|av\.|avda\.|pasaje|psje\.|camino|callejón|parcela)\s+"
                rf"[^\n,;()]{{2,60}}?\s(?:n\s?[°º.]\s*)?\d{{1,5}}{_DEPTO}"
            ),
            0,
            0.9,
        ),
    ]


_SUFIJO = r"(?:S\.\s?A\.|SpA|SPA|S\.p\.A\.|Ltda\.?|LTDA\.?|Limitada|LIMITADA|E\.I\.R\.L\.?|EIRL)"
_RUBRO = (
    "(?:Inmobiliaria|Constructora|Comercial|Sociedad|Inversiones|Transportes|Servicios|Agrícola|Distribuidora|"
    "Importadora|Exportadora|Clínica|Colegio|Fundación|Corporación|Consultora|Asesorías|Minera|Pesquera|Viña|"
    "Restaurante|Farmacia|Laboratorio|Centro Médico|Hospital|Instituto|Liceo|Escuela|Compañía|Holding|Grupo|"
    "Automotora|Ferretería|Supermercados?|Empresas?|Hotel|Panadería|Botillería|Almacén|Jardín Infantil)"
)
_CAP = r"[A-ZÁÉÍÓÚÑÜ0-9][\w&'’.-]*"


class ClEmpresaRecognizer(_Base):
    """Empresas: razón social con SpA, Ltda., S.A., EIRL, o con rubro («Inmobiliaria Los Aromos»)."""

    ENTIDAD = "ORG"
    REGLAS = [
        (re.compile(rf"{_CAP}\s+(?:(?:{_CAP}|de|del|la|las|los|y|e|&)\s+){{0,6}}{_SUFIJO}(?!\w)"), 0, 0.9),
        (
            re.compile(rf"{NOLET}{_RUBRO}(?:[ \t]+(?:(?:de|del|la|las|los|y|e|&)[ \t]+)*[A-ZÁÉÍÓÚÑÜ0-9][\w&'’-]*){{1,5}}"),
            0,
            0.8,
        ),
    ]


class ClLugarRecognizer(_Base):
    """Comunas y lugares con rótulo («comuna de Maipú») y la ciudad de la fecha («En Temuco, a 3 de marzo»)."""

    ENTIDAD = "CITY"
    REGLAS = [
        (
            re.compile(
                rf"{NOLET}(?:[Cc]omuna|[Cc]iudad|[Ll]ocalidad|[Pp]rovincia|[Rr]egión|[Vv]illa|[Pp]oblación|[Ss]ector|"
                rf"[Cc]ondominio|[Pp]ueblo|[Cc]aleta|[Ii]sla|[Ll]oteo|[Cc]ampamento){SP}"
                rf"(?:(?:de|del){SP}(?:la{SP}|las{SP}|los{SP})?)?"
                rf"({MAY}{PAL}(?:{SP}(?:(?:de|del|la|las|los){SP})*{MAY}{PAL}){{0,3}})"
            ),
            1,
            0.85,
        ),
        (
            re.compile(
                rf"{NOLET}(?:[Ee]n{SP})?({MAY}{PAL}(?:{SP}(?:(?:de|del|la|las|los){SP})*{MAY}{PAL}){{0,3}}),{SP}(?:a{SP})?"
                rf"(?=\d{{1,2}}{SP}de{SP}{MESES})"
            ),
            1,
            0.8,
        ),
    ]


_ROLES = (
    r"(?:[Dd]emandante|[Dd]emandad[oa]|[Ii]mputad[oa]|[Qq]uerellante|[Qq]uerellad[oa]|[Vv]íctima|[Tt]rabajador(?:a)?|"
    r"[Aa]rrendador(?:a)?|[Aa]rrendatari[oa]|[Tt]estigo|[Cc]ausante|[Hh]ereder[oa]|[Cc]ónyuge|[Ss]olicitante|"
    r"[Rr]equirente|[Rr]equerid[oa]|[Cc]ontratante|[Aa]bogad[oa]|[Pp]aciente|[Cc]liente|[Ee]mpleador(?:a)?|"
    r"[Rr]epresentante legal|[Mm]adre|[Pp]adre|[Hh]ij[oa]|[Mm]enor|[Dd]enunciante|[Dd]enunciad[oa])"
)
_TRAS_MAYUS = (
    r"(?:[Cc]hilen|[Aa]rgentin|[Pp]eruan|[Vv]enezolan|[Cc]olombian|[Bb]olivian|[Hh]aitian|[Ee]xtranjer|[Cc]asad|"
    r"[Ss]olter|[Dd]ivorciad|[Vv]iud|[Mm]ayor de edad|[Mm]enor de edad|[Aa]bogad|[Ii]ngenier|[Ee]mplead|"
    r"[Cc]omerciante|[Pp]rofesor|[Ee]studiante|[Jj]ubilad|[Cc]édula|[Cc]\.\s?[Ii]\.|RUT|RUN|[Rr]ut|[Nn]acionalidad|"
    r"[Dd]omiciliad|[Dd]e profesión|[Dd]e oficio|[Mm]édic|[Cc]onductor|[Tt]écnic|[Dd]ueñ)"
)
_PALABRA_MAY = re.compile(rf"{NOLET}{MAY}(?:{LET}|['’])*(?:-(?:{LET}|['’])+)*")
_PARTICULA = {"de", "del", "la", "las", "los"}


class ClPersonaRecognizer(_Base):
    """Personas: por contexto (don, señora, demandante…, MAYÚSCULAS antes de «chileno») y por diccionario chileno."""

    ENTIDAD = "PERSON"
    REGLAS = [
        (re.compile(rf"{HONOR}\s+({NOMBRE})"), 1, 0.9),
        (re.compile(rf"{NOLET}((?:[A-ZÁÉÍÓÚÑÜ]{{2,}}{SP}){{1,4}}[A-ZÁÉÍÓÚÑÜ]{{2,}})(?=\s*,\s*{_TRAS_MAYUS})"), 1, 0.9),
        (
            re.compile(
                rf"{NOLET}{_ROLES}\s*,?\s*(?:{HONOR}\s+)?({MAY}{PAL}(?:{SP}(?:de{SP}(?:la{SP}|los{SP})?|del{SP})?{MAY}{PAL}){{1,4}})"
            ),
            1,
            0.85,
        ),
    ]

    def aceptar(self, texto: str, inicio: int, fin: int) -> float | None:
        palabras = [plegar(p) for p in texto[inicio:fin].split()]
        if not palabras or palabras[0] in NO_SON_NOMBRES:
            return None
        if all(p in STOP or p in _PARTICULA for p in palabras):
            return None
        return 1.0

    def _tramos(self, texto: str) -> list[list[tuple[str, int, int, bool]]]:
        """Tramos de palabras con mayúscula en la misma línea, cortados en palabras que no son de nombre."""
        tramos: list[list[tuple[str, int, int, bool]]] = []
        actual: list[tuple[str, int, int, bool]] = []
        fin_previo = -1

        def cerrar() -> None:
            nonlocal actual
            while actual and actual[-1][3]:
                actual.pop()
            if actual:
                tramos.append(actual)
            actual = []

        for m in re.finditer(rf"(?:{LET}|['’-])+", texto):
            w, a, b = m.group(0), m.start(), m.end()
            entre = texto[fin_previo:a] if fin_previo >= 0 else ""
            if fin_previo >= 0 and not re.fullmatch(r"[ \t]+", entre):
                cerrar()
            fin_previo = b
            f = plegar(w)
            if f in _PARTICULA and w.islower():
                if actual:
                    actual.append((f, a, b, True))
                continue
            if not w[0].isupper() or f in STOP or len(w) < 2:
                cerrar()
                continue
            actual.append((f, a, b, False))
        cerrar()
        return tramos

    def _por_diccionario(self, texto: str) -> list[tuple[int, int]]:
        """Nombre(s) conocido(s) + apellido(s), o dos apellidos conocidos seguidos (como el tachador)."""
        out: list[tuple[int, int]] = []
        for seg in self._tramos(texto):
            i = 0
            while i < len(seg):
                if seg[i][3]:
                    i += 1
                    continue
                j = i
                nombres = []
                while j < len(seg) and not seg[j][3] and seg[j][0] in NOMBRES:
                    nombres.append(seg[j])
                    j += 1
                if nombres:
                    apellidos = []
                    k = j
                    while k < len(seg) and len(apellidos) < 3:
                        if not seg[k][3]:
                            apellidos.append(seg[k])
                        k += 1
                    ambiguo = all(n[0] in AMBIGUOS for n in nombres)
                    if apellidos and (not ambiguo or apellidos[0][0] in APELLIDOS):
                        out.append((nombres[0][1], apellidos[-1][2]))
                        i = k
                        continue
                    if len(nombres) >= 2 and not ambiguo:
                        out.append((nombres[0][1], nombres[-1][2]))
                    i = j
                    continue
                if seg[i][0] in APELLIDOS:
                    n = next((x for x in range(i + 1, len(seg)) if not seg[x][3]), None)
                    if n is not None and seg[n][0] in APELLIDOS:
                        out.append((seg[i][1], seg[n][2]))
                        i = n + 1
                        continue
                i += 1
        return out

    def analyze(self, text, entities, nlp_artifacts=None, regex_flags=None):  # noqa: ANN001
        if entities and self.ENTIDAD not in entities:
            return []
        out = super().analyze(text, entities, nlp_artifacts, regex_flags)
        for a, b in self._por_diccionario(text):
            out.append(self.resultado(a, b, 0.85, f"{self.name}:diccionario"))
        return out


# ───────── Filtro final: lo que el modelo de lenguaje confunde en escritos chilenos ─────────
# Palabras jurídicas que el tachador ya conocía, más algunas de escrituras y finiquitos.
VOCABULARIO = STOP | {
    "propiedad", "hipotecas", "gravamenes", "prohibiciones", "finiquito", "remuneracion", "remuneraciones",
    "otrosi", "tanto", "merito", "expuesto", "ruego", "digo", "respetuosamente", "vengo", "interponer",
    "jefatura", "unidad", "cobranza", "antecedentes", "declaraciones", "conclusiones", "informe", "final",
    "investigacion", "investigadora", "investigador", "acoso", "laboral", "sexual", "denuncia", "denunciante",
    "denunciado", "denunciada", "empleador", "trabajadora", "trabajador", "afp", "fonasa", "isapre", "escritura",
    "comparecen", "vendedora", "vendedor", "comprador", "compradora", "inmueble", "precio", "vale", "vista",
    "sjl", "s.j.l", "ss", "s.s", "uf", "n", "nº", "n°", "primero", "segundo", "tercero", "cuarto", "quinto",
}
_ENTIDADES_NER = {"PERSON", "ORG", "LOCATION", "CITY", "NRP"}
# Instituciones públicas: su nombre no identifica a una persona («Juzgado de Familia de Quilpué»)
INSTITUCIONES = {
    "juzgado", "corte", "tribunal", "conservador", "registro", "notaria", "fiscalia", "inspeccion", "ministerio",
    "superintendencia", "contraloria", "tesoreria", "municipalidad", "direccion", "defensoria", "servicio",
    "hospital", "consultorio", "cesfam", "carabineros", "policia", "gendarmeria", "camara", "senado", "agencia",
    "consejo", "instituto", "subsecretaria", "seremi", "intendencia", "delegacion", "gobernacion",
}


def _palabras(texto: str) -> list[str]:
    return [plegar(w) for w in re.findall(rf"(?:{LET}|[.'’])+", texto) if w.strip(".")]


def filtrar(texto: str, resultados: list) -> list:
    """Limpia los hallazgos del modelo de lenguaje antes de tachar.

    - completa los cortes a mitad de palabra («OTROS|Í» → «OTROSÍ») antes de decidir;
    - descarta lo que es sólo vocabulario jurídico («PRIMER OTROSÍ», «POR TANTO», «Registro de Propiedad»);
    - quita saludos y rótulos del borde de un nombre («Estimada Francisca» → «Francisca»);
    - descarta el nombre de una ley («Ley Karin») y las letras sueltas («N°»).
    """
    salida = []
    for r in resultados:
        if r.entity_type not in _ENTIDADES_NER:
            salida.append(r)
            continue
        a, b = r.start, r.end
        while a > 0 and re.match(LET, texto[a - 1]):
            a -= 1
        while b < len(texto) and re.match(LET, texto[b]):
            b += 1
        partes = list(re.finditer(rf"(?:{LET}|['’])+", texto[a:b]))
        if not partes:
            continue
        if all(plegar(p.group(0)) in VOCABULARIO | _PARTICULA for p in partes):
            continue
        if r.entity_type != "PERSON" and plegar(partes[0].group(0)) in INSTITUCIONES:
            continue
        # En personas, recorta del borde saludos y rótulos («Estimada Francisca»). En empresas y lugares no:
        # «Viña del Mar» y «Servicios … Limitada» se tachan enteros.
        if r.entity_type == "PERSON":
            while partes and plegar(partes[0].group(0)) in VOCABULARIO | _PARTICULA:
                partes.pop(0)
            while partes and plegar(partes[-1].group(0)) in VOCABULARIO | _PARTICULA:
                partes.pop()
            a, b = a + partes[0].start(), a + partes[-1].end()
        superficie = texto[a:b]
        palabras = _palabras(superficie)
        if len(superficie.replace(" ", "")) <= 2:
            continue
        if all(p in VOCABULARIO or p in _PARTICULA for p in palabras):
            continue
        antes = plegar(texto[max(0, a - 12):a])
        if re.search(r"\bley\s+(?:n\s?[°º.]?\s*)?$", antes):
            continue
        # La ciudad de un tribunal u oficina pública («Juzgado de Letras del Trabajo de Santiago»)
        linea = plegar(texto[max(0, a - 80):a]).split("\n")[-1]
        if re.search(r"\b(?:juzgado|corte|tribunal|conservador|notaria|fiscalia|inspeccion)\b[^.;]*\bde\s+$", linea):
            continue
        # Una sola palabra que es nombre y lugar a la vez («SANTIAGO», «Rosario») sin apellido: no es persona
        if r.entity_type == "PERSON" and len(palabras) == 1 and palabras[0] in AMBIGUOS:
            continue
        r.start, r.end = a, b
        salida.append(r)
    return salida
