"""Construccion de glosas a partir de eventos ya extraidos."""

# ==========================
# TRADUCCIÓN A GLOSA
# ==========================

MODALES_GLOSA = {
    "TENER",
    "PODER",
    "QUERER",
    "DEBER",
    "SABER",
    "NECESITAR",
    "INTENTAR",
    "PREFERIR",
    "SOLER"
}


def construir_verbo_evento(evento):
    """
    Construye la parte verbal del evento.
    Maneja:
    - verbo normal: COMER
    - verbo negado: COMER<NEG>
    - verbo encadenado: COMER QUERER
    - modal negado: COMER QUERER<NEG>
    """

    verbo = evento["verbo"]

    if evento["es_encadenado"]:
        modal = evento["modal"]

        if evento["negacion"]:
            modal += "<NEG>"

        return f"{verbo} {modal}"

    else:
        if evento["negacion"]:
            verbo += "<NEG>"

        return verbo


def construir_partes_sin_verbo(evento):
    """
    Construye la parte no verbal:
    tiempo + lugar + sujeto + objeto
    """

    partes = []

    if evento["tiempo"]:
        partes.append(evento["tiempo"])

    if evento["lugar"]:
        partes.append(evento["lugar"])

    if evento["sujeto"]:
        partes.append(evento["sujeto"])

    if evento["objeto"]:
        partes.append(evento["objeto"])

    return partes


def construir_linea_tecnica(evento):
    """
    Construye una línea técnica normal:
    TIEMPO LUGAR SUJETO OBJETO VERBO
    """

    partes = construir_partes_sin_verbo(evento)
    partes.append(construir_verbo_evento(evento))

    return " ".join(partes)


def obtener_causa_visible(evento_causa, tiempos_a_evitar=None):
    """
    Convierte una causa técnica en causa visible.

    Ejemplo:
    EXAMEN EXISTIR -> EXAMEN

    También evita duplicar tiempos:
    MAÑANA EXAMEN EXISTIR -> EXAMEN
    si MAÑANA ya estaba en el evento principal.
    """

    if tiempos_a_evitar is None:
        tiempos_a_evitar = set()

    partes = construir_partes_sin_verbo(evento_causa)

    # Evitar duplicar tiempos como MAÑANA, HOY, AYER
    partes = [p for p in partes if p not in tiempos_a_evitar]

    verbo = construir_verbo_evento(evento_causa)

    # Si la causa solo establece existencia:
    # EXAMEN EXISTIR -> EXAMEN
    if verbo == "EXISTIR":
        return " ".join(partes)

    # Si no es existencia, conservar la acción:
    # MAMÁ PEDIR -> MAMÁ PEDIR
    partes.append(verbo)
    return " ".join(partes)


def construir_linea_natural(evento):
    """
    Construye una línea natural simple cuando no hay conectores especiales.
    """

    return construir_linea_tecnica(evento)


