"""Analisis linguistico: texto procesado por spaCy hacia eventos estructurados."""

from .glosarios import (
    GLOSAS_CANTIDADES,
    GLOSAS_SUSTANTIVOS,
    GLOSAS_VERBOS,
    INTERROGATIVOS,
    VERBOS_AMBIGUOS,
    VERBOS_MODALES,
)

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


