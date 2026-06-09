Resumen de funciones (lógica, sin interfaz)

- `es_interrogativo(token)`:
  - Devuelve True si `token` es un interrogativo conocido.

- `obtener_glosa(token)`:
  - Mapea un token a su glosa preferida, priorizando interrogativos,
    luego verbos y sustantivos mediante diccionarios, y finalmente
    devolviendo el lema en mayúsculas.

- `es_plural(token)`:
  - Comprueba la marca morfológica de plural en `token`.

- `obtener_cantidad(token)`:
  - Extrae cuantificadores o números asociados al token y devuelve
    la glosa correspondiente si existe.

- `obtener_posesivo(token)`:
  - Busca determinantes posesivos (mi/tu/su/nuestro/vuestro) y
    devuelve la glosa equivalente.

- `obtener_grupo_nominal(token)`:
  - Construye la representación del sintagma nominal con posesivo,
    sustantivo, adjetivos y cantidad/plural.

- `buscar_sujeto_cercano(token)`:
  - Si spaCy no conecta un sujeto como hijo del verbo, busca hacia
    la izquierda un candidato válido sin cruzar conectores o puntuación.

- `inferir_sujeto_desde_verbo(token)`:
  - Infere pronombres sujetos (YO/TU/NOSOTRO(PL)/USTED(PL)) según
    la morfología de persona y número del verbo.

- `es_posible_verbo(token)`:
  - Heurística para decidir si un token puede actuar como verbo,
    incluso cuando el POS tagging no es fiable.

- `detectar_pregunta(doc)`:
  - Detecta si el texto representa una pregunta y devuelve el tipo
    (`PORQUE`, `QUE`, `QUIEN`, `DONDE`, `CUANDO`, `COMO` o `SI_NO`).

- `obtener_tiempo_global(doc)`:
  - Busca adverbios temporales en todo el `doc` (ayer, hoy, mañana...).

- `tiene_negacion_cercana(token)`:
  - Determina si el token tiene una negación cercana (ej. "no").

- `buscar_verbo_accion_cercano(token)`:
  - Busca un verbo dependiente (infinitivo) cercano a un modal.

- `extraer_evento_verbo_encadenado(token)`:
  - Extrae un `evento` estructurado cuando hay un verbo modal que
    rige una acción (p. ej. "puede comprar").

- `es_verbo_ambiguo_en_contexto(tokens, i)`:
  - Detecta si una palabra ambigua (ej. "limpia") actúa como verbo
    en su contexto.

- `extraer_eventos_ambiguos(doc)`:
  - Maneja construcciones ambiguas extrayendo eventos heurísticamente.

- `extraer_eventos(doc)`:
  - Extrae la lista principal de eventos semánticos del `doc`. Soporta
    verbos encadenados, inferencia de sujeto y recuperación de tiempo
    global.

- `construir_verbo_evento(evento)`:
  - Construye la porción verbal de un evento, incluyendo marcadores
    de negación y modal cuando corresponda.

- `construir_partes_sin_verbo(evento)`:
  - Devuelve una lista con `tiempo`, `lugar`, `sujeto` y `objeto`.

- `construir_linea_tecnica(evento)`:
  - Forma una línea técnica completa (TIEMPO LUGAR SUJETO OBJETO VERBO).

- `obtener_causa_visible(evento_causa, tiempos_a_evitar)`:
  - Convierte un evento de causa en su versión visible evitando
    duplicar tiempos cuando sea necesario.

- `construir_linea_natural(evento)`:
  - Genera la línea "visible" a partir del evento. En este proyecto
    delega en la versión técnica para consistencia.

- `traducir_a_glosa_lsm_tecnica(texto)`:
  - Flujo principal: parsea con spaCy, extrae eventos y construye la
    glosa técnica (varias líneas) incluyendo conectores y marcas de
    pregunta.

- `traducir_a_glosa_lsm_natural(texto)`:
  - Genera la glosa visible para el usuario. Maneja casos especiales
    (PORQUE, MIENTRAS) y normaliza los eventos extraídos.

- `traducir_a_glosa_lsm(texto)`:
  - Wrapper de compatibilidad que devuelve la glosa técnica.

- `generar_glosa_visible(texto_o_glosa)`:
  - Interfaz simple para obtener la glosa visible desde el texto
    original.

- `tokenizar_glosa_para_animacion(glosa)`:
  - Convierte la glosa en una lista de tokens ordenados para
    animaciones palabra-por-palabra.

- `obtener_datos_tecnicos(texto, glosa)`:
  - Construye un bloque de texto con información útil para depuración
    (texto original, glosa y tokens para animación).

Notas:
- La interfaz (archivo principal) sincroniza la lista de tokens con
  una vista de avatar; la lógica de extracción y transformación de
  glosas está contenida en las funciones descritas arriba.
