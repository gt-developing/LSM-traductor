"""Funciones pequenas usadas por la interfaz grafica."""

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


