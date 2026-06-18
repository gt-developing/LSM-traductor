# Flujo del traductor LSM

Este documento explica el camino que sigue una frase desde que el usuario la
escribe hasta que aparece la frase final en glosa LSM.

## 1. Punto de entrada

El proyecto esta organizado como paquete en `traductor_lsm/`.

La aplicacion se inicia desde:

```bash
python -m traductor_lsm.app
```

Ese comando ejecuta `traductor_lsm/app.py`. Al final del archivo se llama a
`ejecutar_app()`, que crea la ventana con CustomTkinter y monta la clase
`TraductorLSMApp`.

## 2. Captura del texto

En `traductor_lsm/app.py`, el usuario escribe una oracion en el cuadro
`self.texto_entrada`.

Cuando presiona el boton `Traducir a LSM`, se ejecuta el metodo:

```python
TraductorLSMApp.traducir()
```

Este metodo hace cuatro cosas principales:

1. Lee el texto original.
2. Genera una glosa tecnica con `traducir_a_glosa_lsm_tecnica(texto)`.
3. Genera la glosa visible final con `traducir_a_glosa_lsm_natural(texto)`.
4. Actualiza la interfaz con la glosa final, los datos tecnicos y la lista de
   tokens para animacion.

## 3. Entrada al flujo principal

Las funciones principales viven en `traductor_lsm/traductor.py`.

Hay dos salidas:

- `traducir_a_glosa_lsm_tecnica(texto)`: salida de depuracion.
- `traducir_a_glosa_lsm_natural(texto)`: frase final que ve el usuario.

Ambas empiezan igual:

```python
doc = nlp(texto)
tipo_pregunta = detectar_pregunta(doc)
eventos = extraer_eventos(doc)
```

Aqui sucede lo siguiente:

1. `nlp(texto)` viene de `traductor_lsm/modelo_spacy.py`.
2. spaCy analiza la frase y entrega tokens con lema, categoria gramatical,
   dependencias y rasgos morfologicos.
3. `detectar_pregunta(doc)` revisa si la frase tiene signos de pregunta.
4. `extraer_eventos(doc)` convierte la frase en eventos estructurados.

## 4. Carga del modelo spaCy

El archivo `traductor_lsm/modelo_spacy.py` centraliza el modelo:

```python
nlp = spacy.load("es_core_news_lg")
```

Esto evita cargar el modelo en muchos lugares distintos. El resto del proyecto
solo importa `nlp` y lo reutiliza.

## 5. Deteccion de pregunta

La funcion `detectar_pregunta(doc)` esta en `traductor_lsm/analisis.py`.

Primero revisa si el texto contiene signos de pregunta. Si no hay signos,
devuelve `None`.

Cuando hay pregunta, clasifica el tipo:

- `PORQUE` para preguntas de causa.
- `QUE`, `QUIEN`, `DONDE`, `CUANDO` o `COMO` si encuentra esas palabras.
- `SI_NO` si hay signos de pregunta, pero no hay interrogativo especifico.

Ese valor no se mete al evento. Se guarda aparte como `tipo_pregunta` y se
agrega al final de la ultima linea de glosa.

## 6. Extraccion de eventos

La funcion mas importante del analisis es:

```python
extraer_eventos(doc)
```

Un evento representa una accion o estado detectado en la frase. Cada evento
tiene esta forma:

```python
{
    "tiempo": "",
    "lugar": "",
    "objeto": "",
    "sujeto": "",
    "verbo": "",
    "modal": "",
    "negacion": False,
    "conector": None,
    "es_encadenado": False
}
```

El flujo interno es:

1. Busca un tiempo global en toda la oracion con `obtener_tiempo_global(doc)`.
   Esto permite rescatar palabras como `AYER`, `HOY` o `MANANA` aunque spaCy no
   las conecte directamente al verbo.
2. Recorre cada token del documento.
3. Ignora tokens ya usados o tokens que no puedan funcionar como verbo.
4. Si el verbo es modal y tiene un infinitivo cercano, construye un evento
   encadenado.
5. Si no es encadenado, construye un evento normal.
6. Si no encuentra ningun evento, hace un segundo intento con verbos ambiguos.

## 7. Eventos normales

Un evento normal sale de un verbo principal.

Por ejemplo:

```text
El gato negro duerme en la cama.
```

El analisis busca:

- sujeto: `gato`
- adjetivos del sujeto: `negro`
- lugar: `cama`
- verbo: `duerme`

El evento queda conceptualmente asi:

```python
{
    "tiempo": "",
    "lugar": "CAMA",
    "objeto": "",
    "sujeto": "GATO NEGRO",
    "verbo": "DORMIR",
    "modal": "",
    "negacion": False,
    "conector": None,
    "es_encadenado": False
}
```

Despues `constructor_glosa.py` lo convierte al orden:

```text
TIEMPO LUGAR SUJETO OBJETO VERBO
```

Resultado:

```text
CAMA GATO NEGRO DORMIR
```

## 8. Eventos encadenados

Los eventos encadenados se usan cuando aparece un modal mas una accion:

```text
quiere comer
puede comprar
tiene que estudiar
no puede comprar
```

El modal queda en `modal` y la accion principal queda en `verbo`.

Ejemplo:

```text
Los estudiantes tienen que estudiar manana.
```

El evento queda conceptualmente asi:

```python
{
    "tiempo": "MANANA",
    "lugar": "",
    "objeto": "",
    "sujeto": "ESTUDIANTE(PL)",
    "verbo": "ESTUDIAR",
    "modal": "TENER",
    "negacion": False,
    "conector": None,
    "es_encadenado": True
}
```

El constructor arma primero la accion y despues el modal:

```text
MANANA ESTUDIANTE(PL) ESTUDIAR TENER
```

Si hay negacion, se pega al modal:

```text
COMPRAR PODER<NEG>
```

## 9. Grupos nominales

Los sustantivos se convierten con `obtener_grupo_nominal(token)`.

El orden que se usa para LSM es:

```text
POSESIVO SUSTANTIVO ADJETIVO CANTIDAD
```

Ejemplos:

- `mi mama` -> `MI MAMA`
- `libros nuevos` -> `LIBRO(PL) NUEVO`
- `tres libros nuevos` -> `LIBRO NUEVO TRES`

Si no hay cantidad explicita, la pluralidad se conserva con `(PL)`.

## 10. Diccionarios y respaldo

Las equivalencias viven en `traductor_lsm/glosarios.py`.

Ahi estan:

- `GLOSAS_VERBOS`
- `GLOSAS_SUSTANTIVOS`
- `GLOSAS_CANTIDADES`
- `INTERROGATIVOS`
- `VERBOS_MODALES`
- `VERBOS_AMBIGUOS`

Cuando una palabra no existe en los diccionarios, el traductor usa el lema de
spaCy en mayusculas como respaldo.

## 11. Construccion de la glosa tecnica

La glosa tecnica se construye en:

```python
traducir_a_glosa_lsm_tecnica(texto)
```

Por cada evento:

1. Si el evento trae conector, agrega una linea como `[PORQUE]`.
2. Llama a `construir_linea_tecnica(evento)`.
3. Si la frase era pregunta, agrega el marcador de pregunta al ultimo evento.

La linea tecnica siempre intenta conservar toda la informacion del evento:

```text
TIEMPO LUGAR SUJETO OBJETO VERBO
```

Esta salida sirve para revisar como entendio la frase el analizador.

## 12. Construccion de la frase final visible

La frase final visible se construye en:

```python
traducir_a_glosa_lsm_natural(texto)
```

Esta es la salida que aparece en el cuadro `Glosa LSM`.

Tiene tres caminos:

### Caso PORQUE

Si hay dos eventos y el segundo tiene conector `PORQUE`, el traductor compacta
la causa.

Ejemplo tecnico:

```text
MANANA ESCUELA ESTUDIANTE(PL) ESTUDIAR TENER
[PORQUE]
EXAMEN EXISTIR
```

Salida visible:

```text
MANANA ESCUELA ESTUDIANTE(PL) EXAMEN / ESTUDIAR TENER
```

La idea es colocar la causa antes de la accion final para que la frase visible
sea mas natural.

### Caso MIENTRAS

Si hay dos eventos y el segundo tiene conector `MIENTRAS`, los dos eventos se
unen con `/`.

Ejemplo:

```text
MI MAMA COCINAR / MI PAPA CASA LIMPIAR
```

### Caso normal

Si no hay caso especial, se construye cada evento con:

```python
construir_linea_natural(evento)
```

Actualmente `construir_linea_natural(evento)` reutiliza la misma estructura que
la tecnica:

```text
TIEMPO LUGAR SUJETO OBJETO VERBO
```

Si hay pregunta, el marcador se agrega al final.

Ejemplos:

- pregunta de si/no: `<?>`
- pregunta con interrogativo: `QUE<?>`, `DONDE<?>`, `PORQUE<?>`

## 13. Regreso a la interfaz

Cuando `app.py` recibe la glosa final:

```python
glosa_visible = traducir_a_glosa_lsm_natural(texto)
```

la coloca en:

```python
self.texto_glosa
```

Luego llama:

```python
self.actualizar_animacion(glosa_visible)
```

Esa funcion usa `tokenizar_glosa_para_animacion(glosa)` desde
`traductor_lsm/interfaz_utilidades.py`.

El resultado es una lista de tokens que alimenta la vista de animacion.

## 14. Panel tecnico

La interfaz tambien genera datos tecnicos con:

```python
obtener_datos_tecnicos(texto, glosa_tecnica)
```

Esto muestra:

1. Texto original.
2. Glosa tecnica generada.
3. Tokens derivados de esa glosa.

Este panel ayuda a revisar el comportamiento interno sin cambiar la frase final
que ve el usuario.

## Resumen completo

```text
Usuario escribe texto
  -> app.py lee el cuadro de entrada
  -> traductor.py recibe el texto
  -> modelo_spacy.py carga y aplica spaCy
  -> analisis.py detecta pregunta
  -> analisis.py extrae eventos
  -> glosarios.py aporta equivalencias cuando existen
  -> constructor_glosa.py ordena tiempo, lugar, sujeto, objeto y verbo
  -> traductor.py decide si usa caso normal, PORQUE o MIENTRAS
  -> app.py muestra la glosa visible final
  -> interfaz_utilidades.py separa tokens para la animacion
```

## Resumen corto

```text
texto original
  -> spaCy
  -> pregunta + eventos
  -> glosa tecnica
  -> glosa visible final
  -> tokens de animacion
```
