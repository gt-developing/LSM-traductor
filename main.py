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
    return token.text.lower() in INTERROGATIVOS


def obtener_glosa(token):
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
    return "Number=Plur" in str(token.morph)


def obtener_cantidad(token):
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


# =========================================================
# UTILIDADES PARA LA INTERFAZ
# =========================================================


def tokenizar_glosa_para_animacion(glosa):

    tokens = []

    for linea in glosa.splitlines():
        linea = linea.strip()

        if not linea:
            continue

        for palabra in linea.split():
            tokens.append(palabra)

    return tokens


def obtener_datos_tecnicos(texto, glosa):

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

# =========================================================
# NOTA: Asegúrate de tener declaradas tus funciones de LSM aquí arriba:
# - traducir_a_glosa_lsm_tecnica(texto)
# - traducir_a_glosa_lsm_natural(texto)
# - obtener_datos_tecnicos(texto, glosa)
# - tokenizar_glosa_para_animacion(glosa)
# =========================================================

class TraductorLSMApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Traductor Español → Glosa LSM")
        self.root.geometry("1100x650")
        self.root.minsize(900, 550)
        self.root.configure(fg_color="white")

        self.tecnico_visible = False
        self.crear_interfaz()

    def crear_interfaz(self):
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

    # =====================================================
    # LÓGICA Y ACCIONES (Se mantienen igual de eficientes)
    # =====================================================

    def traducir(self):
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
        self.animacion_lista.delete(0, "end")
        tokens = tokenizar_glosa_para_animacion(glosa)

        for token in tokens:
            self.animacion_lista.insert("end", token)

        self.indice_animacion = 0
        if tokens:
            self.animacion_lista.selection_set(0)
            self.animacion_lista.activate(0)
            self.animacion_lista.see(0)

    def toggle_tecnico(self):
        if self.tecnico_visible:
            self.tecnico_frame.pack_forget()
            self.btn_ojo.configure(text="👁 Mostrar técnico")
            self.tecnico_visible = False
        else:
            self.tecnico_frame.pack(fill="both", expand=True, pady=(10, 0))
            self.btn_ojo.configure(text="🙈 Ocultar técnico")
            self.tecnico_visible = True

    def limpiar(self):
        self.texto_entrada.delete("1.0", "end")
        self.texto_glosa.delete("1.0", "end")
        self.texto_tecnico.delete("1.0", "end")
        self.animacion_lista.delete(0, "end")
        self.indice_animacion = 0

    def animacion_anterior(self):
        total = self.animacion_lista.size()
        if total == 0: return
        self.indice_animacion = max(0, self.indice_animacion - 1)
        self.seleccionar_animacion_actual()

    def animacion_siguiente(self):
        total = self.animacion_lista.size()
        if total == 0: return
        self.indice_animacion = min(total - 1, self.indice_animacion + 1)
        self.seleccionar_animacion_actual()

    def seleccionar_animacion_actual(self):
        self.animacion_lista.selection_clear(0, "end")
        self.animacion_lista.selection_set(self.indice_animacion)
        self.animacion_lista.activate(self.indice_animacion)
        self.animacion_lista.see(self.indice_animacion)

    def reproducir_demo(self):
        total = self.animacion_lista.size()
        if total == 0: return
        self.indice_animacion = 0
        self.reproducir_paso()

    def reproducir_paso(self):
        total = self.animacion_lista.size()
        if self.indice_animacion >= total: return

        self.seleccionar_animacion_actual()
        self.indice_animacion += 1
        self.root.after(700, self.reproducir_paso)


# =========================================================
# EJECUTAR APP MODERNA
# =========================================================
if __name__ == "__main__":
    # Inicializamos con CustomTkinter para habilitar los temas modernos nativos
    ctk.set_appearance_mode("Light")  # Opciones: "Light", "Dark", "System"
    ctk.set_default_color_theme("blue")  # Opciones: "blue", "green", "dark-blue"

    root = ctk.CTk()
    app = TraductorLSMApp(root)
    root.mainloop()