# Traductor LSM

Prototipo de traductor de texto en espanol a glosa para LSM. El proyecto toma
una oracion escrita, la analiza con spaCy, extrae eventos linguisticos y genera
una glosa visible que tambien se separa en tokens para simular una secuencia de
animacion.

## Caracteristicas

- Interfaz grafica con CustomTkinter.
- Analisis linguistico con spaCy.
- Generacion de glosa tecnica para depuracion.
- Generacion de glosa visible para el usuario.
- Deteccion de preguntas, negacion, tiempo, sujeto, objeto, lugar y conectores.
- Soporte para verbos encadenados como `puede comprar`, `quiere estudiar` o
  `tiene que estudiar`.
- Vista de tokens para una animacion palabra por palabra.

## Estructura del proyecto

```text
.
|-- FLUJO.md
|-- funciones.md
|-- README.md
|-- similar/
|   |-- simibailando (1).png
|   |-- ...
|-- traductor_lsm/
|   |-- __init__.py
|   |-- app.py
|   |-- analisis.py
|   |-- constructor_glosa.py
|   |-- glosarios.py
|   |-- interfaz_utilidades.py
|   |-- modelo_spacy.py
|   |-- pruebas.py
|   |-- traductor.py
```

## Requisitos

- Python 3.11 o superior recomendado.
- pip.
- Entorno virtual recomendado.

Dependencias principales:

- `spacy`
- `customtkinter`
- Modelo de spaCy `es_core_news_lg`

## Instalacion

Crear y activar un entorno virtual:

```bash
python -m venv .venv
```

En Windows:

```bash
.venv\Scripts\activate
```

Instalar dependencias:

```bash
pip install spacy customtkinter
python -m spacy download es_core_news_lg
```

## Ejecucion

Desde la raiz del proyecto:

```bash
python -m traductor_lsm.app
```

Esto abre la interfaz grafica del traductor.

## Uso basico

1. Escribe una oracion en espanol en el cuadro de texto.
2. Presiona `Traducir a LSM`.
3. Revisa la glosa final en el panel `Glosa LSM`.
4. Usa `Mostrar tecnico` para ver la glosa tecnica y los tokens generados.
5. Usa los controles de la derecha para recorrer la secuencia de animacion.

## Flujo general

```text
Texto original
  -> app.py captura la entrada
  -> traductor.py coordina la traduccion
  -> modelo_spacy.py aplica spaCy
  -> analisis.py detecta pregunta y extrae eventos
  -> glosarios.py aporta equivalencias conocidas
  -> constructor_glosa.py ordena las partes de la glosa
  -> app.py muestra la frase final
  -> interfaz_utilidades.py genera tokens para animacion
```

Para una explicacion mas detallada del flujo paso a paso, revisa
[`FLUJO.md`](FLUJO.md).

## Ejemplo conceptual

Entrada:

```text
Los estudiantes tienen que estudiar manana.
```

Salida esperada:

```text
MANANA ESTUDIANTE(PL) ESTUDIAR TENER
```

## Pruebas manuales

El archivo `traductor_lsm/pruebas.py` contiene casos de prueba manuales y un
banco de confiabilidad.

Ejecutar:

```bash
python -m traductor_lsm.pruebas
```

## Documentacion adicional

- [`FLUJO.md`](FLUJO.md): explica el camino completo hasta llegar a la frase
  final.
- [`funciones.md`](funciones.md): resume las funciones principales de la
  logica del traductor.

## Estado del proyecto

Este proyecto es un prototipo academico/en desarrollo. La salida depende del
analisis de spaCy y de las reglas definidas en los modulos de analisis,
glosarios y construccion de glosa.

