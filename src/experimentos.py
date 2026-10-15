"""Experimentos de la PC2.

Uso:
    python pc2/src/experimentos.py

Exp. 1 - Consulta (basado en prompts): Q0 = necesidad original vs Q1 = campo
    "query" de la consulta estructurada por el LLM. Fijos: corpus, segmentación
    baseline (180 palabras, 1 passage de overlap), e5-small, L2, IndexFlatIP, k.
Exp. 2 - Chunking (sin prompts): small = 100, baseline = 180, large = 320
    palabras con las consultas Q0. Fijos: corpus, consultas, qrels, overlap,
    encoder, normalización, similitud, índice y k.

Salidas en pc2/results/: exp1_consulta.jsonl, exp2_chunking.jsonl,
chunks_<condicion>.jsonl, resumen.json, run_config.json
"""
from __future__ import annotations

import json
import os
import platform
import sys
from datetime import datetime

import numpy as np

import config_pc2 as C
import consulta_llm
import recuperador as R

sys.stdout.reconfigure(encoding="utf-8")


def validar_benchmark(docs, necesidades, qrels):
    passages = [p["passage_id"] for d in docs for p in d["passages"]]
    assert len(passages) == len(set(passages)), "passage_id duplicado"
    assert len({d["doc_id"] for d in docs}) == len(docs), "doc_id duplicado"
    ids = [n["query_id"] for n in necesidades]
    assert set(ids) == set(qrels), "cada consulta necesita sus qrels"
    faltan = {p for v in qrels.values() for p in v} - set(passages)
    assert not faltan, f"qrels apunta a passages inexistentes: {faltan}"
    assert all(qrels[q] for q in ids), "consulta sin evidencia relevante"


def top(rec: R.Recuperador, scores, idx, fila: int, k: int = C.MAX_K) -> list[dict]:
    return [{"rank": r + 1, "chunk_id": rec.chunks[int(i)]["chunk_id"], "doc_id": rec.chunks[int(i)]["doc_id"],
             "passage_ids": rec.chunks[int(i)]["passage_ids"], "score": round(float(scores[fila, r]), 4),
             "text": rec.chunks[int(i)]["text"]} for r, i in enumerate(idx[fila, :k])]


def recalls(rec, idx, fila, gold) -> dict:
    return {f"recall@{k}": R.recall_at_k(rec.chunks, idx[fila], set(gold), k) for k in C.TOP_K_VALUES}


def verificar_faiss(rec: R.Recuperador, q: np.ndarray, scores, idx) -> dict:
    """IndexFlatIP debe dar la misma búsqueda exacta que Q·Eᵀ en NumPy."""
    s_np, i_np = R.top_k_numpy(q, rec.vectores, C.MAX_K)
    mismos = bool(np.array_equal(i_np, idx))
    return {"mismo_orden": mismos, "max_dif_score": float(np.abs(s_np - scores).max()),
            "mismos_conjuntos": all(set(a) == set(b) for a, b in zip(i_np, idx))}


def estadisticas(rec: R.Recuperador) -> dict:
    pal = [c["n_words"] for c in rec.chunks]
    tok = [R.n_tokens(C.PREFIJO_PASSAGE + R.normalizar(c["text"])) for c in rec.chunks]
    return {"target_words": rec.target_words, "n_chunks": len(rec.chunks), "palabras_media": round(float(np.mean(pal)), 1),
            "palabras_max": int(max(pal)), "tokens_max": int(max(tok)), "tokens_media": round(float(np.mean(tok)), 1),
            "cortes_por_tokens": int(sum(c["corte_por_tokens"] for c in rec.chunks)),
            "chunks_sin_solape": int(R.validar_overlap(rec.chunks)), "dim": int(rec.vectores.shape[1]),
            "normas_L2": [round(float(x), 4) for x in np.linalg.norm(rec.vectores, axis=1)[[0, -1]]]}


def guardar_jsonl(nombre, filas):
    with (C.RESULTS / nombre).open("w", encoding="utf-8") as f:
        for x in filas:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")


def main():
    C.RESULTS.mkdir(parents=True, exist_ok=True)
    docs = R.corpus()
    necesidades = R.leer_jsonl(C.NECESIDADES_PATH)
    qrels = json.loads(C.QRELS_PATH.read_text(encoding="utf-8"))
    validar_benchmark(docs, necesidades, qrels)
    q0 = [n["necesidad"] for n in necesidades]

    # ---------------- Exp. 2: tamaño de chunk (también da el índice baseline) -------
    recs, resumen = {}, {"exp2": {}, "faiss_vs_numpy": {}, "chunks": {}}
    filas2 = []
    for cond, tw in C.TARGET_WORDS.items():
        rec = R.Recuperador(tw)
        recs[cond] = rec
        guardar_jsonl(f"chunks_{cond}.jsonl", rec.chunks)
        q, scores, idx = rec.buscar(q0)
        resumen["faiss_vs_numpy"][cond] = verificar_faiss(rec, q, scores, idx)
        resumen["chunks"][cond] = estadisticas(rec)
        for i, n in enumerate(necesidades):
            filas2.append({"condicion": cond, "target_words": tw, "query_id": n["query_id"], "consulta": q0[i],
                           "difficulty": n["difficulty"], "gold": qrels[n["query_id"]],
                           **recalls(rec, idx, i, qrels[n["query_id"]]), "top": top(rec, scores, idx, i)})
        media = {f"Recall@{k}": round(float(np.mean([f[f"recall@{k}"] for f in filas2 if f["condicion"] == cond])), 3)
                 for k in C.TOP_K_VALUES}
        resumen["exp2"][cond] = {"target_words": tw, **media}
        print(f"[exp2] {cond:8s} chunks={len(rec.chunks):2d} {media}", flush=True)
    guardar_jsonl("exp2_chunking.jsonl", filas2)

    # ---------------- Exp. 1: consulta original vs estructurada --------------------
    rec = recs["baseline"]
    filas1 = []
    estructuradas = [consulta_llm.estructurar(n["necesidad"], n["intent_gold"]) for n in necesidades]
    _, s0, i0 = rec.buscar(q0)
    usables = [e["query"] if e["schema_valid"] and not e["abstain"] else None for e in estructuradas]
    q1 = [u for u in usables if u]
    s1, i1 = (rec.buscar(q1)[1:] if q1 else (None, None))
    j = 0
    for i, (n, e) in enumerate(zip(necesidades, estructuradas)):
        gold = qrels[n["query_id"]]
        base = {"query_id": n["query_id"], "difficulty": n["difficulty"], "gold": gold, "intent_gold": n["intent_gold"]}
        f0 = {**base, "condicion": "Q0", "consulta": q0[i], **recalls(rec, i0, i, gold), "top": top(rec, s0, i0, i)}
        if usables[i]:
            f1 = {**base, "condicion": "Q1", "consulta": usables[i], **recalls(rec, i1, j, gold),
                  "top": top(rec, s1, i1, j)}
            j += 1
        else:  # sin consulta válida no se recupera nada: Recall = 0 (criterio estricto)
            f1 = {**base, "condicion": "Q1", "consulta": None, **{f"recall@{k}": 0.0 for k in C.TOP_K_VALUES},
                  "top": []}
        f1["llm"] = {k: e[k] for k in ("raw_text", "json_exacto", "json_recuperado", "schema_valid", "errores_schema",
                                         "query", "intent", "abstain", "intent_correcto", "longitud_ok", "adecuada",
                                         "estado", "latency_ms", "prompt_tokens", "generated_tokens")}
        top3_0 = {t["chunk_id"] for t in f0["top"][:3]}
        top3_1 = {t["chunk_id"] for t in f1["top"][:3]}
        f1["jaccard_top3_con_Q0"] = round(len(top3_0 & top3_1) / len(top3_0 | top3_1), 3) if top3_1 else 0.0
        filas1 += [f0, f1]
        print(f"[exp1] {n['query_id']} Q1={e['estado']:18s} intent={e['intent']} | {e['query']}", flush=True)
    guardar_jsonl("exp1_consulta.jsonl", filas1)
    q1_filas = [f for f in filas1 if f["condicion"] == "Q1"]
    resumen["exp1"] = {
        "n_necesidades": len(necesidades),
        "json_exacto_rate": round(float(np.mean([f["llm"]["json_exacto"] for f in q1_filas])), 3),
        "json_parseable_rate": round(float(np.mean([f["llm"]["json_recuperado"] for f in q1_filas])), 3),
        "schema_valid_rate": round(float(np.mean([f["llm"]["schema_valid"] for f in q1_filas])), 3),
        "intent_accuracy": round(float(np.mean([f["llm"]["intent_correcto"] for f in q1_filas])), 3),
        "abstain_rate": round(float(np.mean([bool(f["llm"]["abstain"]) for f in q1_filas])), 3),
        "adecuada_rate": round(float(np.mean([f["llm"]["adecuada"] for f in q1_filas])), 3),
        **{c: {f"Recall@{k}": round(float(np.mean([f[f"recall@{k}"] for f in filas1 if f["condicion"] == c])), 3)
               for k in C.TOP_K_VALUES} for c in ("Q0", "Q1")},
        "jaccard_top3_medio": round(float(np.mean([f["jaccard_top3_con_Q0"] for f in q1_filas])), 3),
    }
    print("[exp1]", json.dumps(resumen["exp1"], ensure_ascii=False), flush=True)
    (C.RESULTS / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")

    import faiss
    import sentence_transformers
    import torch
    cfg = {"fecha": datetime.now().isoformat(timespec="seconds"), "encoder": C.ENCODER_ID,
           "encoder_revision": C.ENCODER_REVISION, "prefijos": [C.PREFIJO_QUERY, C.PREFIJO_PASSAGE],
           "normalizacion_texto": "minúsculas", "normalizacion_vectores": "L2", "indice": "faiss.IndexFlatIP",
           "target_words": C.TARGET_WORDS, "overlap_passages": C.OVERLAP_PASSAGES, "max_tokens": C.MAX_TOKENS,
           "top_k": C.TOP_K_VALUES, "llm": consulta_llm.MODELOS[C.LLM_MODELO], "decoding": consulta_llm.POLITICA,
           "semilla": C.SEED, "faiss": faiss.__version__, "sentence_transformers": sentence_transformers.__version__,
           "torch": torch.__version__, "python": platform.python_version(), "plataforma": platform.platform(),
           "hf_offline": os.environ.get("HF_HUB_OFFLINE")}
    (C.RESULTS / "run_config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
