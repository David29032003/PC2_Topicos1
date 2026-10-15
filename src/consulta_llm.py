"""Necesidad de información -> LLM -> consulta estructurada -> JSON Schema (Semana 3).

Reutiliza de la PC1 el modelo local (llm.py, Qwen2.5-0.5B-Instruct greedy) y el
parseo en dos niveles (validacion.py). La validación tiene tres niveles:

    parseable      JSON exacto o recuperado del texto
    schema-valid   cumple schema/consulta.schema.json
    adecuada       intención esperada, sin abstención y consulta de 4 a 25 palabras
"""
from __future__ import annotations

import hashlib
import json

from jsonschema import Draft202012Validator

import config_pc2 as C
import llm  # noqa: E402  (PC1)
from config import DECODING, MODELOS  # noqa: E402  (PC1)
from validacion import parse_exacto, recuperar_objeto  # noqa: E402  (PC1)

VALIDATOR = Draft202012Validator(json.loads(C.SCHEMA_PATH.read_text(encoding="utf-8")))
POLITICA = "greedy"


def mensajes(necesidad: str) -> list[dict]:
    sistema = (C.PROMPTS / "system_consulta.txt").read_text(encoding="utf-8").strip()
    usuario = (C.PROMPTS / "Q1_consulta.txt").read_text(encoding="utf-8").strip().replace("{necesidad}", necesidad)
    return [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}]


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def generar(necesidad: str, seed: int = C.SEED) -> dict:
    """Generación con caché en disco (misma clave que la PC1: modelo, revisión, mensajes, decoding, semilla)."""
    msgs = mensajes(necesidad)
    model_id, revision = MODELOS[C.LLM_MODELO]
    key = _sha({"model": model_id, "rev": revision, "msgs": msgs, "decoding": DECODING[POLITICA], "seed": seed})
    cache = {}
    if C.CACHE_CONSULTAS.exists():
        for l in C.CACHE_CONSULTAS.read_text(encoding="utf-8").splitlines():
            if l.strip():
                d = json.loads(l)
                cache[d["key"]] = d["gen"]
    if key not in cache:
        gen = llm.generar(msgs, POLITICA, seed, modelo=C.LLM_MODELO)
        C.RESULTS.mkdir(parents=True, exist_ok=True)
        with C.CACHE_CONSULTAS.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"key": key, "gen": gen}, ensure_ascii=False) + "\n")
        cache[key] = gen
    return {**cache[key], "cache_key": key}


def validar(raw: str, intent_gold: str | None = None) -> dict:
    exacto = parse_exacto(raw)
    parsed = exacto if exacto is not None else recuperar_objeto(raw)
    r = {"json_exacto": exacto is not None, "json_recuperado": parsed is not None, "parsed": parsed,
         "schema_valid": False, "errores_schema": [], "query": None, "intent": None, "abstain": None,
         "intent_correcto": False, "longitud_ok": False, "adecuada": False}
    if parsed is None:
        r["estado"] = "json_invalido"
        return r
    errores = list(VALIDATOR.iter_errors(parsed))
    r["errores_schema"] = [f"{'/'.join(map(str, e.path)) or '<raíz>'}: {e.message}" for e in errores][:5]
    r["schema_valid"] = not errores
    if not r["schema_valid"]:
        r["estado"] = "schema_invalido"
        return r
    n = len(parsed["query"].split())
    r.update({"query": parsed["query"].strip(), "intent": parsed["intent"], "abstain": parsed["abstain"],
              "intent_correcto": intent_gold is None or parsed["intent"] == intent_gold,
              "longitud_ok": 4 <= n <= 25, "n_palabras_query": n})
    r["adecuada"] = r["intent_correcto"] and not r["abstain"] and r["longitud_ok"]
    r["estado"] = "valida_adecuada" if r["adecuada"] else "valida_no_adecuada"
    return r


def estructurar(necesidad: str, intent_gold: str | None = None, seed: int = C.SEED) -> dict:
    gen = generar(necesidad, seed)
    return {"necesidad": necesidad, "raw_text": gen["raw_text"], "latency_ms": gen["latency_ms"],
            "prompt_tokens": gen["prompt_tokens"], "generated_tokens": gen["generated_tokens"],
            **validar(gen["raw_text"], intent_gold)}
