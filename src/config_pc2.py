"""Configuración única de la PC2 (recuperación densa verificable).

Todo lo que define una condición experimental vive aquí. La PC2 reutiliza el
código de la PC1 (lectura OCDS, LLM local, parseo JSON), por eso agrega ../src
al path.
"""
from __future__ import annotations

import sys
from pathlib import Path

PC2 = Path(__file__).resolve().parents[1]
REPO = PC2.parent
sys.path.insert(0, str(REPO / "src"))

DATA = PC2 / "data"
PROMPTS = PC2 / "prompts"
SCHEMA_PATH = PC2 / "schema" / "consulta.schema.json"
RESULTS = PC2 / "results"
FIGS = RESULTS / "figs"
CORPUS_PATH = DATA / "corpus.jsonl"
NECESIDADES_PATH = DATA / "necesidades.jsonl"
QRELS_PATH = DATA / "qrels.json"
CACHE_CONSULTAS = RESULTS / "cache_consultas.jsonl"

# Encoder canónico de la Semana 4 (384 dimensiones, ventana de 512 tokens).
ENCODER_ID = "intfloat/multilingual-e5-small"
ENCODER_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
PREFIJO_QUERY = "query: "
PREFIJO_PASSAGE = "passage: "

# Segmentación: se agrupan passages consecutivos hasta target_words, con un
# passage de solapamiento (mismo chunker que el Laboratorio 4).
TARGET_WORDS = {"small": 100, "baseline": 180, "large": 320}
OVERLAP_PASSAGES = 1
# Tope de seguridad = ventana de e5. Ningún chunk se trunca: si target_words no
# cabe en 512 tokens, el chunk se cierra antes (se registra en cada chunk).
MAX_TOKENS = 512
TOP_K_VALUES = [1, 3, 5]
MAX_K = max(TOP_K_VALUES)

# LLM que estructura la consulta (el mismo de la PC1, greedy).
LLM_MODELO = "0.5B"
SEED = 42

INTENTS = ["marca_sin_equivalente", "marca_con_equivalente", "compatibilidad_equipo_existente",
           "competencia", "resultado_adjudicacion", "otro"]
