"""Diapositivas de la PC2 (portada + 5 de contenido) a partir de pc2/results/.

Uso:
    python pc2/slides/construir_slides.py            # PC2.pptx + PC2.pdf (+ PNG de control en slides/_png)

El PDF se exporta con PowerPoint (COM). Si PowerPoint ya tiene otras
presentaciones abiertas, no se cierra.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_TICK_LABEL_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
PC2 = AQUI.parent
RES = PC2 / "results"

NAVY = "0F2A4A"
AZUL = "2A78D6"
NARANJA = "EB6834"
TINTE = "EEF4FC"
TINTE_N = "FDF0EA"
TINTA = "1B1B1B"
TINTA_2 = "52514E"
MUDA = "898781"
BLANCO = "FFFFFF"
FUENTE = "Calibri"


def rgb(h: str) -> RGBColor:
    return RGBColor.from_string(h)


def num(x: float, d: int = 2) -> str:
    if d == 0:
        return str(int(round(x)))
    if x in (0, 1):
        return str(int(x))
    s = f"{x:.{d}f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def texto(slide, x, y, w, h, contenido, size=16, color=TINTA, bold=False, align=PP_ALIGN.LEFT,
          anchor=MSO_ANCHOR.TOP, italic=False, nombre=None):
    """contenido: str o lista de párrafos; cada párrafo es str o lista de (texto, {opciones})."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if nombre:
        tb.name = nombre
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, 0)
    parrafos = contenido if isinstance(contenido, list) else [contenido]
    for i, par in enumerate(parrafos):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        runs = par if isinstance(par, list) else [(par, {})]
        for t, o in runs:
            r = p.add_run()
            r.text = t
            f = r.font
            f.name = o.get("font", FUENTE)
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.italic = o.get("italic", italic)
            f.color.rgb = rgb(o.get("color", color))
        if isinstance(par, list) and par and par[0][1].get("space_after") is not None:
            p.space_after = Pt(par[0][1]["space_after"])
        else:
            p.space_after = Pt(6)
    return tb


def caja(slide, x, y, w, h, fill, radio=0.06, linea=None, nombre=None):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.adjustments[0] = radio
    s.fill.solid()
    s.fill.fore_color.rgb = rgb(fill)
    if linea:
        s.line.color.rgb = rgb(linea)
        s.line.width = Pt(1)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    if nombre:
        s.name = nombre
    return s


def circulo(slide, x, y, d, fill, etiqueta, color=BLANCO, size=14):
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
    s.fill.solid()
    s.fill.fore_color.rgb = rgb(fill)
    s.line.fill.background()
    s.shadow.inherit = False
    tf = s.text_frame
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, 0)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = etiqueta
    r.font.size, r.font.bold, r.font.name = Pt(size), True, FUENTE
    r.font.color.rgb = rgb(color)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    return s


def flecha(slide, x1, y1, x2, y2, color=MUDA):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(1.75)
    ln = c.line._get_or_add_ln()
    from lxml import etree
    tail = etree.SubElement(ln, "{http://schemas.openxmlformats.org/drawingml/2006/main}tailEnd")
    tail.set("type", "triangle")
    return c


def fondo(slide, color):
    f = slide.background.fill
    f.solid()
    f.fore_color.rgb = rgb(color)


def titulo(slide, t, sub=None):
    texto(slide, 0.6, 0.45, 12.1, 0.75, t, size=32, bold=True, color=NAVY, nombre="Título")
    if sub:
        texto(slide, 0.6, 1.18, 12.1, 0.45, sub, size=16, color=TINTA_2, nombre="Subtítulo")


def tabla(slide, x, y, w, filas, anchos, alto_fila=0.36, size=12, cabecera=AZUL):
    shp = slide.shapes.add_table(len(filas), len(filas[0]), Inches(x), Inches(y), Inches(w),
                                 Inches(alto_fila * len(filas)))
    t = shp.table
    for j, a in enumerate(anchos):
        t.columns[j].width = Inches(a)
    for i, fila in enumerate(filas):
        t.rows[i].height = Inches(alto_fila)
        for j, v in enumerate(fila):
            c = t.cell(i, j)
            c.margin_left = c.margin_right = Inches(0.08)
            c.margin_top = c.margin_bottom = Inches(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid()
            c.fill.fore_color.rgb = rgb(cabecera if i == 0 else (TINTE if i % 2 == 0 else BLANCO))
            tf = c.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            r = p.add_run()
            negrita = i == 0 or (isinstance(v, tuple) and v[1])
            r.text = v[0] if isinstance(v, tuple) else str(v)
            r.font.size, r.font.name, r.font.bold = Pt(size), FUENTE, negrita
            r.font.color.rgb = rgb(BLANCO if i == 0 else TINTA)
    return shp


def notas(slide, t):
    slide.notes_slide.notes_text_frame.text = t


# ------------------------------------------------------------------ diapositivas

def s_portada(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    fondo(s, NAVY)
    texto(s, 0.8, 1.55, 11.7, 0.9, "PC2 - Tópicos de Ciencia de la Computación 1", size=40, bold=True, color=BLANCO)
    texto(s, 0.8, 2.55, 11.7, 1.0, "De una consulta estructurada a recuperación densa verificable sobre fichas OCDS "
                                   "de contrataciones públicas", size=22, color="CADCFC")
    pasos = ["Necesidad", "JSON validado", "e5 + FAISS", "Recall@k"]
    for i, p in enumerate(pasos):
        x = 0.8 + i * 2.95
        caja(s, x, 4.35, 2.6, 0.75, "1C3D66", radio=0.5)
        circulo(s, x + 0.14, 4.48, 0.5, NARANJA if i == 3 else AZUL, str(i + 1), size=14)
        texto(s, x + 0.78, 4.35, 1.75, 0.75, p, size=16, color=BLANCO, anchor=MSO_ANCHOR.MIDDLE)
    texto(s, 0.8, 5.75, 11.7, 0.5, "Tema: sistema multi-agente LLM para detectar requisitos direccionados en "
                                   "bases de contrataciones del Estado (continuación de la PC1)", size=14, color="CADCFC")
    notas(s, "Continúo el tema de la PC1. En la PC1 el contexto se le daba al modelo a mano; aquí pregunto cómo "
             "recuperarlo automáticamente: necesidad, consulta estructurada, embeddings, FAISS y Recall@k.")


def s_problema(prs, nec, qrels):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    fondo(s, BLANCO)
    titulo(s, "Problema y necesidad de recuperación",
           "Antes de decidir si un requisito está direccionado, el sistema necesita encontrar la evidencia en la ficha")
    # Izquierda: el corpus
    caja(s, 0.6, 1.95, 4.3, 4.95, TINTE)
    texto(s, 0.9, 2.15, 3.8, 0.4, "Corpus", size=20, bold=True, color=NAVY)
    texto(s, 0.9, 2.65, 3.8, 3.1, [
        [("10 fichas reales ", {"bold": True}), ("del SEACE (OCDS 2026, convocatorias 2024-2026)", {})],
        [("92 passages: ", {"bold": True}), ("convocatoria, ítems, cronograma, documentos, postores, buena pro y contrato", {})],
        [("Cubre las 4 señales ", {"bold": True}), ("de la rúbrica de la PC1, 3 procesos con un solo postor y una trampa léxica (ladrillo ADOBE)", {})],
    ], size=15, color=TINTA)
    texto(s, 0.9, 5.95, 3.8, 0.8, "Qrels sobre passage_id: no cambian cuando cambia el tamaño del chunk",
          size=13, italic=True, color=TINTA_2)
    # Derecha: necesidades
    texto(s, 5.3, 1.95, 7.4, 0.4, "5 necesidades de información (Q0) y su evidencia", size=20, bold=True, color=NAVY)
    cortas = {"N1": ("Marca o código sin \"o equivalente\"", "Cisco, Agilent"),
              "N2": ("Marca que sí acepta \"o equivalente\"", "Oracle, IBM Power"),
              "N3": ("Insumos para un equipo que ya tiene la entidad", "Mindray, Epson"),
              "N4": ("Procesos con un solo postor", "3 passages de postores"),
              "N5": ("Ganador y monto de los reactivos Mindray", "1 passage de buena pro")}
    for i, n in enumerate(nec):
        y = 2.5 + i * 0.86
        caja(s, 5.3, y, 7.4, 0.74, BLANCO, linea="D5E3F5")
        circulo(s, 5.45, y + 0.12, 0.5, NARANJA if n["query_id"] in ("N2", "N5") else AZUL, n["query_id"], size=12)
        a, b = cortas[n["query_id"]]
        texto(s, 6.15, y + 0.08, 4.4, 0.6, a, size=15, bold=True, color=TINTA, anchor=MSO_ANCHOR.MIDDLE)
        texto(s, 10.55, y + 0.08, 2.05, 0.6, f"{b}\n|G| = {len(qrels[n['query_id']])}", size=12, color=TINTA_2,
              anchor=MSO_ANCHOR.MIDDLE)
    notas(s, "El corpus son fichas reales armadas desde las tablas OCDS: no hay texto inventado. Las cinco necesidades "
             "son la evidencia que el detector necesitaría. La relevancia se define sobre passages, por eso los qrels "
             "no cambian al cambiar el tamaño del chunk. |G| es el número de passages relevantes de cada necesidad.")


def s_pipeline(prs, res):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    fondo(s, BLANCO)
    titulo(s, "Pipeline: consulta estructurada → embeddings → FAISS",
           "Cada etapa es una pieza distinta: encoder ≠ índice ≠ almacén ≠ recuperador")
    etapas = [("Necesidad", "texto del auditor (Q0)", AZUL),
              ("Qwen2.5-0.5B", "greedy · prompt con\nTAREA / NECESIDAD / CONTEXTO", AZUL),
              ("JSON Schema", "parseable → cumple el\nschema → intención", NARANJA),
              ("e5-small", "\"query: …\" / \"passage: …\"\n384 dim · L2 · minúsculas", AZUL),
              ("IndexFlatIP", "producto interno exacto\n= coseno (vectores L2)", AZUL),
              ("top-k → Recall@k", "k = 1, 3, 5 sobre los\npassages relevantes", NARANJA)]
    w, gap, y = 1.85, 0.21, 2.05
    for i, (a, b, col) in enumerate(etapas):
        x = 0.6 + i * (w + gap)
        caja(s, x, y, w, 1.75, TINTE if col == AZUL else TINTE_N)
        circulo(s, x + 0.15, y + 0.15, 0.42, col, str(i + 1), size=12)
        texto(s, x + 0.15, y + 0.68, w - 0.3, 0.38, a, size=15, bold=True, color=NAVY)
        texto(s, x + 0.15, y + 1.04, w - 0.25, 0.7, b, size=11, color=TINTA_2)
        if i < len(etapas) - 1:
            flecha(s, x + w + 0.02, y + 0.87, x + w + gap - 0.02, y + 0.87)
    # JSON de ejemplo
    caja(s, 0.6, 4.2, 5.7, 2.65, "F6F7F9", linea="E1E0D9")
    texto(s, 0.85, 4.35, 5.3, 0.35, "Salida del LLM validada (N4)", size=14, bold=True, color=NAVY)
    texto(s, 0.85, 4.8, 5.3, 1.9, ['{"query": "¿En qué procesos se presentó',
                                    '           un solo postor?",',
                                    ' "intent": "competencia",',
                                    ' "abstain": false}'], size=13, color=TINTA, )
    for p in s.shapes[-1].text_frame.paragraphs:
        for r in p.runs:
            r.font.name = "Courier New"
        p.space_after = Pt(0)
    texto(s, 0.85, 6.1, 5.3, 0.6, "parseable ✓ · schema-valid ✓ · intención correcta ✓\n"
                                  "al encoder: \"query: ¿en qué procesos se presentó un solo postor?\"",
          size=12, color=TINTA_2)
    # Segmentación
    ch = res["chunks"]
    filas = [["Chunk", "target_words", "chunks", "palabras media", "tokens máx."]]
    for c in ("small", "baseline", "large"):
        filas.append([c, str(ch[c]["target_words"]), str(ch[c]["n_chunks"]), num(ch[c]["palabras_media"], 0),
                      str(ch[c]["tokens_max"])])
    tabla(s, 6.7, 4.2, 6.0, filas, [1.3, 1.25, 0.95, 1.35, 1.15], alto_fila=0.4, size=13)
    texto(s, 6.7, 5.9, 6.0, 0.95, [
        [("Sin truncación: ", {"bold": True}), ("el texto SEACE ocupa ~2 tokens por palabra; el chunker se cierra "
                                                "antes de 512 tokens (3 de 13 chunks de la condición large).", {})]],
          size=13, color=TINTA_2)
    notas(s, "Con vectores normalizados, el producto interno es el coseno, así que IndexFlatIP ordena por coseno y es "
             "búsqueda exacta. Verifiqué que FAISS y la multiplicación Q por E transpuesta en NumPy dan el mismo orden. "
             "Paso el texto a minúsculas porque el SEACE escribe en mayúsculas y eso multiplica los tokens. Con 320 "
             "palabras se superaba la ventana de 512 tokens, así que el chunker se detiene antes: así no mezclo tamaño "
             "con truncación.")


def s_experimentos(prs, res):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    fondo(s, BLANCO)
    titulo(s, "Dos experimentos, una variable a la vez", "La métrica principal de la discusión es mean Recall@3")
    cols = [("Exp. 1 · Consulta", "basado en prompts", AZUL,
             [("Compara", "Q0 = necesidad original  vs  Q1 = campo query del JSON del LLM"),
              ("Fijos", "corpus · chunk 180 palabras · overlap 1 · e5-small · L2 · IndexFlatIP · k"),
              ("Mide", "schema_valid_rate, intención correcta y Recall@1/3/5 de Q0 vs Q1"),
              ("Hipótesis", "la consulta estructurada conserva la necesidad; no se exige que la mejore")]),
            ("Exp. 2 · Tamaño del chunk", "sin prompts", NARANJA,
             [("Compara", "small = 100 · baseline = 180 · large = 320 palabras"),
              ("Fijos", "corpus · consultas Q0 · qrels · overlap 1 · e5-small · L2 · producto interno · IndexFlatIP · k"),
              ("Mide", "Recall@1, Recall@3 (principal) y Recall@5, y el cambio por necesidad"),
              ("Hipótesis", "el chunk pequeño aísla un ítem, pero puede separar la evidencia de lo que la identifica")])]
    for i, (t, sub, col, filas) in enumerate(cols):
        x = 0.6 + i * 6.25
        caja(s, x, 1.95, 5.85, 4.9, TINTE if col == AZUL else TINTE_N)
        circulo(s, x + 0.3, 2.2, 0.55, col, str(i + 1), size=16)
        texto(s, x + 1.05, 2.18, 4.6, 0.4, t, size=20, bold=True, color=NAVY)
        texto(s, x + 1.05, 2.58, 4.6, 0.3, sub, size=13, italic=True, color=TINTA_2)
        for j, (k, v) in enumerate(filas):
            y = 3.25 + j * 0.88
            texto(s, x + 0.35, y, 1.25, 0.8, k, size=14, bold=True, color=col)
            texto(s, x + 1.6, y, 4.0, 0.85, v, size=14, color=TINTA)
    notas(s, "En el experimento 1 solo cambia la consulta; en el 2 solo cambia el tamaño del chunk. Todo lo demás "
             "queda fijo, incluido el chunker con un passage de solapamiento y el tope de 512 tokens.")


def s_resultados(prs, res, filas2):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    fondo(s, BLANCO)
    e2 = res["exp2"]
    titulo(s, "Resultados y error de recuperación",
           f"Con chunks de 180 palabras se recupera más evidencia; Q1 recupera lo mismo que Q0 "
           f"(mean R@3 = {num(res['exp1']['Q0']['Recall@3'])} en ambas)")
    # Gráfico nativo: Recall@k por condición
    cd = CategoryChartData()
    cd.categories = ["Recall@1", "Recall@3", "Recall@5"]
    conds = [("small", "small · 100"), ("baseline", "baseline · 180"), ("large", "large · 320")]
    for c, nombre in conds:
        cd.add_series(nombre, [e2[c][f"Recall@{k}"] for k in (1, 3, 5)])
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(1.85), Inches(6.2), Inches(3.45), cd)
    ch = gf.chart
    ch.has_legend = True
    ch.legend.position = XL_LEGEND_POSITION.TOP
    ch.legend.include_in_layout = False
    ch.legend.font.size, ch.legend.font.name = Pt(12), FUENTE
    ch.legend.font.color.rgb = rgb(TINTA_2)
    va = ch.value_axis
    va.maximum_scale, va.minimum_scale = 1.0, 0
    va.tick_label_position = XL_TICK_LABEL_POSITION.NONE
    va.format.line.fill.background()
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = rgb("E1E0D9")
    ca = ch.category_axis
    ca.tick_labels.font.size, ca.tick_labels.font.name = Pt(12), FUENTE
    ca.tick_labels.font.color.rgb = rgb(TINTA_2)
    ca.format.line.color.rgb = rgb("C3C2B7")
    colores = ["86B6EF", AZUL, "104281"]
    plot = ch.plots[0]
    plot.gap_width, plot.overlap = 70, 0
    for serie, col, (c, _) in zip(plot.series, colores, conds):
        serie.format.fill.solid()
        serie.format.fill.fore_color.rgb = rgb(col)
        for k, punto in zip((1, 3, 5), serie.points):
            dl = punto.data_label
            dl.has_text_frame = True
            dl.text_frame.text = num(e2[c][f"Recall@{k}"])
            dl.text_frame.paragraphs[0].runs[0].font.size = Pt(11)
            dl.text_frame.paragraphs[0].runs[0].font.color.rgb = rgb(TINTA_2)
            from pptx.enum.chart import XL_LABEL_POSITION
            dl.position = XL_LABEL_POSITION.OUTSIDE_END
    # Tabla por necesidad
    filas = [["R@3", "small", "base", "large"]]
    for q in ("N1", "N2", "N3", "N4", "N5"):
        v = [next(f["recall@3"] for f in filas2 if f["query_id"] == q and f["condicion"] == c) for c, _ in conds]
        filas.append([(q, q in ("N2", "N5"))] + [num(x) for x in v])
    tabla(s, 0.6, 5.45, 6.2, filas, [1.55, 1.55, 1.55, 1.55], alto_fila=0.24, size=11)
    # Derecha: casos
    caja(s, 7.2, 1.95, 5.5, 2.35, TINTE)
    texto(s, 7.45, 2.1, 5.0, 0.4, "N5 · el tamaño del chunk ayuda", size=17, bold=True, color=NAVY)
    texto(s, 7.45, 2.55, 5.05, 1.7, [
        "Con 100 palabras el top-1 es la ficha correcta (D05, 0,891), pero el chunk tiene convocatoria + ítem: "
        "la buena pro quedó en otro chunk → R@3 = 0.",
        "Con 180 la ficha entera cabe en un chunk → R@1 = 1. Documento ≠ fragmento."], size=13, color=TINTA)
    caja(s, 7.2, 4.5, 5.5, 2.35, TINTE_N)
    texto(s, 7.45, 4.65, 5.0, 0.4, "N2 · error con cualquier tamaño", size=17, bold=True, color=NAVY)
    texto(s, 7.45, 5.1, 5.05, 1.7, [
        "La evidencia es una frase corta (\"o equivalente\") dentro de chunks de ~150 palabras: el embedding la diluye.",
        "Top-10 entre 0,851 y 0,838; el chunk relevante de D04 queda 8.º (0,840). Pide señal léxica: BM25 / híbrido."],
          size=13, color=TINTA)
    notas(s, "Recall@3 medio: small 0,20, baseline 0,47, large 0,40. El caso N5 explica casi toda la diferencia de "
             "small: encuentra el documento pero no el fragmento de la buena pro. N2 es el error que no depende del "
             "tamaño: la evidencia es léxica y el modelo denso pone a todos los chunks del dominio en el mismo rango "
             "de score. En el experimento 1 el LLM copió la necesidad en 4 de 5 casos y eligió mal la intención en 2: "
             "el JSON fue schema-valid en 5 de 5, pero no siempre adecuado.")


def s_conclusion(prs, res):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    fondo(s, NAVY)
    texto(s, 0.6, 0.45, 12.1, 0.75, "Limitación y conclusión", size=32, bold=True, color=BLANCO)
    texto(s, 0.6, 1.2, 12.1, 0.45, "Bajo este corpus, estas 5 necesidades, estos qrels y e5-small con IndexFlatIP",
          size=16, color="CADCFC")
    e1 = res["exp1"]
    n1 = e1["n_necesidades"]
    stats = [(f"{round(e1['schema_valid_rate'] * n1)}/{n1}", "salidas de Q1 schema-valid,\npero intención correcta 3/5"),
             ("0,20 → 0,47", "mean Recall@3 al pasar\nde 100 a 180 palabras"),
             ("0", "Recall@3 de N2 con los\ntres tamaños de chunk")]
    for i, (v, et) in enumerate(stats):
        x = 0.6 + i * 4.15
        caja(s, x, 1.95, 3.85, 2.05, "1C3D66")
        texto(s, x + 0.3, 2.1, 3.3, 0.9, v, size=40, bold=True, color=NARANJA if i == 2 else BLANCO)
        texto(s, x + 0.3, 3.05, 3.3, 0.85, et, size=14, color="CADCFC")
    texto(s, 0.6, 4.35, 6.0, 0.4, "Conclusión", size=20, bold=True, color=BLANCO)
    texto(s, 0.6, 4.8, 6.0, 2.1, [
        "El LLM conserva la necesidad (casi la copia) y no mejora la recuperación; el JSON válido no garantiza la "
        "intención correcta.",
        "El tamaño del chunk importa cuando la evidencia y lo que la identifica están en passages distintos."],
          size=14, color=BLANCO)
    texto(s, 6.9, 4.35, 5.8, 0.4, "Limitación", size=20, bold=True, color=BLANCO)
    texto(s, 6.9, 4.8, 5.8, 2.1, [
        "5 necesidades y 10 fichas: un passage mueve el Recall medio entre 0,05 y 0,1. Qrels de un solo anotador.",
        "\"large\" quedó limitado por la ventana de 512 tokens (máx. real 257 palabras). No se generaliza un tamaño "
        "de chunk óptimo."], size=14, color=BLANCO)
    notas(s, "No afirmo que 180 palabras sea el mejor tamaño en general ni que el LLM nunca mejore la consulta: con "
             "estos datos, la recuperación densa sola encuentra el documento correcto más a menudo que la evidencia "
             "exacta. El paso natural es la Semana 5: BM25 y fusión para las señales léxicas como 'o equivalente'.")


def exportar(pptx: Path, pdf: Path, carpeta_png: Path):
    carpeta_png.mkdir(parents=True, exist_ok=True)
    ps = f"""
$app = New-Object -ComObject PowerPoint.Application
$abiertas = $app.Presentations.Count
$p = $app.Presentations.Open('{pptx}', $true, $false, $false)
$p.SaveAs('{pdf}', 32)
$i = 1
foreach ($s in $p.Slides) {{ $s.Export('{carpeta_png}\\slide{{0}}.png' -f $i, 'PNG', 1600, 900); $i++ }}
$p.Close()
if ($abiertas -eq 0) {{ $app.Quit() }}
"""
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)


def main():
    res = json.loads((RES / "resumen.json").read_text(encoding="utf-8"))
    nec = [json.loads(l) for l in (PC2 / "data" / "necesidades.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    qrels = json.loads((PC2 / "data" / "qrels.json").read_text(encoding="utf-8"))
    filas2 = [json.loads(l) for l in (RES / "exp2_chunking.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    s_portada(prs)
    s_problema(prs, nec, qrels)
    s_pipeline(prs, res)
    s_experimentos(prs, res)
    s_resultados(prs, res, filas2)
    s_conclusion(prs, res)
    salida = AQUI / "PC2.pptx"
    prs.save(salida)
    print("PPTX:", salida, "| diapositivas:", len(prs.slides))
    exportar(salida, AQUI / "PC2.pdf", AQUI / "_png")
    print("PDF:", AQUI / "PC2.pdf")


if __name__ == "__main__":
    main()
