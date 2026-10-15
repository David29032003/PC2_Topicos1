"""Construye el corpus de la PC2 a partir de los CSV OCDS (2024-2026).

Uso:
    python pc2/src/construir_corpus.py

Cada documento es la ficha de UN proceso de contratación real, escrita como
texto y dividida en passages atómicos (la unidad de los qrels):

    P01 convocatoria   entidad, procedimiento, objeto, fecha y valor referencial
    P02.. ítems        un passage por ítem (descripción, cantidad, valor, estado)
    ..    cronograma   periodos de consultas y de presentación de ofertas
    ..    documentos   títulos de los documentos publicados (bases, actas...)
    ..    postores     número de postores y nombres
    ..    resultado    buena pro: ganador, monto y % del valor referencial
    ..    contrato     contratos firmados, monto y estado

Los procesos se eligieron para que el corpus contenga las cuatro señales de la
rúbrica de la PC1 y procesos con un solo postor. Si un proceso tiene muchos
ítems, se incluye el ítem objetivo y los siguientes por orden de id hasta
MAX_ITEMS (regla fija, registrada en data/README.md).

Salida: pc2/data/corpus.jsonl
"""
from __future__ import annotations

import json
import sys

import pandas as pd

import config_pc2 as C

sys.stdout.reconfigure(encoding="utf-8")

from construir_casos import dinero, limpiar  # noqa: E402  (código de la PC1)
from ocds import ficha_proceso, tabla  # noqa: E402

P = "ocds-dgv273-seacev3-"
MAX_ITEMS = 8
NOMBRES_POSTORES = 5
MAX_CONTRATOS = 3
MAX_ADJUDICACIONES = 4
# (doc_id, ocid, ítem objetivo, por qué está en el corpus)
PROCESOS = [
    ("D01", P + "1216035", None, "Marca sin equivalente (Cisco); 28 postores. Caso C01 de la PC1."),
    ("D02", P + "1184513", 21194858, "Marca y código de catálogo (Agilent) dentro de una compra de 104 ítems de laboratorio."),
    ("D03", P + "1095541", None, "Marca con 'o equivalente' (Oracle); un solo postor. Caso C05."),
    ("D04", P + "2024-1945-10", None, "Marca con 'o equivalente' (IBM Power); 9 postores."),
    ("D05", P + "1183945", None, "Reactivos para equipo propio Mindray; un solo postor. Caso C06."),
    ("D06", P + "1209013", None, "Tintas para impresora Epson existente; 23 postores. Caso C07."),
    ("D07", P + "1183834", None, "Alimentos sin marca (Vaso de Leche); un solo postor. Caso C09."),
    ("D08", P + "1042389", 20782034, "Dispositivos médicos genéricos; 36 postores; 27 ítems."),
    ("D09", P + "1178657", None, "Trampa léxica: 'ladrillo ADOBE' no es la marca de software."),
    ("D10", P + "2024-48-3", None, "Combustible sin marca; 11 postores."),
]
CATEGORIA = {"goods": "bienes", "services": "servicios", "works": "obras"}


def fecha(x) -> str:
    return str(x)[:10] if pd.notna(x) else "sin fecha"


def frase(texto) -> str:
    """Texto OCDS sin punto final (el punto lo pone la plantilla)."""
    return limpiar(texto).rstrip(". ")


def numero(x) -> str:
    x = float(x)
    return str(int(x)) if x.is_integer() else f"{x:g}"


def elegir_items(items: list[dict], objetivo) -> list[dict]:
    items = sorted(items, key=lambda it: it["id"])
    if objetivo is None or len(items) <= MAX_ITEMS:
        return items[:MAX_ITEMS]
    i = next(k for k, it in enumerate(items) if it["id"] == objetivo)
    elegidos = items[i:i + MAX_ITEMS]
    return elegidos + items[:MAX_ITEMS - len(elegidos)]


def passages_de(doc_id: str, ocid: str, objetivo) -> tuple[dict, list[dict]]:
    f = ficha_proceso(ocid)
    textos = []
    textos.append(("convocatoria",
                   f"Convocatoria {f['nomenclatura']}. {f['entidad']} convocó este proceso por "
                   f"{f['procedimiento']} ({CATEGORIA.get(f['categoria'], f['categoria'])}) el "
                   f"{fecha(f['fecha_convocatoria'])}. Objeto de la contratación: {frase(f['objeto'])}. "
                   f"Valor referencial total: {dinero(f['valor_referencial_pen'])}."))
    items = elegir_items(f["items"], objetivo)
    for k, it in enumerate(items, 1):
        textos.append(("item",
                       f"Ítem {k}: {frase(it['description'])}. Cantidad: {numero(it['quantity'])} "
                       f"{str(it['unit_name']).lower()}. Valor referencial del ítem: "
                       f"{dinero(it['totalValue_amount'], it['totalValue_currency'])}. "
                       f"Estado del ítem: {str(it['statusDetails']).lower()}."))
    m = tabla("main", f["anio_archivo"]).set_index("ocid").loc[ocid]
    periodos = []
    for nombre, campo in (("consultas y observaciones", "enquiryPeriod"), ("presentación de ofertas", "tenderPeriod")):
        ini, fin = m[f"tender_{campo}_startDate"], m[f"tender_{campo}_endDate"]
        if pd.notna(ini) and pd.notna(fin):
            periodos.append(f"{nombre} del {fecha(ini)} al {fecha(fin)}")
    textos.append(("cronograma", "Cronograma: " + ("; ".join(periodos) if periodos
                                                    else "sin fechas registradas en OCDS") + "."))
    titulos = list(dict.fromkeys(d["title"] for d in f["bases_y_documentos"] if pd.notna(d["title"])))
    if titulos:
        textos.append(("documentos", "Documentos publicados en el SEACE: " + "; ".join(titulos) + "."))
    nombres = list(dict.fromkeys(frase(p["name"]) for p in f["postores"]))
    n = int(f["n_postores_ocds"]) if pd.notna(f["n_postores_ocds"]) else len(nombres)
    resto = f" y {len(nombres) - NOMBRES_POSTORES} más" if len(nombres) > NOMBRES_POSTORES else ""
    textos.append(("postores", f"Número de postores registrados: {n}. Postores: "
                               f"{', '.join(nombres[:NOMBRES_POSTORES])}{resto}."))
    if f["adjudicaciones"]:
        partes = []
        for a in f["adjudicaciones"][:MAX_ADJUDICACIONES]:
            partes.append(f"{frase(a['name'])} por {dinero(a['value_amount'], a['value_currency'])} "
                          f"(fecha {fecha(a['date'])})")
        if len(f["adjudicaciones"]) > MAX_ADJUDICACIONES:
            partes.append(f"y {len(f['adjudicaciones']) - MAX_ADJUDICACIONES} adjudicaciones más")
        # El % solo se informa con una sola adjudicación: con varias, las
        # adjudicaciones pueden venir de convocatorias previas del mismo proceso.
        a0, ref = f["adjudicaciones"][0], f["valor_referencial_pen"]
        pct = (f" El monto adjudicado equivale al {a0['value_amount'] / ref:.0%} del valor referencial."
               if len(f["adjudicaciones"]) == 1 and ref and a0["value_currency"] == "PEN" else "")
        textos.append(("resultado", "Buena pro otorgada a " + "; ".join(partes) + "." + pct))
    else:
        textos.append(("resultado", "Buena pro: no hay adjudicación registrada en OCDS para este proceso."))
    if f["contratos"]:
        partes = []
        for c in f["contratos"][:MAX_CONTRATOS]:
            estado = f" (estado: {str(c['statusDetails']).lower()})" if pd.notna(c["statusDetails"]) else ""
            partes.append(f"firmado el {fecha(c['dateSigned'])} por "
                          f"{dinero(c['value_amount'], c['value_currency'])}{estado}")
        resto = len(f["contratos"]) - MAX_CONTRATOS
        textos.append(("contrato", f"Contratos registrados: {len(f['contratos'])}. " + "; ".join(partes)
                       + (f"; y {resto} más" if resto > 0 else "") + "."))
    else:
        textos.append(("contrato", "Contratos registrados: ninguno en OCDS para este proceso."))

    passages = [{"passage_id": f"{doc_id}-P{i:02d}", "tipo": tipo, "text": t}
                for i, (tipo, t) in enumerate(textos, 1)]
    meta = {"doc_id": doc_id, "ocid": ocid, "anio_archivo": f["anio_archivo"],
            "title": f"{f['nomenclatura']} - {limpiar(f['objeto'])[:90]}", "entidad": f["entidad"],
            "n_items_proceso": len(f["items"]), "n_items_incluidos": len(items),
            "fuente": f"OCDS SEACE, {f['anio_archivo']}/ (main, tender_items, tender_documents, "
                      f"tender_tenderers, awards, awards_suppliers)"}
    return meta, passages


def main():
    C.DATA.mkdir(parents=True, exist_ok=True)
    docs = []
    for doc_id, ocid, objetivo, motivo in PROCESOS:
        meta, passages = passages_de(doc_id, ocid, objetivo)
        docs.append({**meta, "motivo": motivo, "passages": passages})
        palabras = sum(len(p["text"].split()) for p in passages)
        print(f"{doc_id} {ocid[-16:]:>16} passages={len(passages):2d} palabras={palabras:4d} | {meta['title'][:70]}")
    with C.CORPUS_PATH.open("w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    n = sum(len(d["passages"]) for d in docs)
    print(f"\n{len(docs)} documentos, {n} passages -> {C.CORPUS_PATH}")


if __name__ == "__main__":
    main()
