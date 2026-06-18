"""Flujo principal de traduccion: texto -> spaCy -> eventos -> glosa."""

from .analisis import detectar_pregunta, extraer_eventos
from .constructor_glosa import (
    construir_linea_natural,
    construir_linea_tecnica,
    construir_partes_sin_verbo,
    construir_verbo_evento,
    obtener_causa_visible,
)
from .modelo_spacy import nlp

def traducir_a_glosa_lsm_tecnica(texto):
    """
    Glosa completa para depuración.
    Conserva conectores como líneas independientes.
    """

    doc = nlp(texto)

    tipo_pregunta = detectar_pregunta(doc)
    eventos = extraer_eventos(doc)

    lineas = []

    for i, evento in enumerate(eventos):

        if evento["conector"]:
            lineas.append(f"[{evento['conector']}]")

        linea = construir_linea_tecnica(evento)

        # Pregunta solo al final
        if tipo_pregunta and i == len(eventos) - 1:
            if tipo_pregunta == "SI_NO":
                linea += "<?>"
            else:
                linea += f" {tipo_pregunta}<?>"

        lineas.append(linea)

    return "\n".join(lineas)


def traducir_a_glosa_lsm_natural(texto):
    """
    Glosa visible para usuario.

    Casos:
    1. Evento principal + [PORQUE] + causa:
       MAÑANA ESCUELA ESTUDIANTE(PL) ESTUDIAR TENER
       [PORQUE]
       EXAMEN EXISTIR

       ->
       MAÑANA ESCUELA ESTUDIANTE(PL) EXAMEN / ESTUDIAR TENER

    2. Evento + [MIENTRAS] + evento:
       MI MAMÁ COCINAR
       [MIENTRAS]
       MI PAPÁ CASA LIMPIAR

       ->
       MI MAMÁ COCINAR / MI PAPÁ CASA LIMPIAR
    """

    doc = nlp(texto)

    tipo_pregunta = detectar_pregunta(doc)
    eventos = extraer_eventos(doc)

    # ==========================
    # CASO: PORQUE / CAUSA
    # ==========================
    if len(eventos) == 2 and eventos[1]["conector"] == "PORQUE":

        evento_principal = eventos[0]
        evento_causa = eventos[1]

        partes_principal = construir_partes_sin_verbo(evento_principal)
        verbo_principal = construir_verbo_evento(evento_principal)

        # Evitar que el tiempo se repita en la causa
        tiempos_a_evitar = set()

        if evento_principal["tiempo"]:
            tiempos_a_evitar.add(evento_principal["tiempo"])

        causa_visible = obtener_causa_visible(
            evento_causa,
            tiempos_a_evitar=tiempos_a_evitar
        )

        partes_visibles = partes_principal.copy()

        if causa_visible:
            partes_visibles.append(causa_visible)

        izquierda = " ".join(partes_visibles)
        derecha = verbo_principal

        glosa = f"{izquierda} / {derecha}"

        if tipo_pregunta:
            if tipo_pregunta == "SI_NO":
                glosa += "<?>"
            else:
                glosa += f" {tipo_pregunta}<?>"

        return glosa

    # ==========================
    # CASO: MIENTRAS / SIMULTANEIDAD
    # ==========================
    if len(eventos) == 2 and eventos[1]["conector"] == "MIENTRAS":

        primera = construir_linea_natural(eventos[0])
        segunda = construir_linea_natural(eventos[1])

        glosa = f"{primera} / {segunda}"

        if tipo_pregunta:
            if tipo_pregunta == "SI_NO":
                glosa += "<?>"
            else:
                glosa += f" {tipo_pregunta}<?>"

        return glosa

    # ==========================
    # CASO NORMAL
    # ==========================

    lineas = []

    for i, evento in enumerate(eventos):

        if evento["conector"]:
            lineas.append(f"[{evento['conector']}]")

        linea = construir_linea_natural(evento)

        if tipo_pregunta and i == len(eventos) - 1:
            if tipo_pregunta == "SI_NO":
                linea += "<?>"
            else:
                linea += f" {tipo_pregunta}<?>"

        lineas.append(linea)

    return " ".join(lineas)


def traducir_a_glosa_lsm(texto):
    """
    Mantengo esta función para que la interfaz no se rompa.
    Por defecto devuelve la glosa técnica.
    """

    return traducir_a_glosa_lsm_tecnica(texto)


def generar_glosa_visible(texto_o_glosa):
    """
    IMPORTANTE:
    Esta función ahora espera el TEXTO ORIGINAL, no la glosa técnica.

    Antes intentábamos convertir glosa técnica -> glosa natural.
    Eso causaba errores porque perdíamos roles semánticos.
    Ahora hacemos texto -> eventos -> glosa natural.
    """

    return traducir_a_glosa_lsm_natural(texto_o_glosa)


