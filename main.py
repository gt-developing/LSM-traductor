"""Traductor de espanol a glosa para LSM.

El modulo combina tres capas:
- reglas linguisticas para convertir texto en eventos estructurados;
- funciones de salida que ordenan esos eventos como glosa tecnica o visible;
- una interfaz de escritorio para probar la traduccion y animar sus tokens.

La estructura interna mas importante es el diccionario ``evento``. Cada evento
representa una accion con campos como tiempo, lugar, sujeto, objeto, verbo,
modal, negacion y conector. Las funciones de construccion de glosa consumen
esa estructura para mantener separada la extraccion linguistica del formato
mostrado al usuario.
"""

import spacy

nlp = spacy.load("es_core_news_lg")

# ==========================
# DICCIONARIOS DE GLOSAS
# ==========================

GLOSAS_VERBOS = {
    "haber": "EXISTIR",
    "conversar": "HABLAR",
    "platicar": "HABLAR",
    "charlar": "HABLAR"
}

GLOSAS_SUSTANTIVOS = {
    "automóvil": "CARRO",
    "coche": "CARRO"
}

VERBOS_AMBIGUOS = {
    "cocina": "COCINAR",
    "limpia": "LIMPIAR",
    "estudio": "ESTUDIAR"
}

GLOSAS_CANTIDADES = {
    "muchos": "MUCHO",
    "muchas": "MUCHO",
    "varios": "VARIO",
    "varias": "VARIO",
    "pocos": "POCO",
    "pocas": "POCO",
    "algunos": "ALGUNO",
    "algunas": "ALGUNO"
}

INTERROGATIVOS = {
    "por qué": "PORQUE",
    "por que": "PORQUE",
    "qué": "QUE",
    "que": "QUE",
    "quién": "QUIEN",
    "quien": "QUIEN",
    "dónde": "DONDE",
    "donde": "DONDE",
    "cuándo": "CUANDO",
    "cuando": "CUANDO",
    "cómo": "COMO",
    "como": "COMO"
}

VERBOS_MODALES = {
    "querer",
    "poder",
    "deber",
    "necesitar",
    "saber",
    "intentar",
    "preferir",
    "soler",
    "tener"  # para casos tipo: tener que estudiar
}


# ==========================
# FUNCIONES AUXILIARES
# ==========================

def es_interrogativo(token):
    """Indica si el token corresponde a una palabra interrogativa conocida."""

    return token.text.lower() in INTERROGATIVOS


def obtener_glosa(token):
    """Devuelve la glosa base de un token segun diccionarios y lema.

    La prioridad es: interrogativos, verbos normalizados, sustantivos
    normalizados y, como respaldo, el lema del token en mayusculas.
    """

    texto = token.text.lower()
    lema = token.lemma_.lower()

    # Interrogativos
    if texto in INTERROGATIVOS:
        return INTERROGATIVOS[texto]

    # Verbos
    if token.pos_ in ["VERB", "AUX"]:
        if lema in GLOSAS_VERBOS:
            return GLOSAS_VERBOS[lema]

    # Sustantivos / otras palabras
    else:
        if lema in GLOSAS_SUSTANTIVOS:
            return GLOSAS_SUSTANTIVOS[lema]

    return lema.upper()


def es_plural(token):
    """Comprueba si spaCy marco el token como plural."""

    return "Number=Plur" in str(token.morph)


def obtener_cantidad(token):
    """Extrae una cantidad asociada al sustantivo si existe.

    Acepta modificadores numerales de spaCy y cuantificadores frecuentes como
    "muchos", "varias" o "pocos".
    """

    for hijo in token.children:

        # Números explícitos: dos, tres, cuatro...
        if hijo.dep_ == "nummod":
            return obtener_glosa(hijo)

        # Cuantificadores: muchos, pocos, varios...
        texto = hijo.text.lower()

        if texto in GLOSAS_CANTIDADES:
            return GLOSAS_CANTIDADES[texto]

    return None


def obtener_posesivo(token):
    """Busca determinantes posesivos dentro del grupo nominal del token."""

    for hijo in token.children:
        texto = hijo.text.lower()

        if texto in ["mi", "mis"]:
            return "MI"

        if texto in ["tu", "tus"]:
            return "TU"

        if texto in ["su", "sus"]:
            return "SU"

        if texto in ["nuestro", "nuestra", "nuestros", "nuestras"]:
            return "NUESTRO"

        if texto in ["vuestro", "vuestra", "vuestros", "vuestras"]:
            return "VUESTRO"

    return ""


def obtener_grupo_nominal(token):
    """Construye la glosa de un grupo nominal.

    El orden usado para LSM es posesivo, sustantivo, adjetivos y cantidad. Si
    no hay cantidad explicita, conserva la pluralidad mediante ``(PL)``.
    """

    cantidad = obtener_cantidad(token)
    posesivo = obtener_posesivo(token)
    palabra = obtener_glosa(token)

    palabras = []

    # Posesivo primero: MI MAMÁ, TU HERMANO
    if posesivo:
        palabras.append(posesivo)

    # Sustantivo
    palabras.append(palabra)

    # Adjetivos después del sustantivo
    for hijo in token.children:
        if hijo.pos_ == "ADJ":

            # Evitar que verbos ambiguos mal etiquetados entren como adjetivos
            # Ejemplo: mamá cocina, papá limpia
            if hijo.text.lower() in VERBOS_AMBIGUOS:
                continue

            palabras.append(obtener_glosa(hijo))

    # Cantidad después del sustantivo + adjetivos:
    # LIBRO NUEVO TRES
    if cantidad:
        palabras.append(cantidad)
    else:
        if es_plural(token):
            indice_sustantivo = 1 if posesivo else 0
            palabras[indice_sustantivo] += "(PL)"

    return " ".join(palabras)

def buscar_sujeto_cercano(token):
    """
    Busca un sujeto nominal cerca de un verbo.
    Sirve cuando spaCy no deja el sujeto como hijo directo.
    Ejemplo:
    Los estudiantes tienen que estudiar...
    """

    doc = token.doc

    # 1. Buscar hijos directos con nsubj
    for hijo in token.children:
        if hijo.dep_ == "nsubj" and not es_interrogativo(hijo):
            return obtener_grupo_nominal(hijo)

    # 2. Buscar hacia la izquierda sin cruzar conectores ni puntuación fuerte
    for i in range(token.i - 1, -1, -1):
        candidato = doc[i]
        texto = candidato.text.lower()

        if candidato.pos_ == "PUNCT" or texto in ["mientras", "cuando", "porque", "aunque", "si"]:
            break

        if candidato.pos_ in ["NOUN", "PROPN", "PRON"]:
            return obtener_grupo_nominal(candidato)

    return ""

def inferir_sujeto_desde_verbo(token):
    """Infere pronombres sujeto a partir de persona y numero verbal."""

    person = token.morph.get("Person")
    number = token.morph.get("Number")

    if not person:
        return ""

    person = person[0] if person else ""
    number = number[0] if number else ""

    if person == "1" and number == "Sing":
        return "YO"

    if person == "2" and number == "Sing":
        return "TU"

    if person == "1" and number == "Plur":
        return "NOSOTRO(PL)"

    if person == "2" and number == "Plur":
        return "USTED(PL)"

    return ""


def es_posible_verbo(token):
    """Determina si un token puede funcionar como verbo de un evento.

    Ademas del etiquetado POS normal, incluye una heuristica para raices que
    spaCy puede confundir con nombres propios en frases cortas.
    """

    if token.pos_ in ["VERB", "AUX"]:
        return True

    # Heurística para casos como "Estudio" mal detectado como PROPN
    if token.dep_ == "ROOT":
        terminaciones = (
            "o", "as", "a",
            "amos", "áis", "an",
            "é", "aste", "ó",
            "aron", "í", "iste",
            "ió", "ieron"
        )

        if token.text.lower().endswith(terminaciones):
            return True

    return False


def detectar_pregunta(doc):
    """Devuelve el tipo de pregunta detectado o ``None`` si no hay pregunta.

    Solo activa la deteccion cuando el texto contiene signos de interrogacion,
    para no tratar palabras como "cuando" o "como" como preguntas indirectas.
    """

    # Solo detectar pregunta si realmente hay signos de pregunta
    if "¿" not in doc.text and "?" not in doc.text:
        return None

    texto = doc.text.lower()

    # Primero expresiones compuestas.
    # Si no, "por qué" se detecta erróneamente como "qué".
    if "por qué" in texto or "por que" in texto:
        return "PORQUE"

    mapa_preguntas = {
        "qué": "QUE",
        "que": "QUE",
        "quién": "QUIEN",
        "quien": "QUIEN",
        "dónde": "DONDE",
        "donde": "DONDE",
        "cuándo": "CUANDO",
        "cuando": "CUANDO",
        "cómo": "COMO",
        "como": "COMO"
    }

    for palabra, glosa in mapa_preguntas.items():
        if palabra in texto:
            return glosa

    # Pregunta cerrada: sí / no
    return "SI_NO"


def obtener_tiempo_global(doc):
    """
    Busca adverbios temporales en toda la oración.
    Sirve para casos donde spaCy no conecta 'ayer', 'hoy',
    'mañana', etc. como hijo directo del verbo.
    """

    tiempos = {
        "ayer": "AYER",
        "hoy": "HOY",
        "mañana": "MAÑANA",
        "ahora": "AHORA",
        "después": "DESPUÉS",
        "despues": "DESPUÉS",
        "antes": "ANTES",
        "luego": "LUEGO",
        "temprano": "TEMPRANO",
        "tarde": "TARDE"
    }

    for token in doc:
        texto = token.text.lower()

        if texto in tiempos:
            return tiempos[texto]

    return ""


def tiene_negacion_cercana(token):
    """
    Detecta negación cerca de un verbo/modal.
    Ejemplo:
    no puede comprar
    no quiere estudiar
    """

    # Hijos directos
    for hijo in token.children:
        if hijo.text.lower() == "no":
            return True

    # Ventana cercana hacia atrás
    doc = token.doc

    for i in range(max(0, token.i - 3), token.i):
        if doc[i].text.lower() == "no":
            return True

    return False


def buscar_verbo_accion_cercano(token):
    """
    Busca el infinitivo que depende o aparece cerca de un modal.
    Sirve para casos como:
    puede comprar
    quiere estudiar
    sabe leer
    tiene que estudiar
    """

    # Primero buscar por dependencia normal
    for hijo in token.children:
        if hijo.dep_ in ["xcomp", "ccomp"] and hijo.pos_ in ["VERB", "AUX"]:
            return hijo

    # Si spaCy no lo conectó como hijo, buscar a la derecha
    doc = token.doc

    for i in range(token.i + 1, min(len(doc), token.i + 7)):
        candidato = doc[i]

        if candidato.pos_ == "PUNCT":
            break

        # Cortar si aparece otro verbo conjugado antes de encontrar infinitivo
        if (
            candidato.pos_ in ["VERB", "AUX"]
            and "VerbForm=Fin" in str(candidato.morph)
            and candidato.i != token.i
        ):
            break

        # Infinitivos: comprar, estudiar, leer...
        if candidato.pos_ == "VERB" and "VerbForm=Inf" in str(candidato.morph):
            return candidato

    return None


# ==========================
# VERBOS ENCADENADOS
# ==========================

def extraer_evento_verbo_encadenado(token):
    """Extrae un evento para construcciones con modal mas infinitivo.

    Ejemplos: "quiere comer", "puede comprar", "tiene que estudiar". La accion
    principal queda en ``verbo`` y el verbo modal queda en ``modal``.
    """

    evento = {
        "tiempo": "",
        "lugar": "",
        "objeto": "",
        "sujeto": "",
        "verbo": "",
        "modal": "",
        "negacion": False,
        "conector": None,
        "es_encadenado": True
    }

    verbo_modal = token
    evento["modal"] = obtener_glosa(verbo_modal)

    # La negación pertenece al modal:
    # no puede comprar -> COMPRAR PODER<NEG>
    if tiene_negacion_cercana(verbo_modal):
        evento["negacion"] = True

    # Buscar sujeto / lugar / tiempo / conector en el modal
    for hijo in verbo_modal.children:

        if hijo.dep_ == "nsubj":
            evento["sujeto"] = obtener_grupo_nominal(hijo)

        elif hijo.dep_ == "obl" and not es_interrogativo(hijo):
            evento["lugar"] = obtener_grupo_nominal(hijo)

        elif hijo.dep_ == "advmod":
            texto = hijo.text.lower()

            if texto != "no" and not es_interrogativo(hijo):
                evento["tiempo"] = obtener_glosa(hijo)

        elif hijo.dep_ == "mark":
            evento["conector"] = hijo.text.upper()

    # Buscar verbo dependiente: comprar, leer, estudiar...
    verbo_accion = buscar_verbo_accion_cercano(verbo_modal)

    if verbo_accion is None:
        return None

    evento["verbo"] = obtener_glosa(verbo_accion)

    # Extraer información del verbo de acción
    for hijo in verbo_accion.children:

        if hijo.dep_ == "obj" and not es_interrogativo(hijo):
            evento["objeto"] = obtener_grupo_nominal(hijo)

        elif hijo.dep_ == "obl" and not es_interrogativo(hijo):
            evento["lugar"] = obtener_grupo_nominal(hijo)

        elif hijo.dep_ == "advmod":
            texto = hijo.text.lower()

            # No pegamos la negación al verbo interno.
            # En "no puede comprar", la negación va sobre PODER.
            if texto == "no":
                continue

            elif not es_interrogativo(hijo):
                evento["tiempo"] = obtener_glosa(hijo)

    # Si no hay sujeto explícito, inferir desde el verbo modal
    if not evento["sujeto"]:
        evento["sujeto"] = buscar_sujeto_cercano(verbo_modal)

    if not evento["sujeto"]:
        evento["sujeto"] = inferir_sujeto_desde_verbo(verbo_modal)

    return evento


# ==========================
# VERBOS AMBIGUOS
# ==========================

def es_verbo_ambiguo_en_contexto(tokens, i):
    """Decide si una palabra ambigua debe tratarse como verbo.

    Palabras como "cocina", "limpia" o "estudio" pueden ser sustantivo,
    adjetivo o verbo; esta funcion usa contexto cercano para resolverlo.
    """

    token = tokens[i]
    texto = token.text.lower()

    if texto not in VERBOS_AMBIGUOS:
        return False

    # Si antes hay un verbo copulativo como "es", "está", "parece",
    # probablemente es adjetivo: "Ella es limpia"
    for j in range(max(0, i - 3), i):
        anterior = tokens[j].text.lower()

        if anterior in ["es", "son", "soy", "eres", "somos", "está", "estan", "están", "parece", "parecen"]:
            return False

    # Si después hay un sustantivo, probablemente hay objeto:
    # "limpia la casa"
    for j in range(i + 1, min(len(tokens), i + 4)):
        siguiente = tokens[j]

        if siguiente.pos_ in ["NOUN", "PROPN"]:
            return True

    # Si antes hay un sujeto nominal cercano:
    # "mi mamá cocina"
    for j in range(max(0, i - 3), i):
        anterior = tokens[j]

        if anterior.pos_ in ["NOUN", "PROPN", "PRON"]:
            return True

    return False


def extraer_eventos_ambiguos(doc):
    """Construye eventos para casos que el analisis POS no detecto como verbos."""

    eventos = []
    tokens = list(doc)

    for i, token in enumerate(tokens):

        if not es_verbo_ambiguo_en_contexto(tokens, i):
            continue

        texto = token.text.lower()

        evento = {
            "tiempo": "",
            "lugar": "",
            "objeto": "",
            "sujeto": "",
            "verbo": VERBOS_AMBIGUOS[texto],
            "modal": "",
            "negacion": False,
            "conector": None,
            "es_encadenado": False
        }

        # Buscar sujeto hacia atrás, sin cruzar conectores
        for j in range(i - 1, -1, -1):
            candidato = tokens[j]
            texto_candidato = candidato.text.lower()

            if texto_candidato in ["mientras", "cuando", "porque", "aunque", "si"]:
                break

            if candidato.pos_ in ["NOUN", "PROPN", "PRON"]:
                evento["sujeto"] = obtener_grupo_nominal(candidato)
                break

        # Buscar conector hacia atrás
        for j in range(i - 1, -1, -1):
            candidato = tokens[j]
            texto_candidato = candidato.text.lower()

            if texto_candidato in ["mientras", "cuando", "porque", "aunque", "si"]:
                evento["conector"] = candidato.text.upper()
                break

        # Buscar objeto hacia adelante, sin cruzar conectores ni otro verbo ambiguo
        for j in range(i + 1, len(tokens)):
            candidato = tokens[j]
            texto_candidato = candidato.text.lower()

            if texto_candidato in ["mientras", "cuando", "porque", "aunque", "si"]:
                break

            if texto_candidato in VERBOS_AMBIGUOS:
                break

            if texto_candidato in ["mi", "tu", "su", "mis", "tus", "sus"]:
                continue

            if candidato.pos_ in ["NOUN", "PROPN"] and candidato.dep_ in ["obj", "appos", "obl"]:
                evento["objeto"] = obtener_grupo_nominal(candidato)
                break

        eventos.append(evento)

    return eventos


# ==========================
# EXTRACCIÓN DE EVENTOS
# ==========================

def extraer_eventos(doc):
    """Extrae los eventos semanticos principales de una oracion analizada.

    Recorre los tokens del documento, detecta verbos normales y encadenados,
    recupera sujeto, objeto, lugar, tiempo, negacion y conectores, y usa un
    segundo pase heuristico cuando no se encontro ningun evento.
    """

    eventos = []
    tokens_usados = set()
    tiempo_global = obtener_tiempo_global(doc)

    for token in doc:

        if token.i in tokens_usados:
            continue

        if not es_posible_verbo(token):
            continue

        lema = token.lemma_.lower()

        # Detectar verbos encadenados:
        # puede comprar, quiere leer, sabe estudiar, tiene que estudiar...
        tiene_verbo_dependiente = buscar_verbo_accion_cercano(token) is not None

        if lema in VERBOS_MODALES and tiene_verbo_dependiente:
            evento_encadenado = extraer_evento_verbo_encadenado(token)

            if evento_encadenado and not evento_encadenado["tiempo"] and tiempo_global and not eventos:
                evento_encadenado["tiempo"] = tiempo_global

            if evento_encadenado:
                eventos.append(evento_encadenado)
                tokens_usados.add(token.i)

                verbo_accion = buscar_verbo_accion_cercano(token)

                if verbo_accion:
                    tokens_usados.add(verbo_accion.i)

                continue

        # Evento normal
        evento = {
            "tiempo": "",
            "lugar": "",
            "objeto": "",
            "sujeto": "",
            "verbo": obtener_glosa(token),
            "modal": "",
            "negacion": False,
            "conector": None,
            "es_encadenado": False
        }

        for hijo in token.children:

            if hijo.dep_ == "nsubj":
                if not es_interrogativo(hijo):
                    evento["sujeto"] = obtener_grupo_nominal(hijo)

            elif hijo.dep_ == "obl":
                if not es_interrogativo(hijo):
                    evento["lugar"] = obtener_grupo_nominal(hijo)

            elif hijo.dep_ == "obj":
                if not es_interrogativo(hijo):
                    evento["objeto"] = obtener_grupo_nominal(hijo)

            elif hijo.dep_ == "advmod":
                texto = hijo.text.lower()

                if texto == "no":
                    evento["negacion"] = True

                elif es_interrogativo(hijo):
                    pass

                else:
                    evento["tiempo"] = obtener_glosa(hijo)

            elif hijo.dep_ == "mark":
                evento["conector"] = hijo.text.upper()

        # Inferir sujeto desde conjugación verbal
        if not evento["sujeto"]:
            evento["sujeto"] = inferir_sujeto_desde_verbo(token)

        # Recuperar tiempo global si no apareció como hijo directo
        if not evento["tiempo"] and tiempo_global and not eventos:
            evento["tiempo"] = tiempo_global

        eventos.append(evento)

    if not eventos:
        eventos = extraer_eventos_ambiguos(doc)

    return eventos


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
    Usa eventos estructurados, no hacks de string.

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


# ==========================
# PRUEBAS OPCIONALES
# ==========================

if __name__ == "__main__":
    oraciones = [
        "Hoy mi hermana no puede comprar dos flores rojas en el mercado.",
        "¿Dónde compró Juan tres panes grandes ayer?",
        "Tu amigo quiere leer un libro nuevo en la biblioteca.",
        "Los gatos pequeños duermen en la silla mientras el perro come sopa.",
        "¿Por qué los estudiantes no quieren estudiar mañana en la escuela?",
        "Mañana los estudiantes tienen que estudiar en la escuela porque hay examen.",
        "Mi mamá cocina mientras mi papá limpia la casa."
    ]

    print("=== TRADUCTOR ESPAÑOL → GLOSA LSM ===\n")

    for oracion in oraciones:
        glosa_tecnica = traducir_a_glosa_lsm_tecnica(oracion)
        glosa_visible = traducir_a_glosa_lsm_natural(oracion)

        print(f"Original: {oracion}")
        print("Glosa técnica:")
        print(glosa_tecnica)
        print("Glosa visible:")
        print(glosa_visible)
        print()

import tkinter as tk
from tkinter import ttk, messagebox

# ==========================
# PRUEBAS DE CONFIABILIDAD
# 50 FRASES
# ==========================

casos_prueba = [
    # ==========================
    # 1. ORACIONES SIMPLES
    # ==========================
    {
        "categoria": "simple",
        "oracion": "El gato duerme.",
        "esperada_tecnica": "GATO DORMIR",
        "esperada_visible": "GATO DORMIR"
    },
    {
        "categoria": "simple",
        "oracion": "El perro corre.",
        "esperada_tecnica": "PERRO CORRER",
        "esperada_visible": "PERRO CORRER"
    },
    {
        "categoria": "simple",
        "oracion": "Juan come una manzana.",
        "esperada_tecnica": "JUAN MANZANA COMER",
        "esperada_visible": "JUAN MANZANA COMER"
    },
    {
        "categoria": "simple",
        "oracion": "María lee un libro.",
        "esperada_tecnica": "MARÍA LIBRO LEER",
        "esperada_visible": "MARÍA LIBRO LEER"
    },
    {
        "categoria": "simple",
        "oracion": "La niña canta.",
        "esperada_tecnica": "NIÑA CANTAR",
        "esperada_visible": "NIÑA CANTAR"
    },

    # ==========================
    # 2. LUGAR / CONTEXTO
    # ==========================
    {
        "categoria": "lugar",
        "oracion": "El gato negro duerme en la cama.",
        "esperada_tecnica": "CAMA GATO NEGRO DORMIR",
        "esperada_visible": "CAMA GATO NEGRO DORMIR"
    },
    {
        "categoria": "lugar",
        "oracion": "Los niños juegan en el parque.",
        "esperada_tecnica": "PARQUE NIÑO(PL) JUGAR",
        "esperada_visible": "PARQUE NIÑO(PL) JUGAR"
    },
    {
        "categoria": "lugar",
        "oracion": "La niña pequeña corre en la escuela.",
        "esperada_tecnica": "ESCUELA NIÑA PEQUEÑO CORRER",
        "esperada_visible": "ESCUELA NIÑA PEQUEÑO CORRER"
    },
    {
        "categoria": "lugar",
        "oracion": "Juan estudia en la biblioteca.",
        "esperada_tecnica": "BIBLIOTECA JUAN ESTUDIAR",
        "esperada_visible": "BIBLIOTECA JUAN ESTUDIAR"
    },
    {
        "categoria": "lugar",
        "oracion": "Mi papá trabaja en la oficina.",
        "esperada_tecnica": "OFICINA MI PAPÁ TRABAJAR",
        "esperada_visible": "OFICINA MI PAPÁ TRABAJAR"
    },

    # ==========================
    # 3. TIEMPO
    # ==========================
    {
        "categoria": "tiempo",
        "oracion": "Ayer Juan compró pan.",
        "esperada_tecnica": "AYER JUAN PAN COMPRAR",
        "esperada_visible": "AYER JUAN PAN COMPRAR"
    },
    {
        "categoria": "tiempo",
        "oracion": "Hoy María estudia.",
        "esperada_tecnica": "HOY MARÍA ESTUDIAR",
        "esperada_visible": "HOY MARÍA ESTUDIAR"
    },
    {
        "categoria": "tiempo",
        "oracion": "Mañana los niños juegan.",
        "esperada_tecnica": "MAÑANA NIÑO(PL) JUGAR",
        "esperada_visible": "MAÑANA NIÑO(PL) JUGAR"
    },
    {
        "categoria": "tiempo",
        "oracion": "Ahora el perro duerme.",
        "esperada_tecnica": "AHORA PERRO DORMIR",
        "esperada_visible": "AHORA PERRO DORMIR"
    },
    {
        "categoria": "tiempo",
        "oracion": "Después mi mamá cocina.",
        "esperada_tecnica": "DESPUÉS MI MAMÁ COCINAR",
        "esperada_visible": "DESPUÉS MI MAMÁ COCINAR"
    },

    # ==========================
    # 4. PLURAL Y CANTIDAD
    # ==========================
    {
        "categoria": "plural_cantidad",
        "oracion": "Los perros corren.",
        "esperada_tecnica": "PERRO(PL) CORRER",
        "esperada_visible": "PERRO(PL) CORRER"
    },
    {
        "categoria": "plural_cantidad",
        "oracion": "Dos perros corren.",
        "esperada_tecnica": "PERRO DOS CORRER",
        "esperada_visible": "PERRO DOS CORRER"
    },
    {
        "categoria": "plural_cantidad",
        "oracion": "Tres niños juegan en el parque.",
        "esperada_tecnica": "PARQUE NIÑO TRES JUGAR",
        "esperada_visible": "PARQUE NIÑO TRES JUGAR"
    },
    {
        "categoria": "plural_cantidad",
        "oracion": "Muchos estudiantes estudian.",
        "esperada_tecnica": "ESTUDIANTE MUCHO ESTUDIAR",
        "esperada_visible": "ESTUDIANTE MUCHO ESTUDIAR"
    },
    {
        "categoria": "plural_cantidad",
        "oracion": "Ayer compré tres libros nuevos en la biblioteca.",
        "esperada_tecnica": "AYER BIBLIOTECA YO LIBRO NUEVO TRES COMPRAR",
        "esperada_visible": "AYER BIBLIOTECA YO LIBRO NUEVO TRES COMPRAR"
    },

    # ==========================
    # 5. NEGACIÓN
    # ==========================
    {
        "categoria": "negacion",
        "oracion": "El perro no duerme.",
        "esperada_tecnica": "PERRO DORMIR<NEG>",
        "esperada_visible": "PERRO DORMIR<NEG>"
    },
    {
        "categoria": "negacion",
        "oracion": "Juan no come una manzana.",
        "esperada_tecnica": "JUAN MANZANA COMER<NEG>",
        "esperada_visible": "JUAN MANZANA COMER<NEG>"
    },
    {
        "categoria": "negacion",
        "oracion": "Los niños no juegan en el parque.",
        "esperada_tecnica": "PARQUE NIÑO(PL) JUGAR<NEG>",
        "esperada_visible": "PARQUE NIÑO(PL) JUGAR<NEG>"
    },
    {
        "categoria": "negacion",
        "oracion": "María no lee el libro.",
        "esperada_tecnica": "MARÍA LIBRO LEER<NEG>",
        "esperada_visible": "MARÍA LIBRO LEER<NEG>"
    },
    {
        "categoria": "negacion",
        "oracion": "Mi hermano no trabaja.",
        "esperada_tecnica": "MI HERMANO TRABAJAR<NEG>",
        "esperada_visible": "MI HERMANO TRABAJAR<NEG>"
    },

    # ==========================
    # 6. PREGUNTAS
    # ==========================
    {
        "categoria": "pregunta",
        "oracion": "¿Dónde está el perro?",
        "esperada_tecnica": "PERRO ESTAR DONDE<?>",
        "esperada_visible": "PERRO ESTAR DONDE<?>"
    },
    {
        "categoria": "pregunta",
        "oracion": "¿Qué come Juan?",
        "esperada_tecnica": "JUAN COMER QUE<?>",
        "esperada_visible": "JUAN COMER QUE<?>"
    },
    {
        "categoria": "pregunta",
        "oracion": "¿Cuándo juegan los niños?",
        "esperada_tecnica": "NIÑO(PL) JUGAR CUANDO<?>",
        "esperada_visible": "NIÑO(PL) JUGAR CUANDO<?>"
    },
    {
        "categoria": "pregunta",
        "oracion": "¿Los niños juegan?",
        "esperada_tecnica": "NIÑO(PL) JUGAR<?>",
        "esperada_visible": "NIÑO(PL) JUGAR<?>"
    },
    {
        "categoria": "pregunta",
        "oracion": "¿Juan no come?",
        "esperada_tecnica": "JUAN COMER<NEG><?>",
        "esperada_visible": "JUAN COMER<NEG><?>"
    },

    # ==========================
    # 7. POSESIVOS
    # ==========================
    {
        "categoria": "posesivo",
        "oracion": "Mi mamá cocina.",
        "esperada_tecnica": "MI MAMÁ COCINAR",
        "esperada_visible": "MI MAMÁ COCINAR"
    },
    {
        "categoria": "posesivo",
        "oracion": "Mi papá limpia la casa.",
        "esperada_tecnica": "MI PAPÁ CASA LIMPIAR",
        "esperada_visible": "MI PAPÁ CASA LIMPIAR"
    },
    {
        "categoria": "posesivo",
        "oracion": "Tu hermano lee un libro.",
        "esperada_tecnica": "TU HERMANO LIBRO LEER",
        "esperada_visible": "TU HERMANO LIBRO LEER"
    },
    {
        "categoria": "posesivo",
        "oracion": "Su hermana compra flores.",
        "esperada_tecnica": "SU HERMANA FLOR(PL) COMPRAR",
        "esperada_visible": "SU HERMANA FLOR(PL) COMPRAR"
    },
    {
        "categoria": "posesivo",
        "oracion": "Nuestro amigo estudia en la escuela.",
        "esperada_tecnica": "ESCUELA NUESTRO AMIGO ESTUDIAR",
        "esperada_visible": "ESCUELA NUESTRO AMIGO ESTUDIAR"
    },

    # ==========================
    # 8. VERBOS ENCADENADOS / MODALES
    # ==========================
    {
        "categoria": "modal",
        "oracion": "Juan quiere comer la manzana verde.",
        "esperada_tecnica": "JUAN MANZANA VERDE COMER QUERER",
        "esperada_visible": "JUAN MANZANA VERDE COMER QUERER"
    },
    {
        "categoria": "modal",
        "oracion": "Juan no quiere comer la manzana verde.",
        "esperada_tecnica": "JUAN MANZANA VERDE COMER QUERER<NEG>",
        "esperada_visible": "JUAN MANZANA VERDE COMER QUERER<NEG>"
    },
    {
        "categoria": "modal",
        "oracion": "Los niños no saben leer.",
        "esperada_tecnica": "NIÑO(PL) LEER SABER<NEG>",
        "esperada_visible": "NIÑO(PL) LEER SABER<NEG>"
    },
    {
        "categoria": "modal",
        "oracion": "Tu amigo quiere leer un libro nuevo en la biblioteca.",
        "esperada_tecnica": "BIBLIOTECA TU AMIGO LIBRO NUEVO LEER QUERER",
        "esperada_visible": "BIBLIOTECA TU AMIGO LIBRO NUEVO LEER QUERER"
    },
    {
        "categoria": "modal",
        "oracion": "Hoy mi hermana no puede comprar dos flores rojas en el mercado.",
        "esperada_tecnica": "HOY MERCADO MI HERMANA FLOR ROJO DOS COMPRAR PODER<NEG>",
        "esperada_visible": "HOY MERCADO MI HERMANA FLOR ROJO DOS COMPRAR PODER<NEG>"
    },

    # ==========================
    # 9. CONECTORES
    # ==========================
    {
        "categoria": "conector",
        "oracion": "Mi mamá cocina mientras mi papá limpia la casa.",
        "esperada_tecnica": "MI MAMÁ COCINAR\n[MIENTRAS]\nMI PAPÁ CASA LIMPIAR",
        "esperada_visible": "MI MAMÁ COCINAR / MI PAPÁ CASA LIMPIAR"
    },
    {
        "categoria": "conector",
        "oracion": "Los niños juegan en el parque mientras los adultos conversan.",
        "esperada_tecnica": "PARQUE NIÑO(PL) JUGAR\n[MIENTRAS]\nADULTO(PL) HABLAR",
        "esperada_visible": "PARQUE NIÑO(PL) JUGAR / ADULTO(PL) HABLAR"
    },
    {
        "categoria": "conector",
        "oracion": "Cuando llego a casa, el perro duerme.",
        "esperada_tecnica": "[CUANDO]\nCASA YO LLEGAR\nPERRO DORMIR",
        "esperada_visible": "CASA YO LLEGAR / PERRO DORMIR"
    },
    {
        "categoria": "conector",
        "oracion": "Estudio porque mañana hay examen.",
        "esperada_tecnica": "YO ESTUDIAR\n[PORQUE]\nMAÑANA EXAMEN EXISTIR",
        "esperada_visible": "MAÑANA EXAMEN / YO ESTUDIAR"
    },
    {
        "categoria": "conector",
        "oracion": "Mañana los estudiantes tienen que estudiar en la escuela porque hay examen.",
        "esperada_tecnica": "MAÑANA ESCUELA ESTUDIANTE(PL) ESTUDIAR TENER\n[PORQUE]\nEXAMEN EXISTIR",
        "esperada_visible": "MAÑANA ESCUELA ESTUDIANTE(PL) EXAMEN / ESTUDIAR TENER"
    },

    # ==========================
    # 10. MIXTAS / UN POCO MÁS DIFÍCILES
    # ==========================
    {
        "categoria": "mixta",
        "oracion": "¿Dónde compró Juan tres panes grandes ayer?",
        "esperada_tecnica": "AYER JUAN PAN GRANDE TRES COMPRAR DONDE<?>",
        "esperada_visible": "AYER JUAN PAN GRANDE TRES COMPRAR DONDE<?>"
    },
    {
        "categoria": "mixta",
        "oracion": "¿Tu hermano no quiere comer la sopa fría?",
        "esperada_tecnica": "TU HERMANO SOPA FRÍO COMER QUERER<NEG><?>",
        "esperada_visible": "TU HERMANO SOPA FRÍO COMER QUERER<NEG><?>"
    },
    {
        "categoria": "mixta",
        "oracion": "Los gatos pequeños duermen en la silla mientras el perro come sopa.",
        "esperada_tecnica": "SILLA GATO(PL) PEQUEÑO DORMIR\n[MIENTRAS]\nPERRO SOPA COMER",
        "esperada_visible": "SILLA GATO(PL) PEQUEÑO DORMIR / PERRO SOPA COMER"
    },
    {
        "categoria": "mixta",
        "oracion": "¿Por qué los estudiantes no quieren estudiar mañana en la escuela?",
        "esperada_tecnica": "MAÑANA ESCUELA ESTUDIANTE(PL) ESTUDIAR QUERER<NEG> PORQUE<?>",
        "esperada_visible": "MAÑANA ESCUELA ESTUDIANTE(PL) ESTUDIAR QUERER<NEG> PORQUE<?>"
    },
    {
        "categoria": "mixta",
        "oracion": "¿Por qué el perro grande persigue al gato en el jardín?",
        "esperada_tecnica": "JARDÍN PERRO GRANDE GATO PERSEGUIR PORQUE<?>",
        "esperada_visible": "JARDÍN PERRO GRANDE GATO PERSEGUIR PORQUE<?>"
    },
]


def normalizar_glosa(glosa):
    """
    Normaliza una glosa para comparaciones en pruebas.

    Limpia espacios repetidos y lineas vacias, pero conserva los saltos de
    linea significativos porque la glosa tecnica usa conectores en lineas
    separadas.
    """

    lineas = glosa.strip().splitlines()
    lineas_limpias = []

    for linea in lineas:
        linea_limpia = " ".join(linea.strip().split())
        if linea_limpia:
            lineas_limpias.append(linea_limpia)

    return "\n".join(lineas_limpias)


def evaluar_casos():
    """Ejecuta el banco de pruebas y reporta aciertos por tipo de glosa."""

    total = len(casos_prueba)

    aciertos_tecnica = 0
    aciertos_visible = 0

    resultados = []

    resumen_categorias = {}

    for i, caso in enumerate(casos_prueba, start=1):
        categoria = caso["categoria"]
        oracion = caso["oracion"]

        esperada_tecnica = normalizar_glosa(caso["esperada_tecnica"])
        esperada_visible = normalizar_glosa(caso["esperada_visible"])

        try:
            obtenida_tecnica = normalizar_glosa(
                traducir_a_glosa_lsm_tecnica(oracion)
            )

            obtenida_visible = normalizar_glosa(
                traducir_a_glosa_lsm_natural(oracion)
            )

        except Exception as e:
            obtenida_tecnica = f"ERROR: {e}"
            obtenida_visible = f"ERROR: {e}"

        ok_tecnica = obtenida_tecnica == esperada_tecnica
        ok_visible = obtenida_visible == esperada_visible

        if ok_tecnica:
            aciertos_tecnica += 1

        if ok_visible:
            aciertos_visible += 1

        if categoria not in resumen_categorias:
            resumen_categorias[categoria] = {
                "total": 0,
                "tecnica": 0,
                "visible": 0
            }

        resumen_categorias[categoria]["total"] += 1

        if ok_tecnica:
            resumen_categorias[categoria]["tecnica"] += 1

        if ok_visible:
            resumen_categorias[categoria]["visible"] += 1

        resultados.append({
            "numero": i,
            "categoria": categoria,
            "oracion": oracion,
            "esperada_tecnica": esperada_tecnica,
            "obtenida_tecnica": obtenida_tecnica,
            "ok_tecnica": ok_tecnica,
            "esperada_visible": esperada_visible,
            "obtenida_visible": obtenida_visible,
            "ok_visible": ok_visible
        })

    porcentaje_tecnica = (aciertos_tecnica / total) * 100
    porcentaje_visible = (aciertos_visible / total) * 100

    print("=== RESULTADO GENERAL ===")
    print(f"Total de frases: {total}")
    print(f"Aciertos glosa técnica: {aciertos_tecnica}/{total} = {porcentaje_tecnica:.2f}%")
    print(f"Aciertos glosa visible: {aciertos_visible}/{total} = {porcentaje_visible:.2f}%")
    print()

    print("=== RESULTADO POR CATEGORÍA ===")
    for categoria, datos in resumen_categorias.items():
        total_cat = datos["total"]
        pct_tec = (datos["tecnica"] / total_cat) * 100
        pct_vis = (datos["visible"] / total_cat) * 100

        print(
            f"{categoria}: "
            f"Técnica {datos['tecnica']}/{total_cat} = {pct_tec:.2f}% | "
            f"Visible {datos['visible']}/{total_cat} = {pct_vis:.2f}%"
        )

    print()
    print("=== ERRORES DETECTADOS ===")

    hubo_errores = False

    for r in resultados:
        if not r["ok_tecnica"] or not r["ok_visible"]:
            hubo_errores = True

            print(f"\nCaso {r['numero']} [{r['categoria']}]")
            print(f"Original: {r['oracion']}")

            if not r["ok_tecnica"]:
                print("Glosa técnica incorrecta:")
                print("Esperada:")
                print(r["esperada_tecnica"])
                print("Obtenida:")
                print(r["obtenida_tecnica"])

            if not r["ok_visible"]:
                print("Glosa visible incorrecta:")
                print("Esperada:")
                print(r["esperada_visible"])
                print("Obtenida:")
                print(r["obtenida_visible"])

    if not hubo_errores:
        print("No hubo errores. Todas las frases coincidieron.")


if __name__ == "__main__":
    evaluar_casos()
# =========================================================
# UTILIDADES PARA LA INTERFAZ
# =========================================================


def tokenizar_glosa_para_animacion(glosa):
    """Convierte una glosa multilinea en tokens secuenciales para la animacion."""

    tokens = []

    for linea in glosa.splitlines():
        linea = linea.strip()

        if not linea:
            continue

        for palabra in linea.split():
            tokens.append(palabra)

    return tokens


def obtener_datos_tecnicos(texto, glosa):
    """Genera el texto de depuracion mostrado en el panel tecnico."""

    lineas = []

    lineas.append("=== DATOS TÉCNICOS ===")
    lineas.append("")
    lineas.append("Texto original:")
    lineas.append(texto)
    lineas.append("")
    lineas.append("Glosa generada:")
    lineas.append(glosa)
    lineas.append("")
    lineas.append("Tokens para animación:")

    for i, token in enumerate(tokenizar_glosa_para_animacion(glosa), start=1):
        lineas.append(f"{i}. {token}")

    return "\n".join(lineas)


# =========================================================
# APP PRINCIPAL
# =========================================================

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import os
import random
from glob import glob

# =========================================================
# NOTA: Asegúrate de tener declaradas tus funciones de LSM aquí arriba:
# - traducir_a_glosa_lsm_tecnica(texto)
# - traducir_a_glosa_lsm_natural(texto)
# - obtener_datos_tecnicos(texto, glosa)
# - tokenizar_glosa_para_animacion(glosa)
# =========================================================

class TraductorLSMApp:
    """Interfaz grafica del traductor LSM.

    Administra la entrada del usuario, la salida en glosa visible, el panel
    tecnico y la lista de tokens que simula la secuencia de animacion.
    """

    def __init__(self, root):
        """Inicializa estado de la ventana y construye la interfaz."""

        self.root = root
        self.root.title("Traductor Español → Glosa LSM")
        self.root.geometry("1100x650")
        self.root.minsize(900, 550)
        self.root.configure(fg_color="white")

        self.tecnico_visible = False
        self.avatar_frames = self.cargar_frames_avatar()
        self.ultimo_avatar = None
        self.crear_interfaz()

    def cargar_frames_avatar(self):
        """Carga imagenes PNG del avatar desde la carpeta ``similar``."""

        base_dir = os.path.dirname(os.path.abspath(__file__))
        patron = os.path.join(base_dir, "similar", "simibailando (*.png")
        rutas = sorted(glob(patron))

        frames = []
        for ruta in rutas:
            try:
                frames.append(tk.PhotoImage(file=ruta))
            except tk.TclError:
                continue

        return frames

    def actualizar_frame_avatar(self):
        """Muestra un frame aleatorio del avatar evitando repetir el anterior."""

        if not self.avatar_frames or not hasattr(self, "avatar_frame_label"):
            return

        if len(self.avatar_frames) == 1:
            indice = 0
        else:
            opciones = list(range(len(self.avatar_frames)))
            if self.ultimo_avatar in opciones:
                opciones.remove(self.ultimo_avatar)
            indice = random.choice(opciones)

        self.ultimo_avatar = indice
        imagen = self.avatar_frames[indice]
        self.avatar_frame_label.configure(image=imagen, text="")
        self.avatar_frame_label.image = imagen

    def crear_interfaz(self):
        """Crea la estructura general de la ventana."""

        # Contenedor general (Main grid)
        # Usamos un CTkFrame transparente para que actúe como el 'main' original
        main = ctk.CTkFrame(self.root, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=34, pady=34)

        # --- HEADER (Título y Subtítulo) ---
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))

        titulo = ctk.CTkLabel(
            header, 
            text="Traductor Español → LSM", 
            font=("Segoe UI", 24, "bold")
        )
        titulo.pack(anchor="w")

        subtitulo = ctk.CTkLabel(
            header, 
            text="Prototipo de texto a glosa LSM con vista previa de animación palabra por palabra.", 
            font=("Segoe UI", 13),
            text_color="#5E5E5E"
        )
        subtitulo.pack(anchor="w")

        # --- DIVISIÓN IZQUIERDA / DERECHA ---
        # Nota: CustomTkinter maneja mejor la distribución con frames normales/grids que con PanedWindow
        cuerpo = ctk.CTkFrame(main, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True)
        
        # Panel izquierdo ocupará el 65% del ancho, el derecho el 35%
        self.panel_izquierdo = ctk.CTkFrame(cuerpo, fg_color="white")
        self.panel_izquierdo.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.panel_derecho = ctk.CTkFrame(cuerpo, fg_color="transparent")
        self.panel_derecho.configure(width=320)
        self.panel_derecho.pack(side="right", fill="both", expand=False, padx=(10, 0))

        self.crear_panel_izquierdo()
        self.crear_panel_derecho()

    def crear_panel_con_sombra(self, parent, corner_radius=12, fg_color="#FFFFFF"):
        """Crea un contenedor reutilizable con borde y radio de esquina."""

        contenedor = ctk.CTkFrame(parent, fg_color="transparent")

        panel = ctk.CTkFrame(
            contenedor,
            fg_color=fg_color,
            corner_radius=corner_radius,
            border_width=1,
            border_color="#D0D0D0"
        )
        panel.pack(fill="both", expand=True)

        return contenedor, panel

    def crear_panel_izquierdo(self):
        """Construye los controles de entrada, botones, glosa y detalles."""

        # --- ENTRADA (Panel con sombra y bordes redondeados automática) ---
        # 'corner_radius' se encarga de redondearlo y darle un aspecto moderno
        entrada_container, entrada_frame = self.crear_panel_con_sombra(self.panel_izquierdo)
        entrada_container.pack(fill="both", expand=True, pady=(0, 10))

        titulo_panel_entrada = ctk.CTkLabel(
            entrada_frame, 
            text="Texto en español", 
            font=("Segoe UI", 14, "bold")
        )
        titulo_panel_entrada.pack(anchor="w", padx=15, pady=(12, 4))

        # Cuadro de texto nativo de CustomTkinter
        self.texto_entrada = ctk.CTkTextbox(
            entrada_frame, 
            font=("Segoe UI", 13),
            activate_scrollbars=True,
            border_color="#53BAFF", border_width=1
        )
        self.texto_entrada.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.texto_entrada.insert("1.0", "El gato negro duerme en la cama.")

        # --- BOTONES ---
        botones_frame = ctk.CTkFrame(self.panel_izquierdo, fg_color="transparent")
        botones_frame.pack(fill="x", pady=10)

        # Botón Traducir (Estilo principal, color llamativo opcional)
        self.btn_traducir = ctk.CTkButton(
            botones_frame, 
            text="Traducir a LSM", 
            font=("Segoe UI", 12, "bold"),
            height=40,
            command=self.traducir
        )
        self.btn_traducir.pack(side="left", padx=(0, 8))

        # Botón Mostrar Técnico
        self.btn_ojo = ctk.CTkButton(
            botones_frame, 
            text="👁 Mostrar técnico", 
            fg_color="#FFFFFF", hover_color="#CECECE",
            text_color="#000000",
            border_color="#D0D0D0",
            border_width=1,
            height=40, 
            command=self.toggle_tecnico
        )
        self.btn_ojo.pack(side="left", padx=(0, 8))

        # Botón Limpiar
        self.btn_limpiar = ctk.CTkButton(
            botones_frame, 
            text="Limpiar",
            height=40,
            text_color="#000000",
            border_color="#D0D0D0",
            border_width=1, 
            fg_color="#FFFFFF", hover_color="#CACACA", # Tonos rojos
            command=self.limpiar
        )
        self.btn_limpiar.pack(side="left")

        # --- SALIDA GLOSA (Panel con sombra automático) ---
        glosa_container, glosa_frame = self.crear_panel_con_sombra(self.panel_izquierdo)
        glosa_container.pack(fill="both", expand=True, pady=10)

        titulo_glosa = ctk.CTkLabel(
            glosa_frame, 
            text="Glosa LSM", 
            font=("Segoe UI", 14, "bold")
        )
        titulo_glosa.pack(anchor="w", padx=15, pady=(12, 4))

        self.texto_glosa = ctk.CTkTextbox(
            glosa_frame, 
            font=("Consolas", 15, "bold"),
            activate_scrollbars=True
        )
        self.texto_glosa.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # --- TÉCNICO OCULTO ---
        self.tecnico_frame, tecnico_frame = self.crear_panel_con_sombra(self.panel_izquierdo)
        # No hace pack al inicio porque está oculto

        titulo_tecnico = ctk.CTkLabel(
            tecnico_frame, 
            text="Detalles técnicos", 
            font=("Segoe UI", 14, "bold")
        )
        titulo_tecnico.pack(anchor="w", padx=15, pady=(12, 4))

        self.texto_tecnico = ctk.CTkTextbox(
            tecnico_frame, 
            font=("Consolas", 12),
            activate_scrollbars=True
        )
        self.texto_tecnico.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def crear_panel_derecho(self):
        """Construye la vista de avatar, lista de tokens y controles."""

        # --- PANEL DE ANIMACIÓN ---
        anim_container, anim_frame = self.crear_panel_con_sombra(self.panel_derecho)
        anim_container.pack(fill="both", expand=True)

        titulo_anim = ctk.CTkLabel(
            anim_frame, 
            text="Vista de animación", 
            font=("Segoe UI", 14, "bold")
        )
        titulo_anim.pack(anchor="w", padx=15, pady=(12, 4))

        descripcion = ctk.CTkLabel(
            anim_frame, 
            text="Secuencia que ejecutaría el avatar :b", 
            font=("Segoe UI", 12),
            wraplength=260
        )
        descripcion.pack(anchor="w", padx=15, pady=(0, 10))

        avatar_container = ctk.CTkFrame(anim_frame, fg_color="#F7F7F7", border_width=1, border_color="#D3D3D3")
        avatar_container.pack(fill="x", padx=15, pady=(0, 10))

        avatar_titulo = ctk.CTkLabel(
            avatar_container,
            text="Avatar",
            font=("Segoe UI", 12, "bold"),
            text_color="#4B4B4B"
        )
        avatar_titulo.pack(anchor="w", padx=10, pady=(8, 4))

        self.avatar_frame_label = ctk.CTkLabel(avatar_container, text="")
        self.avatar_frame_label.pack(padx=10, pady=(0, 10))

        # Contenedor de la lista (un sutil borde alrededor)
        rectangulo = ctk.CTkFrame(anim_frame, fg_color="transparent", border_width=2, border_color="#D3D3D3")
        rectangulo.pack(fill="both", expand=True, padx=15, pady=10)

        # Mantenemos el tk.Listbox clásico porque CustomTkinter no tiene Listbox nativo,
        # pero lo estilizamos para que encaje perfectamente.
        self.animacion_lista = tk.Listbox(
            rectangulo,
            font=("Segoe UI", 16, "bold"),
            justify="center",
            activestyle="none",
            bd=0,
            highlightthickness=0,
            bg="#f9f9f9" if ctk.get_appearance_mode() == "Light" else "#2b2b2b",
            fg="black" if ctk.get_appearance_mode() == "Light" else "white"
        )
        self.animacion_lista.pack(fill="both", expand=True, padx=5, pady=5)

        # Controles de reproducción
        controles = ctk.CTkFrame(anim_frame, fg_color="transparent")
        controles.pack(fill="x", padx=15, pady=(0, 15))

        self.btn_anterior = ctk.CTkButton(controles, text="◀", width=40, command=self.animacion_anterior)
        self.btn_anterior.pack(side="left", padx=(0, 6))

        self.btn_reproducir = ctk.CTkButton(controles, text="Reproducir demo", command=self.reproducir_demo)
        self.btn_reproducir.pack(side="left", expand=True, fill="x", padx=(0, 6))

        self.btn_siguiente = ctk.CTkButton(controles, text="▶", width=40, command=self.animacion_siguiente)
        self.btn_siguiente.pack(side="left")

        self.indice_animacion = 0
        self.actualizar_frame_avatar()

    # =====================================================
    # LÓGICA Y ACCIONES (Se mantienen igual de eficientes)
    # =====================================================

    def traducir(self):
        """Traduce el texto escrito y actualiza glosa, detalles y animacion."""

        texto = self.texto_entrada.get("1.0", "end").strip()

        if not texto:
            messagebox.showwarning("Texto vacío", "Escribe una oración para traducir.")
            return

        try:
            glosa_tecnica = traducir_a_glosa_lsm_tecnica(texto)
            glosa_visible = traducir_a_glosa_lsm_natural(texto)
        except NameError:
            messagebox.showerror(
                "Error",
                "No encontré las funciones de traducción.\nAsegúrate de que estén declaradas arriba en el script."
            )
            return
        except Exception as e:
            messagebox.showerror("Error al traducir", str(e))
            return

        self.texto_glosa.delete("1.0", "end")
        self.texto_glosa.insert("1.0", glosa_visible)

        self.actualizar_animacion(glosa_visible)

        tecnico = obtener_datos_tecnicos(texto, glosa_tecnica)
        self.texto_tecnico.delete("1.0", "end")
        self.texto_tecnico.insert("1.0", tecnico)

    def actualizar_animacion(self, glosa):
        """Refresca la lista visual con los tokens de la glosa visible."""

        self.animacion_lista.delete(0, "end")
        tokens = tokenizar_glosa_para_animacion(glosa)

        for token in tokens:
            self.animacion_lista.insert("end", token)

        self.indice_animacion = 0
        if tokens:
            self.animacion_lista.selection_set(0)
            self.animacion_lista.activate(0)
            self.animacion_lista.see(0)
            self.actualizar_frame_avatar()

    def toggle_tecnico(self):
        """Muestra u oculta el panel con datos tecnicos."""

        if self.tecnico_visible:
            self.tecnico_frame.pack_forget()
            self.btn_ojo.configure(text="Mostrar técnico")
            self.tecnico_visible = False
        else:
            self.tecnico_frame.pack(fill="both", expand=True, pady=(10, 0))
            self.btn_ojo.configure(text="Ocultar técnico")
            self.tecnico_visible = True

    def limpiar(self):
        """Limpia entrada, salidas y estado de animacion."""

        self.texto_entrada.delete("1.0", "end")
        self.texto_glosa.delete("1.0", "end")
        self.texto_tecnico.delete("1.0", "end")
        self.animacion_lista.delete(0, "end")
        self.indice_animacion = 0

    def animacion_anterior(self):
        """Selecciona el token anterior en la secuencia de animacion."""

        total = self.animacion_lista.size()
        if total == 0: return
        self.indice_animacion = max(0, self.indice_animacion - 1)
        self.seleccionar_animacion_actual()

    def animacion_siguiente(self):
        """Selecciona el siguiente token en la secuencia de animacion."""

        total = self.animacion_lista.size()
        if total == 0: return
        self.indice_animacion = min(total - 1, self.indice_animacion + 1)
        self.seleccionar_animacion_actual()

    def seleccionar_animacion_actual(self):
        """Sincroniza la seleccion visual con ``indice_animacion``."""

        self.animacion_lista.selection_clear(0, "end")
        self.animacion_lista.selection_set(self.indice_animacion)
        self.animacion_lista.activate(self.indice_animacion)
        self.animacion_lista.see(self.indice_animacion)
        self.actualizar_frame_avatar()

    def reproducir_demo(self):
        """Inicia la reproduccion automatica de la secuencia actual."""

        total = self.animacion_lista.size()
        if total == 0: return
        self.indice_animacion = 0
        self.reproducir_paso()

    def reproducir_paso(self):
        """Avanza un paso de la reproduccion automatica."""

        total = self.animacion_lista.size()
        if self.indice_animacion >= total: return

        self.seleccionar_animacion_actual()
        self.indice_animacion += 1
        self.root.after(700, self.reproducir_paso)


if __name__ == "__main__":
    ctk.set_appearance_mode("Light") 
    ctk.set_default_color_theme("blue") 

    root = ctk.CTk()
    app = TraductorLSMApp(root)
    root.mainloop()
