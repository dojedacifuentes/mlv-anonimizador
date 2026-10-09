"""Documentos de prueba FICTICIOS (personas, RUT, causas y empresas inventados).

Cada documento trae su respuesta correcta:
  debe  = lo que tiene que quedar tachado (con su tipo)
  queda = lo que NO se debe tachar (instituciones, normas, cargos)
"""

from __future__ import annotations


def rut(cuerpo: int) -> str:
    """RUT con dígito verificador correcto y puntos (12.345.678-5)."""
    s, m = 0, 2
    for d in reversed(str(cuerpo)):
        s += int(d) * m
        m = 2 if m == 7 else m + 1
    r = 11 - (s % 11)
    dv = "0" if r == 11 else "K" if r == 10 else str(r)
    return f"{cuerpo:,}".replace(",", ".") + f"-{dv}"


R1, R2, R3, R4, R5, R6 = rut(15834221), rut(9472118), rut(76543210), rut(18220943), rut(12904577), rut(21056334)

DOCUMENTOS = [
    {
        "id": "01-contrato-trabajo",
        "titulo": "Contrato de trabajo",
        "texto": f"""CONTRATO DE TRABAJO

En Santiago, a 14 de marzo de 2025, entre Inversiones Los Aromos SpA, RUT {R3}, representada legalmente por don Rodrigo Andrés Fuenzalida Tapia, cédula de identidad N° {R2}, ambos domiciliados en Avenida Apoquindo 4499, oficina 1203, comuna de Las Condes, en adelante «el Empleador»; y doña Camila Ignacia Sepúlveda Arancibia, chilena, soltera, cédula de identidad N° {R1}, domiciliada en Pasaje Los Jazmines 1187, comuna de Maipú, teléfono +56 9 8765 4321, correo camila.sepulveda.a@correo-ficticio.cl, en adelante «la Trabajadora», se ha convenido el siguiente contrato de trabajo, regido por el Código del Trabajo:

PRIMERO: La Trabajadora se desempeñará como analista contable.
SEGUNDO: La remuneración se pagará mediante depósito en la cuenta corriente N° 00-123-45678-09 del Banco del Estado de Chile.
TERCERO: La Trabajadora declara estar afiliada a AFP Modelo y a Fonasa.
CUARTO: Para todos los efectos legales, las partes fijan domicilio en la ciudad de Santiago y se someten a la competencia del Juzgado de Letras del Trabajo de Santiago.

Rodrigo Fuenzalida Tapia                          Camila Sepúlveda Arancibia
p.p. Inversiones Los Aromos SpA                   Trabajadora
""",
        "debe": [
            ("Inversiones Los Aromos SpA", "Empresa"),
            (R3, "RUT"),
            ("Rodrigo Andrés Fuenzalida Tapia", "Persona"),
            (R2, "RUT"),
            ("Avenida Apoquindo 4499, oficina 1203", "Dirección"),
            ("Camila Ignacia Sepúlveda Arancibia", "Persona"),
            (R1, "RUT"),
            ("Pasaje Los Jazmines 1187", "Dirección"),
            ("Maipú", "Comuna"),
            ("+56 9 8765 4321", "Teléfono"),
            ("camila.sepulveda.a@correo-ficticio.cl", "Correo"),
            ("00-123-45678-09", "Cuenta"),
            ("Rodrigo Fuenzalida Tapia", "Persona"),
            ("Camila Sepúlveda Arancibia", "Persona"),
        ],
        "queda": ["Código del Trabajo", "Juzgado de Letras del Trabajo de Santiago", "analista contable", "Fonasa"],
    },
    {
        "id": "02-informe-ley-karin",
        "titulo": "Informe de investigación (Ley Karin)",
        "texto": f"""INFORME FINAL DE INVESTIGACIÓN
Procedimiento de investigación por acoso laboral — Ley N° 21.643 (Ley Karin)

1. ANTECEDENTES
Con fecha 2 de junio de 2025, la trabajadora Valentina Paz Riquelme Ortiz, RUT {R4}, presentó una denuncia en contra de su jefatura directa, el señor Matías Ignacio Carrasco Bravo, RUT {R5}, por conductas constitutivas de acoso laboral. La denuncia fue remitida a la Inspección del Trabajo conforme al artículo 211-B del Código del Trabajo.

2. DECLARACIONES
Declaró como testigo Javiera Muñoz Valdés, compañera de la unidad de cobranza, quien señaló haber presenciado gritos en reuniones de equipo. También declaró don Felipe Contreras Saavedra, quien no recordó hechos específicos.
La denunciante acompañó una licencia médica por trastorno ansioso emitida por la Dra. Andrea Lagos Venegas, y señaló estar en tratamiento psiquiátrico.

3. CONCLUSIONES
Se estima acreditada la existencia de conductas de hostigamiento reiteradas. Se recomienda a Constructora Puerto Claro Limitada la aplicación de una medida disciplinaria al denunciado y la derivación de la señora Riquelme al organismo administrador de la Ley N° 16.744.

Investigadora: Daniela Soto Figueroa
""",
        "debe": [
            ("Valentina Paz Riquelme Ortiz", "Persona"),
            (R4, "RUT"),
            ("Matías Ignacio Carrasco Bravo", "Persona"),
            (R5, "RUT"),
            ("Javiera Muñoz Valdés", "Persona"),
            ("Felipe Contreras Saavedra", "Persona"),
            ("Andrea Lagos Venegas", "Persona"),
            ("Constructora Puerto Claro Limitada", "Empresa"),
            ("Riquelme", "Persona"),
            ("Daniela Soto Figueroa", "Persona"),
        ],
        "sensibles": ["trastorno ansioso", "tratamiento psiquiátrico", "licencia médica"],
        "queda": ["Ley N° 21.643", "Ley Karin", "Inspección del Trabajo", "Código del Trabajo", "Ley N° 16.744"],
    },
    {
        "id": "03-demanda-laboral",
        "titulo": "Demanda por despido injustificado",
        "texto": f"""EN LO PRINCIPAL: Demanda por despido injustificado y cobro de prestaciones; PRIMER OTROSÍ: Acompaña documentos; SEGUNDO OTROSÍ: Patrocinio y poder.

S.J.L. DEL TRABAJO DE SANTIAGO

JORGE ESTEBAN NÚÑEZ PIZARRO, chileno, casado, conductor, cédula nacional de identidad N° {R6}, domiciliado en calle Los Copihues 245, departamento 32, comuna de Puente Alto, a S.S. respetuosamente digo:

Que vengo en interponer demanda en contra de mi ex empleador Transportes Cordillera Sur Ltda., RUT {R3}, representada por don Sebastián Herrera Gallardo, ambos domiciliados en Avenida Vicuña Mackenna 7250, comuna de La Florida.

Presté servicios como conductor del camión patente HJKL·42 desde el 1 de agosto de 2019. Fui despedido verbalmente el 30 de abril de 2025. Existe además causa conexa RIT O-4512-2025 seguida ante este mismo tribunal, y la causa Rol C-18233-2024 del 12° Juzgado Civil de Santiago.

POR TANTO, en mérito de lo expuesto y lo dispuesto en los artículos 162, 163 y 168 del Código del Trabajo, RUEGO A S.S. tener por interpuesta la demanda.

PRIMER OTROSÍ: Ruego a S.S. tener por acompañada copia del finiquito.
SEGUNDO OTROSÍ: Designo abogado patrocinante y confiero poder a doña Francisca Morales Espinoza, con domicilio en Avenida Providencia 1208, oficina 801, Providencia.
""",
        "debe": [
            ("JORGE ESTEBAN NÚÑEZ PIZARRO", "Persona"),
            (R6, "RUT"),
            ("calle Los Copihues 245, departamento 32", "Dirección"),
            ("Puente Alto", "Comuna"),
            ("Transportes Cordillera Sur Ltda.", "Empresa"),
            ("Sebastián Herrera Gallardo", "Persona"),
            ("Avenida Vicuña Mackenna 7250", "Dirección"),
            ("HJKL·42", "Patente"),
            ("O-4512-2025", "Causa"),
            ("C-18233-2024", "Causa"),
            ("Francisca Morales Espinoza", "Persona"),
        ],
        "queda": ["Código del Trabajo", "Juzgado Civil", "PRIMER OTROSÍ", "SEGUNDO OTROSÍ"],
    },
    {
        "id": "04-compraventa-y-correo",
        "titulo": "Compraventa de inmueble y correo del cliente",
        "texto": f"""ESCRITURA DE COMPRAVENTA (extracto)

Comparecen: doña María José Valenzuela Cáceres, chilena, divorciada, ingeniera comercial, cédula de identidad N° {R1}, como vendedora; y don Tomás Alfonso Reyes Medina, chileno, casado, médico cirujano, cédula de identidad N° {R2}, como comprador.

El inmueble se encuentra inscrito a fojas 45.871 número 66.203 del Registro de Propiedad del Conservador de Bienes Raíces de Santiago del año 2018, y tiene el rol de avalúo 1523-87 de la comuna de Ñuñoa. El precio es de 7.850 UF, que se paga mediante vale vista.

-----
De: tomas.reyes.m@correo-ficticio.cl
Asunto: dudas sobre la escritura

Estimada Francisca: te escribo por lo del departamento. Mi señora, Antonia Bustos, también quiere firmar. Mi celular es 9 6123 4455. Saludos, Tomás.
""",
        "debe": [
            ("María José Valenzuela Cáceres", "Persona"),
            (R1, "RUT"),
            ("Tomás Alfonso Reyes Medina", "Persona"),
            (R2, "RUT"),
            ("fojas 45.871 número 66.203", "Propiedad"),
            ("1523-87", "Propiedad"),
            ("Ñuñoa", "Comuna"),
            ("tomas.reyes.m@correo-ficticio.cl", "Correo"),
            ("Antonia Bustos", "Persona"),
            ("9 6123 4455", "Teléfono"),
        ],
        "queda": ["Conservador de Bienes Raíces", "Registro de Propiedad", "vale vista"],
    },
]

# ───────── Documentos de reserva: escritos DESPUÉS de ajustar el programa, para medir sin trampa ─────────
R7, R8, R9 = rut(16543217), rut(10288456), rut(77812990)

RESERVA = [
    {
        "id": "05-finiquito",
        "titulo": "Finiquito (reserva)",
        "texto": f"""FINIQUITO DE CONTRATO DE TRABAJO

En Viña del Mar, a 31 de julio de 2025, comparecen por una parte Servicios Integrales Costa Azul Limitada, rut {R9}, representada por su gerente general Patricio Olivares Lagos, y por la otra Nicolás Andrés Gallardo Zúñiga, rut {R7.replace('.', '')}, con domicilio en Av. Libertad 1450 depto 504, Viña del Mar, fono (32) 2345 6789.

El trabajador prestó servicios entre el 3 de enero de 2022 y el 30 de junio de 2025, fecha en que se puso término al contrato por la causal del artículo 161 inciso primero del Código del Trabajo (necesidades de la empresa).

Se pagan las siguientes sumas mediante transferencia a la cuenta vista N° 3456789012 del trabajador: indemnización por años de servicio y feriado proporcional.

El trabajador declara que durante la relación laboral estuvo afiliado al Sindicato de Trabajadores N° 2 de la empresa y que no tiene reclamos pendientes ante la Inspección Provincial del Trabajo.
""",
        "debe": [
            ("Servicios Integrales Costa Azul Limitada", "Empresa"),
            (R9, "RUT"),
            ("Patricio Olivares Lagos", "Persona"),
            ("Nicolás Andrés Gallardo Zúñiga", "Persona"),
            (R7.replace('.', ''), "RUT"),
            ("Av. Libertad 1450 depto 504", "Dirección"),
            ("(32) 2345 6789", "Teléfono"),
            ("3456789012", "Cuenta"),
        ],
        "sensibles": ["afiliado al Sindicato"],
        "queda": ["Código del Trabajo", "Inspección Provincial del Trabajo", "necesidades de la empresa"],
    },
    {
        "id": "06-acta-mediacion",
        "titulo": "Acta de mediación familiar (reserva)",
        "texto": f"""ACTA DE MEDIACIÓN

Ante la mediadora Carolina Henríquez Pino comparecen Gonzalo Ríos Escobar, cédula {R8}, y Ximena Paredes Uribe, ambos con domicilio en la comuna de Quilpué, para acordar el régimen de relación directa y regular respecto de su hija menor de edad, Isidora Ríos Paredes.

Las partes dejan constancia de que existe una causa de alimentos, RIT C-2231-2024 del Juzgado de Familia de Quilpué, y de que la madre padece una enfermedad crónica que requiere controles mensuales en el Hospital de Quilpué.

El padre se compromete a retirar a la niña los días sábado a las 10:00 horas desde el domicilio materno, ubicado en Los Aromos 778, villa Las Palmas. Correo de contacto del padre: grios.escobar@correo-ficticio.cl.
""",
        "debe": [
            ("Carolina Henríquez Pino", "Persona"),
            ("Gonzalo Ríos Escobar", "Persona"),
            (R8, "RUT"),
            ("Ximena Paredes Uribe", "Persona"),
            ("Isidora Ríos Paredes", "Persona"),
            ("C-2231-2024", "Causa"),
            ("Los Aromos 778", "Dirección"),
            ("grios.escobar@correo-ficticio.cl", "Correo"),
        ],
        "sensibles": ["enfermedad crónica"],
        "queda": ["Juzgado de Familia", "relación directa y regular"],
    },
]
