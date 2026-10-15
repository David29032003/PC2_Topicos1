# PC2 · De una consulta estructurada a recuperación densa verificable

**CC0F4 Tópicos de Ciencia de la Computación I · 2026-2 · Segunda Práctica Calificada**
**Autores:** David Fernando Reeves Goñi y Luis Azaña Vega
**Tema (el mismo de la PC1):** Sistema multi-agente LLM para la detección de requisitos direccionados en bases de contrataciones del Estado usando registros OCDS.

Esta carpeta continúa el repositorio de la PC1 y reutiliza su lectura de los CSV OCDS (`../src/ocds.py`), su LLM local (`../src/llm.py`) y su parseo JSON en dos niveles (`../src/validacion.py`).

```text
necesidad de información -> LLM -> consulta estructurada -> JSON Schema
  -> "query: ..." -> multilingual-e5-small -> FAISS IndexFlatIP -> top-k -> Recall@k
```

La salida recuperada **no** se usa todavía para generar una respuesta con el LLM (no es RAG).

## Cómo ejecutar

Desde la raíz del repositorio de la PC1 y con el entorno del curso (`requirements.txt` ya incluye `sentence-transformers` y `faiss-cpu`):

```bash
python pc2/src/construir_corpus.py   # solo si tienes los CSV OCDS (corpus.jsonl ya está versionado)
python pc2/src/experimentos.py       # Exp. 1 y Exp. 2 -> pc2/results/*.jsonl, resumen.json
python pc2/src/reporte.py            # tablas, auditoría y figuras -> pc2/results/resumen.md, figs/
python pc2/src/demo.py N5            # demostración de 2 minutos (también acepta texto libre)
```

La primera ejecución descarga `intfloat/multilingual-e5-small` (~470 MB, revisión fijada en `pc2/src/config_pc2.py`). Después corre sin conexión con `HF_HUB_OFFLINE=1`.

```text
pc2/
├── README.md
├── src/       config_pc2, construir_corpus, recuperador, consulta_llm, experimentos, reporte, demo
├── data/      corpus.jsonl, necesidades.jsonl, qrels.json, README.md (procedencia)
├── prompts/   system_consulta.txt, Q1_consulta.txt
├── schema/    consulta.schema.json
├── results/   exp1_consulta.jsonl, exp2_chunking.jsonl, chunks_*.jsonl, resumen.json/.md, figs/
└── slides/    construir_slides.py, PC2.pptx, PC2.pdf
```

## 1. Problema de recuperación

Antes de decidir si un requerimiento está direccionado, el sistema necesita **ver la evidencia**: el texto del ítem con la marca, si admite "o equivalente", si es para un equipo que la entidad ya tiene, cuántos postores hubo y quién ganó. En la PC1 esa evidencia se entregaba a mano en el prompt. Aquí la pregunta es:

> Dada una necesidad de información de un auditor, ¿el recuperador denso encuentra los fragmentos de las fichas OCDS donde está la evidencia?

## 2. Corpus y consultas

- **Corpus:** 10 fichas de procesos reales del SEACE (archivo OCDS 2026, convocatorias 2024-2026), 92 passages, de 134 a 390 palabras por documento. Cada ficha tiene passages de convocatoria, ítems, cronograma, documentos, postores, resultado y contrato. La procedencia completa, ocid por ocid, está en [`data/README.md`](data/README.md).
- **Selección:** los documentos cubren las cuatro señales de la rúbrica de la PC1 (marca sin equivalente, marca con equivalente, equipo existente, sin marca). Tres procesos tienen un solo postor, y se incluye una trampa léxica ("ladrillo ADOBE").
- **Consultas (5 necesidades) y qrels:**

| Id | Necesidad (Q0, tal como la escribió el autor) | Intención esperada | Passages relevantes |
|---|---|---|---|
| N1 | ¿En qué compras se exige una marca o un código de fabricante específico sin aceptar productos equivalentes? | marca_sin_equivalente | D01-P02, D02-P02 |
| N2 | Quiero encontrar los requerimientos que mencionan una marca pero permiten ofertar un producto equivalente. | marca_con_equivalente | D03-P01/P02, D04-P01/P02 |
| N3 | ¿Qué compras son de insumos o repuestos para un equipo que la entidad ya tiene? | compatibilidad_equipo_existente | D05-P01/P02, D06-P01/P02 |
| N4 | ¿En qué procesos se presentó un solo postor? | competencia | D03-P05, D05-P05, D07-P06 |
| N5 | ¿Qué empresa ganó la compra de reactivos para el equipo Mindray del hospital de Jaén y por cuánto? | resultado_adjudicacion | D05-P06 |

Los qrels se definen sobre **passages**, no sobre chunks, para que sigan siendo los mismos cuando cambia el tamaño del chunk. Un passage es relevante si contiene la evidencia literal que pide la necesidad.

## 3. Consulta estructurada y JSON Schema

El LLM es el mismo de la PC1: `Qwen/Qwen2.5-0.5B-Instruct`, revisión fijada, greedy, CPU. El prompt (`prompts/Q1_consulta.txt`) separa **TAREA**, **NECESIDAD** (entrada), **CONTEXTO** (qué contiene una ficha) e **INTENCIONES** posibles, y fija el contrato de salida:

```json
{"query": "<consulta de 4 a 25 palabras>", "intent": "marca_sin_equivalente | ... | otro", "abstain": false}
```

`schema/consulta.schema.json` (Draft 2020-12) exige las tres claves, `intent` dentro del enum, `abstain` booleano y nada más. La validación tiene tres niveles, como en la Semana 3:

1. **parseable:** JSON exacto o recuperable (primer objeto `{...}` dentro del texto);
2. **schema-valid:** cumple el schema;
3. **adecuada:** intención igual a la esperada, sin abstención y `query` de 4 a 25 palabras.

Solo el campo `query` se envía al encoder. Si la salida no es schema-valid o se abstiene, no hay consulta y el Recall se cuenta como 0 (criterio estricto).

## 4. Modelo de embeddings

`intfloat/multilingual-e5-small` (revisión `614241f6…`): encoder multilingüe orientado a recuperación, 384 dimensiones y ventana de 512 tokens. Se respetan sus prefijos de tarea, `query: ` para la consulta y `passage: ` para el chunk. Los vectores salen **L2-normalizados** (`normalize_embeddings=True`).

Normalización del texto: el SEACE publica casi todo en MAYÚSCULAS, y medido sobre este corpus el tokenizador de e5 produce 2,31 tokens por palabra (1,98 en minúsculas). Por eso passages y consultas se pasan a minúsculas antes de codificar, igual en todas las condiciones.

## 5. Segmentación

`recuperador.construir_chunks` es el chunker del Laboratorio 4: agrupa passages consecutivos de un mismo documento hasta `target_words`, con **1 passage de solapamiento**. Tiene dos protecciones, registradas en cada chunk:

- **Sin truncación:** si `target_words` no cabe en 512 tokens, el chunk se cierra antes (`corte_por_tokens`). Así el experimento no confunde tamaño de chunk con truncación. El encoder además rechaza cualquier entrada de más de 512 tokens.
- **Sin duplicados:** si el passage siguiente no cabe junto al solapamiento, el chunk nuevo repetiría solo el solapamiento. En ese caso empieza sin solapar. `validar_overlap` verifica el solapamiento real.

| Condición | target_words | Chunks | Palabras (media / máx.) | Tokens (media / máx.) | Cortes por tokens | Sin solape |
|---|---:|---:|---|---|---:|---:|
| small | 100 | 36 | 80 / 100 | 162 / 236 | 0 | 1 |
| baseline | 180 | 18 | 137 / 180 | 276 / 365 | 0 | 0 |
| large | 320 | 13 | 179 / 257 | 357 / 502 | 3 | 0 |

## 6. Índice y similitud

`faiss.IndexFlatIP`: búsqueda **exhaustiva** por producto interno, es decir exacta y no aproximada. Con vectores L2-normalizados,

$$\hat q^\top \hat e = \frac{q^\top e}{\lVert q\rVert\,\lVert e\rVert} = \cos(q, e),$$

así que ordenar por producto interno es ordenar por similitud coseno. `experimentos.py` lo verifica: FAISS y la multiplicación `Q·Eᵀ` en NumPy dan el **mismo orden** en las tres condiciones, con una diferencia máxima de score de 2,4·10⁻⁷.

Hay que distinguir cuatro piezas: el **encoder** produce vectores, el **índice** los organiza y los busca, el **almacén** (aquí `chunks_*.jsonl`) guarda ids, metadatos y texto, y el **recuperador** (`recuperador.Recuperador`) es la política completa: chunker, encoder, índice y top-k. Un **documento** (ficha) no es lo mismo que un **fragmento** (chunk): los qrels apuntan a passages, que viven dentro de chunks.

## 7. Experimento 1 · Consulta (basado en prompts)

- **Pregunta:** ¿la consulta que escribe el LLM conserva, mejora o degrada la necesidad original?
- **Comparación:** Q0 (necesidad original) contra Q1 (campo `query` del JSON del LLM).
- **Fijos:** corpus, segmentación baseline (180 palabras, 1 passage de overlap), e5-small, normalización L2, IndexFlatIP, k = 1, 3, 5.

| Métrica de Q1 | Valor |
|---|---|
| JSON exacto | 0/5 (siempre envuelto en ```json … ```) |
| JSON parseable | 5/5 |
| **schema_valid_rate** | **5/5 = 1,0** |
| Intención correcta | 3/5 (N3 → `competencia`, N5 → `marca_con_equivalente`) |
| Abstención | 0/5 |
| Adecuada (3 chequeos) | 3/5 |

| Consulta | Recall@1 | Recall@3 | Recall@5 |
|---|---:|---:|---:|
| Q0 | 0,30 | 0,47 | 0,53 |
| Q1 | 0,30 | 0,47 | 0,53 |

Jaccard medio entre los top-3 de Q0 y Q1: 0,9.

**Caso.** En 4 de 5 necesidades el modelo copió la necesidad **literalmente** como `query`. En N2 la reformuló ("Quiero encontrar los requerimientos que…" → "¿Qué requerimientos mencionan…"), con lo que cambió uno de los tres chunks recuperados (Jaccard 0,5), pero ninguno era relevante en ninguna de las dos versiones.

La transformación **conserva** la necesidad y no la mejora. El modelo no reescribe hacia el vocabulario de las fichas, por ejemplo "o equivalente", "número de postores registrados: 1" o "buena pro".

Además, la salida es **schema-valid pero no siempre adecuada**: en N5 ("¿qué empresa ganó…?") la intención es `marca_con_equivalente`. El schema solo garantiza que el valor está en el enum, no que sea el correcto. Una regla de recuperación que filtrara por `intent` habría buscado en el lugar equivocado. El prompt no se ajustó después de ver estos resultados.

## 8. Experimento 2 · Chunking (sin prompts)

- **Pregunta:** ¿cómo cambia la recuperación al modificar solo el tamaño objetivo del chunk?
- **Hipótesis previa:** el chunk pequeño aísla mejor una evidencia corta (un ítem), pero puede separar la evidencia de la parte de la ficha que la identifica.
- **Variable:** `target_words` = 100 / **180 (baseline)** / 320.
- **Fijos:** corpus, consultas Q0, qrels, overlap = 1 passage, e5-small, normalización (minúsculas + L2), producto interno, IndexFlatIP, k.
- **Métrica principal:** mean Recall@3.

| Condición | Recall@1 | **Recall@3** | Recall@5 |
|---|---:|---:|---:|
| small (100) | 0,00 | 0,20 | 0,30 |
| baseline (180) | 0,30 | **0,47** | 0,53 |
| large (320) | 0,30 | 0,40 | 0,47 |

| Necesidad | R@3 small | R@3 baseline | R@3 large | Qué pasó |
|---|---:|---:|---:|---|
| N1 marca sin equivalente | 0,5 | 0,5 | 0,5 | **No cambia:** encuentra Cisco (D01) pero no Agilent (D02) |
| N2 marca con equivalente | 0 | 0 | 0 | **No cambia:** falla en las tres condiciones (ver §10) |
| N3 equipo existente | 0,5 | 0,5 | 0,5 | **No cambia:** encuentra Mindray (D05) pero no Epson (D06) |
| N4 un solo postor | 0 | 0,33 | 0 | Solo baseline trae D07 en el puesto 3 |
| N5 ganador Mindray | 0 | **1** | 1 | **El tamaño ayuda:** ver abajo |

**Caso en que el tamaño ayuda (N5).** Con chunks de 100 palabras el primer resultado es el documento correcto (D05, score 0,891), pero el chunk recuperado es `D05-C01` = convocatoria + ítem + cronograma. Ahí están "reactivos", "Mindray" y "Jaén", que son las palabras de la consulta, pero **no** el passage de la buena pro (D05-P06, "Buena pro otorgada a SIMED PERU S.A.C por S/ 358,500.00"), que quedó en otro chunk. Recall@3 = 0. Con 180 o 320 palabras toda la ficha de D05 cabe en un solo chunk, que sale primero (0,871) y contiene P06: Recall@1 = 1.

Es la diferencia entre documento y fragmento. La consulta describe el proceso y la evidencia es otra parte de la ficha. Solo un chunk que contiene ambas cosas la recupera.

**Caso en que el tamaño perjudica (N4).** En baseline, el chunk `D07-C02` (postores = 1 + buena pro + contrato) entra en el puesto 3. En large ese mismo passage queda dentro del chunk de la ficha completa de D07, cuya representación la dominan la convocatoria y los alimentos, y baja al puesto 11.

## 9. Resultados

| Experimento | Variable modificada | Variable fija | Métrica | Resultado | Conclusión |
|---|---|---|---|---|---|
| Consulta | query original / estructurada | corpus, chunk 180, e5-small, IndexFlatIP, top-k | schema_valid_rate + Recall@k | schema_valid 1,0; intención 3/5; R@3 0,47 en Q0 y Q1; Jaccard 0,9 | El LLM conserva la necesidad (casi la copia) y no la mejora; un JSON válido puede traer una intención equivocada |
| Chunking | tamaño del chunk | corpus, queries, qrels, overlap, e5-small, índice, top-k | Recall@1/3/5 | mean R@3: small 0,20 · baseline 0,47 · large 0,40 | Con estas fichas, 180 palabras recupera más evidencia; el chunk pequeño separa la evidencia (buena pro) de lo que la identifica (ítem) |

Figuras: `results/figs/exp1_recall3.png` y `results/figs/exp2_recall.png`. Auditoría completa (top-3 de cada necesidad en cada condición, con scores y passages marcados): `results/resumen.md`.

## 10. Un error de recuperación

**N2: "requerimientos que mencionan una marca pero permiten ofertar un producto equivalente".** Recall@3 = 0 con los tres tamaños y con Q0 y Q1.

- **Qué buscaba:** los passages de Oracle (D03) e IBM Power (D04), que dicen literalmente "… O EQUIVALENTE".
- **Qué recuperó (baseline):** D02-C02 (ítems de micropipetas, 0,851), D06-C01 (tintas Epson, 0,850) y D07-C01 (Vaso de Leche, 0,849).
- **Por qué falla:**
  - La evidencia es una **marca léxica corta**: dos palabras ("o equivalente") dentro de un chunk de 130-180 palabras que habla de servidores, montos, fechas y postores.
  - El embedding resume el tema del chunk (compras, ítems, entidades) y diluye esa marca.
  - Los scores del top-10 van de 0,851 a 0,838. El chunk relevante de D04 queda en el **puesto 8** (0,840), a solo 0,011 del primero, y el de D03 en el puesto 15 (0,828). e5 pone a todos los chunks del mismo dominio muy cerca, así que la diferencia entre "acepta equivalente" y "no lo menciona" no alcanza para mover el orden.
  - No es truncación (ningún chunk supera 512 tokens) ni un qrel mal puesto: el texto está en el chunk.
- **Qué lo arreglaría:** una señal léxica exacta (BM25 o un filtro por la frase), que es la recuperación híbrida de la Semana 5.

## 11. Limitación

- **Muestra mínima.** 5 necesidades y 10 documentos: un cambio de un passage mueve el Recall@3 medio en 0,05 a 0,1, y no hay potencia para afirmar diferencias.
- **Tope de tokens.** El texto del SEACE ocupa ~2 tokens por palabra. La condición large está limitada por la ventana de 512 tokens (3 de 13 chunks se cortaron antes de 320 palabras; el máximo real fue 257), así que "large" significa "hasta 320 palabras o 512 tokens".
- **Juez único.** El autor diseñó las necesidades y los qrels; no hay un segundo anotador.
- **Corpus construido.** Las fichas se armaron con una plantilla a partir de OCDS. Las bases en PDF, donde están los requisitos completos, no están en los datos.

## 12. Conclusión

Bajo este corpus (10 fichas OCDS, 92 passages), estas 5 necesidades, estos qrels y multilingual-e5-small con IndexFlatIP, se observó lo siguiente:

1. La consulta estructurada por Qwen2.5-0.5B fue schema-valid en 5/5, pero en 4/5 copió la necesidad y en 2/5 eligió una intención equivocada. Recuperó lo mismo que la consulta original (mean Recall@3 = 0,47 en ambas).
2. Cambiar solo el tamaño del chunk llevó el mean Recall@3 de 0,20 (100 palabras) a 0,47 (180) y 0,40 (320). La diferencia la explican sobre todo N5, donde el chunk pequeño separa la buena pro del ítem que la identifica, y N4.
3. N2 falla con cualquier tamaño, porque la evidencia es una frase corta ("o equivalente") que el embedding diluye.

No se puede generalizar que 180 palabras sea el mejor tamaño ni que el LLM nunca mejore la consulta. Con estos datos, la recuperación densa sola encuentra el documento correcto más a menudo que la evidencia exacta.

## 13. Fuentes

**Fuente primaria (método)**

- Wang, L., Yang, N., Huang, X., Yang, L., Majumder, R. y Wei, F. (2024). *Multilingual E5 Text Embeddings: A Technical Report*. arXiv:2402.05672. → Modelo usado; justifica los prefijos `query:` / `passage:`, la normalización y el uso del coseno.

**Fuentes adicionales**

- Wang, L., Yang, N., Huang, X., Jiao, B., Yang, L., Jiang, D., Majumder, R. y Wei, F. (2022). *Text Embeddings by Weakly-Supervised Contrastive Pre-training*. arXiv:2212.03533. → Entrenamiento contrastivo de E5 y por qué consulta y pasaje llevan prefijos distintos.
- Karpukhin, V., Oğuz, B., Min, S., Lewis, P., Wu, L., Edunov, S., Chen, D. y Yih, W. (2020). Dense Passage Retrieval for Open-Domain Question Answering. *EMNLP 2020*, 6769-6781. → Recuperación densa de pasajes con producto interno. Discute que BM25 es sensible a palabras y frases muy selectivas que el modelo denso puede no capturar, que es lo que pasa en N2.
- Johnson, J., Douze, M. y Jégou, H. (2021). Billion-scale similarity search with GPUs. *IEEE Transactions on Big Data*, 7(3), 535-547. → Biblioteca FAISS; `IndexFlatIP` es la búsqueda exacta de referencia frente a los índices aproximados.
- Fazekas, M. y Kocsis, G. (2020). Uncovering High-Level Corruption: Cross-National Objective Corruption Risk Indicators Using Public Procurement Data. *British Journal of Political Science*, 50(1), 155-164. → Postor único como indicador de riesgo: motiva la necesidad N4.
- Open Contracting Partnership. *Open Contracting Data Standard 1.1* (documentación). → Estructura de `tender`, `awards`, `contracts` y `parties` usada para armar las fichas.

**Herramientas de búsqueda sugeridas para ampliar la revisión:** Connected Papers con Karpukhin et al. (2020) como semilla para recuperación densa e híbrida; Scite para ver cómo se cita el reporte de mE5.
