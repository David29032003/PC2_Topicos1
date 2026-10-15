"""Tablas, figuras y auditoría de errores de la PC2 a partir de pc2/results/.

Uso:
    python pc2/src/reporte.py

Salidas: pc2/results/resumen.md, pc2/results/figs/*.png
"""
from __future__ import annotations

import json
import sys

import numpy as np

import config_pc2 as C
import graficos as g  # noqa: E402  (paleta de la PC1)
import recuperador as R

sys.stdout.reconfigure(encoding="utf-8")
CONDS = list(C.TARGET_WORDS)


def tabla(filas: list[dict], cols: list[str]) -> str:
    L = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    L += ["| " + " | ".join(str(f.get(c, "")) for c in cols) + " |" for f in filas]
    return "\n".join(L)


def num(x) -> str:
    return f"{x:.2f}".rstrip("0").rstrip(".") if isinstance(x, float) else str(x)


def texto_passage() -> dict:
    return {p["passage_id"]: p["text"] for d in R.corpus() for p in d["passages"]}


def auditoria(f: dict, k: int = 3) -> list[str]:
    gold = set(f["gold"])
    L = [f"- Consulta: *{f['consulta']}*", f"- Evidencia relevante (qrels): {', '.join(f['gold'])}",
         f"- Recall@1/3/5: {num(f['recall@1'])} / {num(f['recall@3'])} / {num(f['recall@5'])}", ""]
    L += ["| rank | chunk | score | passages (★ = relevante) | inicio del texto |", "|---|---|---|---|---|"]
    for t in f["top"][:k]:
        ps = ", ".join(p + (" ★" if p in gold else "") for p in t["passage_ids"])
        L.append(f"| {t['rank']} | {t['chunk_id']} | {t['score']:.4f} | {ps} | {t['text'][:110]}… |")
    return L


def fig_exp2(res: dict):
    import matplotlib.pyplot as plt

    ks = [f"Recall@{k}" for k in C.TOP_K_VALUES]
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    ax.set_xlim(-0.6, len(ks) - 0.4)
    ax.set_ylim(0, 1.18)
    g.limpiar_ejes(ax)
    ancho = 0.26
    colores = [g.RIESGO_COLOR["bajo"], g.RIESGO_COLOR["medio"], g.RIESGO_COLOR["alto"]]  # ordinal claro -> oscuro
    for j, cond in enumerate(CONDS):
        xs = [i + (j - 1) * ancho for i in range(len(ks))]
        vals = [res[cond][k] for k in ks]
        g.barras(ax, xs, vals, ancho * 0.88, colores[j])
        for x, v in zip(xs, vals):
            ax.text(x, v + 0.02, f"{v:.2f}".replace(".", ","), ha="center", va="bottom", fontsize=8, color=g.TINTA_2)
    ax.set_xticks(range(len(ks)), ks)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0], ["0", "0,25", "0,5", "0,75", "1"])
    ax.set_ylabel("Recall medio (5 necesidades)")
    g.leyenda(ax, [(f"{c} · {C.TARGET_WORDS[c]} palabras", col) for c, col in zip(CONDS, colores)], loc="upper left")
    ax.set_title("Exp. 2 · Recall@k según el tamaño del chunk", pad=10)
    C.FIGS.mkdir(parents=True, exist_ok=True)
    fig.savefig(C.FIGS / "exp2_recall.png")


def fig_exp1(filas1: list[dict]):
    import matplotlib.pyplot as plt

    ids = sorted({f["query_id"] for f in filas1})
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    ax.set_xlim(-0.6, len(ids) - 0.4)
    ax.set_ylim(0, 1.22)
    g.limpiar_ejes(ax)
    ancho = 0.36
    for j, (cond, color) in enumerate((("Q0", g.SERIE_1), ("Q1", g.SERIE_2))):
        vals = [next(f["recall@3"] for f in filas1 if f["query_id"] == q and f["condicion"] == cond) for q in ids]
        xs = [i + (j - 0.5) * ancho for i in range(len(ids))]
        g.barras(ax, xs, vals, ancho * 0.9, color)
        for x, v in zip(xs, vals):
            ax.text(x, v + 0.02, f"{v:.2f}".replace(".", ","), ha="center", va="bottom", fontsize=8, color=g.TINTA_2)
    ax.set_xticks(range(len(ids)), ids)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0], ["0", "0,25", "0,5", "0,75", "1"])
    ax.set_ylabel("Recall@3")
    g.leyenda(ax, [("Q0 · necesidad original", g.SERIE_1), ("Q1 · consulta del LLM", g.SERIE_2)], loc="upper left")
    ax.set_title("Exp. 1 · Recall@3 por necesidad (chunks de 180 palabras)", pad=10)
    C.FIGS.mkdir(parents=True, exist_ok=True)
    fig.savefig(C.FIGS / "exp1_recall3.png")


def main():
    res = json.loads((C.RESULTS / "resumen.json").read_text(encoding="utf-8"))
    filas1 = R.leer_jsonl(C.RESULTS / "exp1_consulta.jsonl")
    filas2 = R.leer_jsonl(C.RESULTS / "exp2_chunking.jsonl")
    L = ["# Resumen de resultados (PC2)", "",
         "Generado por `pc2/src/reporte.py` a partir de `pc2/results/*.jsonl`. 5 necesidades, 10 documentos, "
         f"{sum(len(d['passages']) for d in R.corpus())} passages.", ""]

    L += ["## Segmentación", "", tabla([{"condición": c, **res["chunks"][c]} for c in CONDS],
                                      ["condición", "target_words", "n_chunks", "palabras_media", "palabras_max",
                                       "tokens_media", "tokens_max", "cortes_por_tokens", "chunks_sin_solape"]), ""]
    L += ["FAISS `IndexFlatIP` vs búsqueda exacta en NumPy (Q·Eᵀ): " + ", ".join(
        f"{c}: mismo orden={v['mismo_orden']}, dif. máx. de score={v['max_dif_score']:.1e}"
        for c, v in res["faiss_vs_numpy"].items()), ""]

    e1 = res["exp1"]
    L += ["## Experimento 1 · consulta original (Q0) vs consulta estructurada (Q1)", "",
          tabla([{"métrica": k, "valor": num(v)} for k, v in e1.items() if not isinstance(v, dict)], ["métrica", "valor"]),
          "", tabla([{"consulta": c, **{k: num(v) for k, v in e1[c].items()}} for c in ("Q0", "Q1")],
                    ["consulta"] + [f"Recall@{k}" for k in C.TOP_K_VALUES]), ""]
    por_q = []
    for q in sorted({f["query_id"] for f in filas1}):
        a = next(f for f in filas1 if f["query_id"] == q and f["condicion"] == "Q0")
        b = next(f for f in filas1 if f["query_id"] == q and f["condicion"] == "Q1")
        por_q.append({"id": q, "Q0": a["consulta"], "Q1 (query del LLM)": b["consulta"], "intent": b["llm"]["intent"],
                      "estado": b["llm"]["estado"], "R@3 Q0": num(a["recall@3"]), "R@3 Q1": num(b["recall@3"]),
                      "Jaccard top-3": num(b["jaccard_top3_con_Q0"])})
    L += [tabla(por_q, list(por_q[0])), ""]

    L += ["## Experimento 2 · tamaño del chunk", "",
          tabla([{"condición": c, **{k: num(v) for k, v in res["exp2"][c].items()}} for c in CONDS],
                ["condición", "target_words"] + [f"Recall@{k}" for k in C.TOP_K_VALUES]), ""]
    pares = []
    for q in sorted({f["query_id"] for f in filas2}):
        fila = {"id": q}
        for c in CONDS:
            fila[f"R@3 {c}"] = num(next(f["recall@3"] for f in filas2 if f["query_id"] == q and f["condicion"] == c))
        base = float(fila["R@3 baseline"])
        fila["Δ small"] = num(round(float(fila["R@3 small"]) - base, 3))
        fila["Δ large"] = num(round(float(fila["R@3 large"]) - base, 3))
        pares.append(fila)
    L += ["Recall@3 por necesidad (Δ respecto de baseline):", "", tabla(pares, list(pares[0])), ""]

    L += ["## Auditoría: top-3 de cada necesidad en cada condición", ""]
    for q in sorted({f["query_id"] for f in filas2}):
        for c in CONDS:
            f = next(x for x in filas2 if x["query_id"] == q and x["condicion"] == c)
            L += [f"### {q} · {c}", ""] + auditoria(f) + [""]
    for f in filas1:
        if f["condicion"] == "Q1" and f["top"]:
            L += [f"### {f['query_id']} · Q1 (baseline)", ""] + auditoria(f) + [""]
    (C.RESULTS / "resumen.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    fig_exp1(filas1)
    fig_exp2(res["exp2"])
    print("->", C.RESULTS / "resumen.md")


if __name__ == "__main__":
    main()
