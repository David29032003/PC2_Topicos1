# Resumen de resultados (PC2)

Generado por `pc2/src/reporte.py` a partir de `pc2/results/*.jsonl`. 5 necesidades, 10 documentos, 92 passages.

## Segmentación

| condición | target_words | n_chunks | palabras_media | palabras_max | tokens_media | tokens_max | cortes_por_tokens | chunks_sin_solape |
|---|---|---|---|---|---|---|---|---|
| small | 100 | 36 | 79.5 | 100 | 162.4 | 236 | 0 | 1 |
| baseline | 180 | 18 | 137.2 | 180 | 276.4 | 365 | 0 | 0 |
| large | 320 | 13 | 178.8 | 257 | 357.2 | 502 | 3 | 0 |

FAISS `IndexFlatIP` vs búsqueda exacta en NumPy (Q·Eᵀ): small: mismo orden=True, dif. máx. de score=2.4e-07, baseline: mismo orden=True, dif. máx. de score=1.2e-07, large: mismo orden=True, dif. máx. de score=2.4e-07

## Experimento 1 · consulta original (Q0) vs consulta estructurada (Q1)

| métrica | valor |
|---|---|
| n_necesidades | 5 |
| json_exacto_rate | 0 |
| json_parseable_rate | 1 |
| schema_valid_rate | 1 |
| intent_accuracy | 0.6 |
| abstain_rate | 0 |
| adecuada_rate | 0.6 |
| jaccard_top3_medio | 0.9 |

| consulta | Recall@1 | Recall@3 | Recall@5 |
|---|---|---|---|
| Q0 | 0.3 | 0.47 | 0.53 |
| Q1 | 0.3 | 0.47 | 0.53 |

| id | Q0 | Q1 (query del LLM) | intent | estado | R@3 Q0 | R@3 Q1 | Jaccard top-3 |
|---|---|---|---|---|---|---|---|
| N1 | ¿En qué compras se exige una marca o un código de fabricante específico sin aceptar productos equivalentes? | ¿En qué compras se exige una marca o un código de fabricante específico sin aceptar productos equivalentes? | marca_sin_equivalente | valida_adecuada | 0.5 | 0.5 | 1 |
| N2 | Quiero encontrar los requerimientos que mencionan una marca pero permiten ofertar un producto equivalente. | ¿Qué requerimientos mencionan una marca pero permiten ofertar un producto equivalente? | marca_con_equivalente | valida_adecuada | 0 | 0 | 0.5 |
| N3 | ¿Qué compras son de insumos o repuestos para un equipo que la entidad ya tiene? | ¿Qué compras son de insumos o repuestos para un equipo que la entidad ya tiene? | competencia | valida_no_adecuada | 0.5 | 0.5 | 1 |
| N4 | ¿En qué procesos se presentó un solo postor? | ¿En qué procesos se presentó un solo postor? | competencia | valida_adecuada | 0.33 | 0.33 | 1 |
| N5 | ¿Qué empresa ganó la compra de reactivos para el equipo Mindray del hospital de Jaén y por cuánto? | ¿Qué empresa ganó la compra de reactivos para el equipo Mindray del hospital de Jaén y por cuánto? | marca_con_equivalente | valida_no_adecuada | 1 | 1 | 1 |

## Experimento 2 · tamaño del chunk

| condición | target_words | Recall@1 | Recall@3 | Recall@5 |
|---|---|---|---|---|
| small | 100 | 0 | 0.2 | 0.3 |
| baseline | 180 | 0.3 | 0.47 | 0.53 |
| large | 320 | 0.3 | 0.4 | 0.47 |

Recall@3 por necesidad (Δ respecto de baseline):

| id | R@3 small | R@3 baseline | R@3 large | Δ small | Δ large |
|---|---|---|---|---|---|
| N1 | 0.5 | 0.5 | 0.5 | 0 | 0 |
| N2 | 0 | 0 | 0 | 0 | 0 |
| N3 | 0.5 | 0.5 | 0.5 | 0 | 0 |
| N4 | 0 | 0.33 | 0 | -0.33 | -0.33 |
| N5 | 0 | 1 | 1 | -1 | 0 |

## Auditoría: top-3 de cada necesidad en cada condición

### N1 · small

- Consulta: *¿En qué compras se exige una marca o un código de fabricante específico sin aceptar productos equivalentes?*
- Evidencia relevante (qrels): D01-P02, D02-P02
- Recall@1/3/5: 0 / 0.5 / 1

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D08-C01-W100 | 0.8223 | D08-P01, D08-P02 | Convocatoria SIE-SIE-31-2024-CENARES/ MINSA-1. CENTRO NACIONAL DE ABASTECIMIENTO DE RECURSOS ESTRATEGICOS EN S… |
| 2 | D01-C01-W100 | 0.8185 | D01-P01, D01-P02 ★, D01-P03 | Convocatoria LP-ABR-1-2026-OGA-ACFFAA-1. AGENCIA DE COMPRAS DE LAS FUERZAS ARMADAS convocó este proceso por Li… |
| 3 | D09-C03-W100 | 0.8102 | D09-P04, D09-P05, D09-P06, D09-P07 | Documentos publicados en el SEACE: Bases Administrativas; Acta de no formulación de consultas y observaciones;… |

### N1 · baseline

- Consulta: *¿En qué compras se exige una marca o un código de fabricante específico sin aceptar productos equivalentes?*
- Evidencia relevante (qrels): D01-P02, D02-P02
- Recall@1/3/5: 0.5 / 0.5 / 0.5

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D01-C01-W180 | 0.8129 | D01-P01, D01-P02 ★, D01-P03, D01-P04, D01-P05, D01-P06, D01-P07 | Convocatoria LP-ABR-1-2026-OGA-ACFFAA-1. AGENCIA DE COMPRAS DE LAS FUERZAS ARMADAS convocó este proceso por Li… |
| 2 | D08-C01-W180 | 0.8104 | D08-P01, D08-P02, D08-P03, D08-P04, D08-P05, D08-P06 | Convocatoria SIE-SIE-31-2024-CENARES/ MINSA-1. CENTRO NACIONAL DE ABASTECIMIENTO DE RECURSOS ESTRATEGICOS EN S… |
| 3 | D09-C02-W180 | 0.8102 | D09-P04, D09-P05, D09-P06, D09-P07 | Documentos publicados en el SEACE: Bases Administrativas; Acta de no formulación de consultas y observaciones;… |

### N1 · large

- Consulta: *¿En qué compras se exige una marca o un código de fabricante específico sin aceptar productos equivalentes?*
- Evidencia relevante (qrels): D01-P02, D02-P02
- Recall@1/3/5: 0.5 / 0.5 / 0.5

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D01-C01-W320 | 0.8129 | D01-P01, D01-P02 ★, D01-P03, D01-P04, D01-P05, D01-P06, D01-P07 | Convocatoria LP-ABR-1-2026-OGA-ACFFAA-1. AGENCIA DE COMPRAS DE LAS FUERZAS ARMADAS convocó este proceso por Li… |
| 2 | D08-C01-W320 | 0.8069 | D08-P01, D08-P02, D08-P03, D08-P04, D08-P05, D08-P06, D08-P07, D08-P08, D08-P09 | Convocatoria SIE-SIE-31-2024-CENARES/ MINSA-1. CENTRO NACIONAL DE ABASTECIMIENTO DE RECURSOS ESTRATEGICOS EN S… |
| 3 | D06-C01-W320 | 0.8051 | D06-P01, D06-P02, D06-P03, D06-P04, D06-P05, D06-P06, D06-P07 | Convocatoria LP-ABR-1-2026-RSP/OC-1. GOBIERNO REGIONAL DE HUANUCO - RED DE SALUD PACHITEA convocó este proceso… |

### N2 · small

- Consulta: *Quiero encontrar los requerimientos que mencionan una marca pero permiten ofertar un producto equivalente.*
- Evidencia relevante (qrels): D03-P01, D03-P02, D04-P01, D04-P02
- Recall@1/3/5: 0 / 0 / 0

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D07-C02-W100 | 0.8593 | D07-P02, D07-P03, D07-P04 | Ítem 1: ADQUISICION DE LECHE EVAPORADA ENTERA X 410 GRAMOS PARA EL PROGRAMA VADO DE LECHE 2026. Cantidad: 2232… |
| 2 | D02-C03-W100 | 0.8507 | D02-P07, D02-P08, D02-P09, D02-P10, D02-P11 | Ítem 6: Set de micropipetas multicanal, con volúmenes 0.5¿10 µL, 10¿100 µL y 20¿200 µL. Cantidad: 1 unidad. Va… |
| 3 | D08-C01-W100 | 0.8505 | D08-P01, D08-P02 | Convocatoria SIE-SIE-31-2024-CENARES/ MINSA-1. CENTRO NACIONAL DE ABASTECIMIENTO DE RECURSOS ESTRATEGICOS EN S… |

### N2 · baseline

- Consulta: *Quiero encontrar los requerimientos que mencionan una marca pero permiten ofertar un producto equivalente.*
- Evidencia relevante (qrels): D03-P01, D03-P02, D04-P01, D04-P02
- Recall@1/3/5: 0 / 0 / 0

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D02-C02-W180 | 0.8506 | D02-P07, D02-P08, D02-P09, D02-P10, D02-P11, D02-P12, D02-P13, D02-P14 | Ítem 6: Set de micropipetas multicanal, con volúmenes 0.5¿10 µL, 10¿100 µL y 20¿200 µL. Cantidad: 1 unidad. Va… |
| 2 | D06-C01-W180 | 0.8503 | D06-P01, D06-P02, D06-P03, D06-P04, D06-P05, D06-P06, D06-P07 | Convocatoria LP-ABR-1-2026-RSP/OC-1. GOBIERNO REGIONAL DE HUANUCO - RED DE SALUD PACHITEA convocó este proceso… |
| 3 | D07-C01-W180 | 0.8487 | D07-P01, D07-P02, D07-P03, D07-P04, D07-P05, D07-P06 | Convocatoria LP-ABR-5-2025-MDR/CS-1. MUNICIPALIDAD DISTRITAL DE RONDOS convocó este proceso por Licitación Púb… |

### N2 · large

- Consulta: *Quiero encontrar los requerimientos que mencionan una marca pero permiten ofertar un producto equivalente.*
- Evidencia relevante (qrels): D03-P01, D03-P02, D04-P01, D04-P02
- Recall@1/3/5: 0 / 0 / 0

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D07-C01-W320 | 0.8532 | D07-P01, D07-P02, D07-P03, D07-P04, D07-P05, D07-P06, D07-P07, D07-P08 | Convocatoria LP-ABR-5-2025-MDR/CS-1. MUNICIPALIDAD DISTRITAL DE RONDOS convocó este proceso por Licitación Púb… |
| 2 | D06-C01-W320 | 0.8503 | D06-P01, D06-P02, D06-P03, D06-P04, D06-P05, D06-P06, D06-P07 | Convocatoria LP-ABR-1-2026-RSP/OC-1. GOBIERNO REGIONAL DE HUANUCO - RED DE SALUD PACHITEA convocó este proceso… |
| 3 | D08-C01-W320 | 0.8459 | D08-P01, D08-P02, D08-P03, D08-P04, D08-P05, D08-P06, D08-P07, D08-P08, D08-P09 | Convocatoria SIE-SIE-31-2024-CENARES/ MINSA-1. CENTRO NACIONAL DE ABASTECIMIENTO DE RECURSOS ESTRATEGICOS EN S… |

### N3 · small

- Consulta: *¿Qué compras son de insumos o repuestos para un equipo que la entidad ya tiene?*
- Evidencia relevante (qrels): D05-P01, D05-P02, D06-P01, D06-P02
- Recall@1/3/5: 0 / 0.5 / 0.5

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D08-C01-W100 | 0.8516 | D08-P01, D08-P02 | Convocatoria SIE-SIE-31-2024-CENARES/ MINSA-1. CENTRO NACIONAL DE ABASTECIMIENTO DE RECURSOS ESTRATEGICOS EN S… |
| 2 | D05-C01-W100 | 0.8454 | D05-P01 ★, D05-P02 ★, D05-P03 | Convocatoria DIRECTA-DIRECTA-8-2025-HGJ-1. GOBIERNO REGIONAL DE CAJAMARCA-HOSPITAL GENERAL DE JAEN convocó est… |
| 3 | D01-C01-W100 | 0.8360 | D01-P01, D01-P02, D01-P03 | Convocatoria LP-ABR-1-2026-OGA-ACFFAA-1. AGENCIA DE COMPRAS DE LAS FUERZAS ARMADAS convocó este proceso por Li… |

### N3 · baseline

- Consulta: *¿Qué compras son de insumos o repuestos para un equipo que la entidad ya tiene?*
- Evidencia relevante (qrels): D05-P01, D05-P02, D06-P01, D06-P02
- Recall@1/3/5: 0 / 0.5 / 0.5

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D01-C01-W180 | 0.8407 | D01-P01, D01-P02, D01-P03, D01-P04, D01-P05, D01-P06, D01-P07 | Convocatoria LP-ABR-1-2026-OGA-ACFFAA-1. AGENCIA DE COMPRAS DE LAS FUERZAS ARMADAS convocó este proceso por Li… |
| 2 | D08-C01-W180 | 0.8377 | D08-P01, D08-P02, D08-P03, D08-P04, D08-P05, D08-P06 | Convocatoria SIE-SIE-31-2024-CENARES/ MINSA-1. CENTRO NACIONAL DE ABASTECIMIENTO DE RECURSOS ESTRATEGICOS EN S… |
| 3 | D05-C01-W180 | 0.8363 | D05-P01 ★, D05-P02 ★, D05-P03, D05-P04, D05-P05, D05-P06, D05-P07 | Convocatoria DIRECTA-DIRECTA-8-2025-HGJ-1. GOBIERNO REGIONAL DE CAJAMARCA-HOSPITAL GENERAL DE JAEN convocó est… |

### N3 · large

- Consulta: *¿Qué compras son de insumos o repuestos para un equipo que la entidad ya tiene?*
- Evidencia relevante (qrels): D05-P01, D05-P02, D06-P01, D06-P02
- Recall@1/3/5: 0 / 0.5 / 0.5

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D01-C01-W320 | 0.8407 | D01-P01, D01-P02, D01-P03, D01-P04, D01-P05, D01-P06, D01-P07 | Convocatoria LP-ABR-1-2026-OGA-ACFFAA-1. AGENCIA DE COMPRAS DE LAS FUERZAS ARMADAS convocó este proceso por Li… |
| 2 | D08-C01-W320 | 0.8370 | D08-P01, D08-P02, D08-P03, D08-P04, D08-P05, D08-P06, D08-P07, D08-P08, D08-P09 | Convocatoria SIE-SIE-31-2024-CENARES/ MINSA-1. CENTRO NACIONAL DE ABASTECIMIENTO DE RECURSOS ESTRATEGICOS EN S… |
| 3 | D05-C01-W320 | 0.8363 | D05-P01 ★, D05-P02 ★, D05-P03, D05-P04, D05-P05, D05-P06, D05-P07 | Convocatoria DIRECTA-DIRECTA-8-2025-HGJ-1. GOBIERNO REGIONAL DE CAJAMARCA-HOSPITAL GENERAL DE JAEN convocó est… |

### N4 · small

- Consulta: *¿En qué procesos se presentó un solo postor?*
- Evidencia relevante (qrels): D03-P05, D05-P05, D07-P06
- Recall@1/3/5: 0 / 0 / 0

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D09-C03-W100 | 0.8263 | D09-P04, D09-P05, D09-P06, D09-P07 | Documentos publicados en el SEACE: Bases Administrativas; Acta de no formulación de consultas y observaciones;… |
| 2 | D02-C04-W100 | 0.8191 | D02-P11, D02-P12, D02-P13, D02-P14 | Documentos publicados en el SEACE: Bases Administrativas; Resumen ejecutivo. Número de postores registrados: 1… |
| 3 | D10-C05-W100 | 0.8145 | D10-P11, D10-P12 | Documentos publicados en el SEACE: Bases Administrativas; Resumen ejecutivo; Documentos de Otorgamiento de Bue… |

### N4 · baseline

- Consulta: *¿En qué procesos se presentó un solo postor?*
- Evidencia relevante (qrels): D03-P05, D05-P05, D07-P06
- Recall@1/3/5: 0 / 0.33 / 0.67

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D09-C02-W180 | 0.8263 | D09-P04, D09-P05, D09-P06, D09-P07 | Documentos publicados en el SEACE: Bases Administrativas; Acta de no formulación de consultas y observaciones;… |
| 2 | D10-C03-W180 | 0.7992 | D10-P12, D10-P13, D10-P14 | Número de postores registrados: 11. Postores: GRIFO NICOL CAROLINA E.I.R.L, ESTACION DE SERVICIOS AYPATE E.I.R… |
| 3 | D07-C02-W180 | 0.7967 | D07-P06 ★, D07-P07, D07-P08 | Número de postores registrados: 1. Postores: INVERSIONES LECHE MASS S.A.C. Buena pro otorgada a INVERSIONES LE… |

### N4 · large

- Consulta: *¿En qué procesos se presentó un solo postor?*
- Evidencia relevante (qrels): D03-P05, D05-P05, D07-P06
- Recall@1/3/5: 0 / 0 / 0.33

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D02-C02-W320 | 0.8191 | D02-P11, D02-P12, D02-P13, D02-P14 | Documentos publicados en el SEACE: Bases Administrativas; Resumen ejecutivo. Número de postores registrados: 1… |
| 2 | D09-C01-W320 | 0.7966 | D09-P01, D09-P02, D09-P03, D09-P04, D09-P05, D09-P06, D09-P07 | Convocatoria LP-ABR-27-2025-MML-OGA-OL-1. MUNICIPALIDAD METROPOLITANA DE LIMA convocó este proceso por Licitac… |
| 3 | D10-C02-W320 | 0.7900 | D10-P08, D10-P09, D10-P10, D10-P11, D10-P12, D10-P13, D10-P14 | Ítem 7: DIESEL B5 S50 - MUNICIPALIDAD PROVINCIAL Y DISTRITOS DE AYABACA. Cantidad: 15000 galon. Valor referenc… |

### N5 · small

- Consulta: *¿Qué empresa ganó la compra de reactivos para el equipo Mindray del hospital de Jaén y por cuánto?*
- Evidencia relevante (qrels): D05-P06
- Recall@1/3/5: 0 / 0 / 0

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D05-C01-W100 | 0.8906 | D05-P01, D05-P02, D05-P03 | Convocatoria DIRECTA-DIRECTA-8-2025-HGJ-1. GOBIERNO REGIONAL DE CAJAMARCA-HOSPITAL GENERAL DE JAEN convocó est… |
| 2 | D08-C01-W100 | 0.8432 | D08-P01, D08-P02 | Convocatoria SIE-SIE-31-2024-CENARES/ MINSA-1. CENTRO NACIONAL DE ABASTECIMIENTO DE RECURSOS ESTRATEGICOS EN S… |
| 3 | D08-C04-W100 | 0.8206 | D08-P07, D08-P08, D08-P09, D08-P10 | Ítem 6: APOSITO DE GASA Y ALGODON ESTERIL 10 x 20 cm. Cantidad: 787575 unidad. Valor referencial del ítem: S/ … |

### N5 · baseline

- Consulta: *¿Qué empresa ganó la compra de reactivos para el equipo Mindray del hospital de Jaén y por cuánto?*
- Evidencia relevante (qrels): D05-P06
- Recall@1/3/5: 1 / 1 / 1

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D05-C01-W180 | 0.8708 | D05-P01, D05-P02, D05-P03, D05-P04, D05-P05, D05-P06 ★, D05-P07 | Convocatoria DIRECTA-DIRECTA-8-2025-HGJ-1. GOBIERNO REGIONAL DE CAJAMARCA-HOSPITAL GENERAL DE JAEN convocó est… |
| 2 | D08-C01-W180 | 0.8282 | D08-P01, D08-P02, D08-P03, D08-P04, D08-P05, D08-P06 | Convocatoria SIE-SIE-31-2024-CENARES/ MINSA-1. CENTRO NACIONAL DE ABASTECIMIENTO DE RECURSOS ESTRATEGICOS EN S… |
| 3 | D08-C02-W180 | 0.8237 | D08-P06, D08-P07, D08-P08, D08-P09, D08-P10, D08-P11, D08-P12 | Ítem 5: APOSITO DE GASA Y ALGODON ESTERIL 10 x 10 cm. Cantidad: 499250 unidad. Valor referencial del ítem: S/ … |

### N5 · large

- Consulta: *¿Qué empresa ganó la compra de reactivos para el equipo Mindray del hospital de Jaén y por cuánto?*
- Evidencia relevante (qrels): D05-P06
- Recall@1/3/5: 1 / 1 / 1

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D05-C01-W320 | 0.8708 | D05-P01, D05-P02, D05-P03, D05-P04, D05-P05, D05-P06 ★, D05-P07 | Convocatoria DIRECTA-DIRECTA-8-2025-HGJ-1. GOBIERNO REGIONAL DE CAJAMARCA-HOSPITAL GENERAL DE JAEN convocó est… |
| 2 | D08-C01-W320 | 0.8238 | D08-P01, D08-P02, D08-P03, D08-P04, D08-P05, D08-P06, D08-P07, D08-P08, D08-P09 | Convocatoria SIE-SIE-31-2024-CENARES/ MINSA-1. CENTRO NACIONAL DE ABASTECIMIENTO DE RECURSOS ESTRATEGICOS EN S… |
| 3 | D08-C02-W320 | 0.8232 | D08-P09, D08-P10, D08-P11, D08-P12, D08-P13, D08-P14 | Ítem 8: GUANTE DE NITRILO DESCARTABLE TALLA L PARA EXAMEN MEDICO. Cantidad: 6746900 unidad. Valor referencial … |

### N1 · Q1 (baseline)

- Consulta: *¿En qué compras se exige una marca o un código de fabricante específico sin aceptar productos equivalentes?*
- Evidencia relevante (qrels): D01-P02, D02-P02
- Recall@1/3/5: 0.5 / 0.5 / 0.5

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D01-C01-W180 | 0.8129 | D01-P01, D01-P02 ★, D01-P03, D01-P04, D01-P05, D01-P06, D01-P07 | Convocatoria LP-ABR-1-2026-OGA-ACFFAA-1. AGENCIA DE COMPRAS DE LAS FUERZAS ARMADAS convocó este proceso por Li… |
| 2 | D08-C01-W180 | 0.8104 | D08-P01, D08-P02, D08-P03, D08-P04, D08-P05, D08-P06 | Convocatoria SIE-SIE-31-2024-CENARES/ MINSA-1. CENTRO NACIONAL DE ABASTECIMIENTO DE RECURSOS ESTRATEGICOS EN S… |
| 3 | D09-C02-W180 | 0.8102 | D09-P04, D09-P05, D09-P06, D09-P07 | Documentos publicados en el SEACE: Bases Administrativas; Acta de no formulación de consultas y observaciones;… |

### N2 · Q1 (baseline)

- Consulta: *¿Qué requerimientos mencionan una marca pero permiten ofertar un producto equivalente?*
- Evidencia relevante (qrels): D03-P01, D03-P02, D04-P01, D04-P02
- Recall@1/3/5: 0 / 0 / 0

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D06-C01-W180 | 0.8193 | D06-P01, D06-P02, D06-P03, D06-P04, D06-P05, D06-P06, D06-P07 | Convocatoria LP-ABR-1-2026-RSP/OC-1. GOBIERNO REGIONAL DE HUANUCO - RED DE SALUD PACHITEA convocó este proceso… |
| 2 | D07-C01-W180 | 0.8184 | D07-P01, D07-P02, D07-P03, D07-P04, D07-P05, D07-P06 | Convocatoria LP-ABR-5-2025-MDR/CS-1. MUNICIPALIDAD DISTRITAL DE RONDOS convocó este proceso por Licitación Púb… |
| 3 | D09-C02-W180 | 0.8164 | D09-P04, D09-P05, D09-P06, D09-P07 | Documentos publicados en el SEACE: Bases Administrativas; Acta de no formulación de consultas y observaciones;… |

### N3 · Q1 (baseline)

- Consulta: *¿Qué compras son de insumos o repuestos para un equipo que la entidad ya tiene?*
- Evidencia relevante (qrels): D05-P01, D05-P02, D06-P01, D06-P02
- Recall@1/3/5: 0 / 0.5 / 0.5

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D01-C01-W180 | 0.8407 | D01-P01, D01-P02, D01-P03, D01-P04, D01-P05, D01-P06, D01-P07 | Convocatoria LP-ABR-1-2026-OGA-ACFFAA-1. AGENCIA DE COMPRAS DE LAS FUERZAS ARMADAS convocó este proceso por Li… |
| 2 | D08-C01-W180 | 0.8377 | D08-P01, D08-P02, D08-P03, D08-P04, D08-P05, D08-P06 | Convocatoria SIE-SIE-31-2024-CENARES/ MINSA-1. CENTRO NACIONAL DE ABASTECIMIENTO DE RECURSOS ESTRATEGICOS EN S… |
| 3 | D05-C01-W180 | 0.8363 | D05-P01 ★, D05-P02 ★, D05-P03, D05-P04, D05-P05, D05-P06, D05-P07 | Convocatoria DIRECTA-DIRECTA-8-2025-HGJ-1. GOBIERNO REGIONAL DE CAJAMARCA-HOSPITAL GENERAL DE JAEN convocó est… |

### N4 · Q1 (baseline)

- Consulta: *¿En qué procesos se presentó un solo postor?*
- Evidencia relevante (qrels): D03-P05, D05-P05, D07-P06
- Recall@1/3/5: 0 / 0.33 / 0.67

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D09-C02-W180 | 0.8263 | D09-P04, D09-P05, D09-P06, D09-P07 | Documentos publicados en el SEACE: Bases Administrativas; Acta de no formulación de consultas y observaciones;… |
| 2 | D10-C03-W180 | 0.7992 | D10-P12, D10-P13, D10-P14 | Número de postores registrados: 11. Postores: GRIFO NICOL CAROLINA E.I.R.L, ESTACION DE SERVICIOS AYPATE E.I.R… |
| 3 | D07-C02-W180 | 0.7967 | D07-P06 ★, D07-P07, D07-P08 | Número de postores registrados: 1. Postores: INVERSIONES LECHE MASS S.A.C. Buena pro otorgada a INVERSIONES LE… |

### N5 · Q1 (baseline)

- Consulta: *¿Qué empresa ganó la compra de reactivos para el equipo Mindray del hospital de Jaén y por cuánto?*
- Evidencia relevante (qrels): D05-P06
- Recall@1/3/5: 1 / 1 / 1

| rank | chunk | score | passages (★ = relevante) | inicio del texto |
|---|---|---|---|---|
| 1 | D05-C01-W180 | 0.8708 | D05-P01, D05-P02, D05-P03, D05-P04, D05-P05, D05-P06 ★, D05-P07 | Convocatoria DIRECTA-DIRECTA-8-2025-HGJ-1. GOBIERNO REGIONAL DE CAJAMARCA-HOSPITAL GENERAL DE JAEN convocó est… |
| 2 | D08-C01-W180 | 0.8282 | D08-P01, D08-P02, D08-P03, D08-P04, D08-P05, D08-P06 | Convocatoria SIE-SIE-31-2024-CENARES/ MINSA-1. CENTRO NACIONAL DE ABASTECIMIENTO DE RECURSOS ESTRATEGICOS EN S… |
| 3 | D08-C02-W180 | 0.8237 | D08-P06, D08-P07, D08-P08, D08-P09, D08-P10, D08-P11, D08-P12 | Ítem 5: APOSITO DE GASA Y ALGODON ESTERIL 10 x 10 cm. Cantidad: 499250 unidad. Valor referencial del ítem: S/ … |

