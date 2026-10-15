"""Segmentación, embeddings, índice FAISS y Recall@k (Semana 4).

documento -> passages -> chunks -> embeddings (e5, L2) -> IndexFlatIP -> top-k

El chunker es el del Laboratorio 4: agrupa passages consecutivos de un mismo
documento hasta target_words, con `overlap_passages` passages repetidos entre
chunks vecinos. Los qrels se definen sobre passage_id, así que no cambian
cuando cambia el tamaño del chunk.
"""
from __future__ import annotations

import json
from functools import lru_cache

import numpy as np

import config_pc2 as C


def leer_jsonl(path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def corpus() -> list[dict]:
    return leer_jsonl(C.CORPUS_PATH)


def normalizar(texto: str) -> str:
    """Normalización previa al encoder, igual para passages y consultas.

    El SEACE publica casi todo en MAYÚSCULAS y el tokenizador de e5 parte las
    mayúsculas en más piezas (medido: 2,4 tokens/palabra). En minúsculas el
    mismo texto ocupa ~15 % menos de la ventana de 512 tokens.
    """
    return texto.lower()


def cabe(textos: list[str], max_tokens: int | None) -> bool:
    if max_tokens is None:
        return True
    return n_tokens(C.PREFIJO_PASSAGE + normalizar(" ".join(textos))) <= max_tokens


def construir_chunks(documentos: list[dict], target_words: int,
                     overlap_passages: int = C.OVERLAP_PASSAGES,
                     max_tokens: int | None = C.MAX_TOKENS) -> list[dict]:
    """Agrupa passages hasta target_words SIN superar max_tokens (ventana del encoder).

    El tope de tokens solo se activa cuando target_words no cabe en la ventana;
    cada chunk registra si se cortó por tokens (`corte_por_tokens`).
    """
    if target_words <= 0 or overlap_passages < 0:
        raise ValueError("target_words > 0 y overlap_passages >= 0")
    chunks = []
    palabras_de = lambda p: len(p["text"].split())
    for doc in documentos:
        passages = doc["passages"]
        start, numero, solape = 0, 0, 0
        while start < len(passages):
            actual, palabras, end, por_tokens = [], 0, start, False
            while end < len(passages):
                n = palabras_de(passages[end])
                if actual and palabras + n > target_words:
                    break
                if actual and not cabe([p["text"] for p in actual] + [passages[end]["text"]], max_tokens):
                    por_tokens = True
                    break
                actual.append(passages[end])
                palabras += n
                end += 1
            numero += 1
            chunks.append({
                "chunk_id": f"{doc['doc_id']}-C{numero:02d}-W{target_words}",
                "doc_id": doc["doc_id"],
                "passage_ids": [p["passage_id"] for p in actual],
                "n_words": palabras,
                "overlap_previo": solape,
                "corte_por_tokens": por_tokens,
                "text": " ".join(p["text"] for p in actual),
            })
            if end >= len(passages):
                break
            siguiente = max(end - overlap_passages, start + 1)
            # Diferencia con el Laboratorio 4: si el passage siguiente no cabe
            # junto al solapamiento, el chunk nuevo repetiría solo el
            # solapamiento (un duplicado). En ese caso se empieza sin solapar.
            repetido = [p["text"] for p in passages[siguiente:end]]
            n_rep = sum(len(t.split()) for t in repetido)
            if siguiente < end and (n_rep + palabras_de(passages[end]) > target_words
                                    or not cabe(repetido + [passages[end]["text"]], max_tokens)):
                siguiente = end
            solape = end - siguiente
            start = siguiente
    return chunks


def validar_overlap(chunks: list[dict], esperado: int = C.OVERLAP_PASSAGES) -> int:
    """Verifica el solapamiento realizado; devuelve cuántos chunks no pudieron solapar."""
    por_doc: dict[str, list[dict]] = {}
    for ch in chunks:
        por_doc.setdefault(ch["doc_id"], []).append(ch)
    sin_solape = 0
    for doc_id, lista in por_doc.items():
        for a, b in zip(lista, lista[1:]):
            real = len(set(a["passage_ids"]) & set(b["passage_ids"]))
            if real != b["overlap_previo"] or real not in (0, esperado):
                raise AssertionError(f"{doc_id}: overlap {real}, registrado {b['overlap_previo']}")
            if set(b["passage_ids"]) <= set(a["passage_ids"]):
                raise AssertionError(f"{b['chunk_id']} repite un chunk anterior")
            sin_solape += real == 0
    return sin_solape


@lru_cache(maxsize=1)
def encoder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(C.ENCODER_ID, revision=C.ENCODER_REVISION, device="cpu")


def n_tokens(texto: str) -> int:
    return len(encoder().tokenizer(texto, add_special_tokens=True, truncation=False)["input_ids"])


def codificar(textos: list[str], prefijo: str) -> np.ndarray:
    """Embeddings L2-normalizados. Se detiene si algún texto excede la ventana
    del encoder: la truncación agregaría una segunda variable al experimento."""
    entradas = [prefijo + normalizar(t) for t in textos]
    maximo = max(n_tokens(t) for t in entradas)
    if maximo > encoder().max_seq_length:
        raise ValueError(f"truncación: {maximo} tokens > {encoder().max_seq_length}")
    return encoder().encode(entradas, convert_to_numpy=True, normalize_embeddings=True,
                            batch_size=16).astype("float32")


def indice(vectores: np.ndarray):
    import faiss

    idx = faiss.IndexFlatIP(vectores.shape[1])  # búsqueda exhaustiva por producto interno
    idx.add(vectores)
    return idx


def top_k_numpy(consultas: np.ndarray, vectores: np.ndarray, k: int):
    """Misma búsqueda exacta sin FAISS, para verificar el índice."""
    s = consultas @ vectores.T
    orden = np.argsort(-s, axis=1, kind="stable")[:, :k]
    return np.take_along_axis(s, orden, axis=1), orden


def recall_at_k(chunks: list[dict], indices_fila, gold: set[str], k: int) -> float:
    cubiertos = set()
    for i in indices_fila[:k]:
        cubiertos.update(chunks[int(i)]["passage_ids"])
    return len(gold & cubiertos) / len(gold)


class Recuperador:
    """Política de recuperación: encoder + índice + chunks + top-k."""

    def __init__(self, target_words: int):
        self.target_words = target_words
        self.chunks = construir_chunks(corpus(), target_words)
        validar_overlap(self.chunks)
        self.vectores = codificar([c["text"] for c in self.chunks], C.PREFIJO_PASSAGE)
        self.index = indice(self.vectores)

    def buscar(self, consultas: list[str], k: int = C.MAX_K):
        q = codificar(consultas, C.PREFIJO_QUERY)
        scores, idx = self.index.search(q, k)
        return q, scores, idx
