"""Casos manuales y banco de pruebas de confiabilidad del traductor."""

if __package__ in (None, ""):
    import os
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from traductor_lsm.traductor import (
        traducir_a_glosa_lsm_natural,
        traducir_a_glosa_lsm_tecnica,
    )
else:
    from .traductor import (
        traducir_a_glosa_lsm_natural,
        traducir_a_glosa_lsm_tecnica,
    )


def mostrar_ejemplos():
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
    mostrar_ejemplos()
    evaluar_casos()
