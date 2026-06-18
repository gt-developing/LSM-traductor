"""Carga centralizada del modelo de lenguaje usado por el traductor."""

import spacy

try:
    import es_core_news_lg

    nlp = es_core_news_lg.load()
except ImportError:
    nlp = spacy.load("es_core_news_lg")
