"""Carga centralizada del modelo de lenguaje usado por el traductor."""

import spacy

nlp = spacy.load("es_core_news_lg")
