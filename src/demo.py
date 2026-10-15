"""Demostración de la PC2 (2 minutos): necesidad -> JSON -> validación -> encoder -> top-k -> Recall@k.

Uso:
    python pc2/src/demo.py N5                       # una necesidad del benchmark (muestra Recall@k)
    python pc2/src/demo.py "texto libre" --k 3      # cualquier necesidad (sin qrels, sin Recall)
    python pc2/src/demo.py N5 --chunk small         # misma necesidad con otra segmentación

Reutiliza la caché de generaciones: si la necesidad ya se corrió, no vuelve a llamar al LLM.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

os.environ.setdefault("HF_HUB_OFFLINE", "1")
import config_pc2 as C
import consulta_llm
import recuperador as R

sys.stdout.reconfigure(encoding="utf-8")


def titulo(t: str):
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("necesidad", help="id del benchmark (N1..N5) o texto libre")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--chunk", default="baseline", choices=list(C.TARGET_WORDS))
    ap.add_argument("--q0", action="store_true", help="usar la necesidad original en vez de la consulta del LLM")
    args = ap.parse_args()

    necesidades = {n["query_id"]: n for n in R.leer_jsonl(C.NECESIDADES_PATH)}
    qrels = json.loads(C.QRELS_PATH.read_text(encoding="utf-8"))
    n = necesidades.get(args.necesidad.upper())
    texto = n["necesidad"] if n else args.necesidad

    titulo("1. Necesidad de información")
    print(texto)

    titulo("2. LLM -> consulta estructurada (Qwen2.5-0.5B-Instruct, greedy)")
    e = consulta_llm.estructurar(texto, n["intent_gold"] if n else None)
    print("Salida cruda del modelo:\n" + e["raw_text"])

    titulo("3. Validación (JSON Schema Draft 2020-12 + chequeo semántico)")
    print(f"JSON exacto: {e['json_exacto']} | JSON recuperable: {e['json_recuperado']} | schema-valid: {e['schema_valid']}")
    if e["errores_schema"]:
        print("Errores:", e["errores_schema"])
    if e["schema_valid"]:
        extra = f" (esperada: {n['intent_gold']})" if n else ""
        print(f"intent: {e['intent']}{extra} | abstain: {e['abstain']} | palabras de la query: {e['n_palabras_query']}")
        print("Estado:", e["estado"])

    consulta = texto if (args.q0 or not e["schema_valid"] or e["abstain"]) else e["query"]
    titulo(f"4. Consulta enviada al encoder ({C.ENCODER_ID})")
    print(repr(C.PREFIJO_QUERY + R.normalizar(consulta)))

    titulo(f"5. Top-{args.k} con IndexFlatIP · chunks '{args.chunk}' ({C.TARGET_WORDS[args.chunk]} palabras)")
    rec = R.Recuperador(C.TARGET_WORDS[args.chunk])
    _, scores, idx = rec.buscar([consulta], max(args.k, C.MAX_K))
    gold = set(qrels.get(n["query_id"], [])) if n else set()
    for r in range(args.k):
        ch = rec.chunks[int(idx[0, r])]
        marcas = ", ".join(p + (" ★" if p in gold else "") for p in ch["passage_ids"])
        print(f"\n#{r + 1}  score={scores[0, r]:.4f}  {ch['chunk_id']}  passages: {marcas}")
        print("    " + ch["text"][:300] + ("…" if len(ch["text"]) > 300 else ""))

    if n:
        titulo("6. Recall@k (★ = passage relevante según qrels)")
        print("Evidencia relevante:", ", ".join(sorted(gold)))
        for k in C.TOP_K_VALUES:
            print(f"Recall@{k} = {R.recall_at_k(rec.chunks, idx[0], gold, k):.2f}")


if __name__ == "__main__":
    main()
