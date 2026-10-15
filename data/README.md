# Datos de la PC2

## Procedencia

Los 10 documentos son **fichas de procesos reales del SEACE** (Perú) reconstruidas como texto a partir de los CSV OCDS que usa la PC1 (archivo `2026/`, convocatorias de 2024 a 2026). No hay texto sintético ni editado a mano. `pc2/src/construir_corpus.py` genera `corpus.jsonl` con esta plantilla fija:

| Passage | Tabla OCDS de origen |
|---|---|
| convocatoria | `main` (entidad, procedimiento, objeto `tender_description`, fecha, valor referencial) |
| ítem (uno por ítem) | `tender_items` (descripción del requerimiento, cantidad, valor, estado) |
| cronograma | `main` (periodos de consultas y de presentación de ofertas) |
| documentos | `tender_documents` (títulos: bases, actas, pliegos…) |
| postores | `main.tender_numberOfTenderers` + `tender_tenderers` (5 nombres como máximo) |
| resultado | `awards` + `awards_suppliers` (4 adjudicaciones como máximo) |
| contrato | `contracts` (3 contratos como máximo) |

Regla de ítems: si un proceso tiene más de 8 ítems, se incluye el ítem objetivo y los siguientes por orden de id hasta completar 8.

| Doc | ocid (`ocds-dgv273-seacev3-…`) | Entidad | Ítems incluidos | Passages | Palabras | Por qué está |
|---|---|---|---|---:|---:|---|
| D01 | 1216035 | Agencia de Compras de las FF.AA. | 1 de 1 | 7 | 178 | Marca sin equivalente (Cisco); 28 postores. Caso C01 de la PC1 |
| D02 | 1184513 | U.N. Toribio Rodríguez de Mendoza | 8 de 104 | 14 | 271 | Marca y código de catálogo (Agilent) entre materiales de laboratorio |
| D03 | 1095541 | SBS | 1 de 1 | 7 | 134 | Marca con "o equivalente" (Oracle); un solo postor. Caso C05 |
| D04 | 2024-1945-10 | COFOPRI | 1 de 1 | 7 | 185 | Marca con "o equivalente" (IBM Power); 9 postores |
| D05 | 1183945 | Hospital General de Jaén | 1 de 1 | 7 | 157 | Reactivos para equipo propio Mindray; un solo postor. Caso C06 |
| D06 | 1209013 | Red de Salud Pachitea | 1 de 1 | 7 | 171 | Tintas para impresora Epson existente; 23 postores. Caso C07 |
| D07 | 1183834 | Municipalidad Distrital de Rondos | 2 de 2 | 8 | 201 | Alimentos sin marca (Vaso de Leche); un solo postor. Caso C09 |
| D08 | 1042389 | CENARES (MINSA) | 8 de 27 | 14 | 378 | Dispositivos médicos genéricos; 36 postores |
| D09 | 1178657 | Municipalidad Metropolitana de Lima | 1 de 1 | 7 | 201 | Trampa léxica: "ladrillo ADOBE" no es el software |
| D10 | 2024-48-3 | Gobierno Regional de Piura | 8 de 15 | 14 | 390 | Combustible sin marca; 11 postores |

Total: 10 documentos y 92 passages.

## Necesidades y qrels

`necesidades.jsonl` contiene las 5 necesidades tal como las formuló el autor (Q0), con la intención esperada. `qrels.json` indica qué **passages** son relevantes. La relevancia se fija sobre `passage_id` y no sobre chunks, para que no cambie cuando cambia el tamaño del chunk.

Criterio: es relevante el passage que contiene la evidencia **literal** que pide la necesidad.

| Necesidad | Evidencia buscada | Passages relevantes |
|---|---|---|
| N1 | Marca o código sin "o equivalente" | D01-P02 (Cisco), D02-P02 (Agilent) |
| N2 | Marca con "o equivalente" | D03-P01, D03-P02 (Oracle), D04-P01, D04-P02 (IBM Power) |
| N3 | Marca por equipo que la entidad ya tiene | D05-P01, D05-P02 (Mindray), D06-P01, D06-P02 (Epson) |
| N4 | Un solo postor | D03-P05, D05-P05, D07-P06 |
| N5 | Ganador y monto de los reactivos Mindray | D05-P06 |

En N2 y N3 el objeto de la convocatoria (P01) repite el texto del ítem (P02), por eso ambos cuentan. En N1 el objeto no menciona la marca y solo cuenta el ítem.

## Regla experimental

`corpus.jsonl`, `necesidades.jsonl` y `qrels.json` no se modificaron después de ver resultados. Si cambia cualquiera de los tres, es una nueva versión del benchmark.
