# 08 — Score de realismo físico (Fase 8)

## Contexto

Score multidimensional que sintetiza los `RuleResult` del validador (`07-*`) en un valor por dimensión y un score global.

**Decisión de diseño** (consenso usuario):
- **Dos scores**: interno (sin ground-truth) y externo (con ground-truth, futuro post L-01).
- Cada dimensión tiene `confidence_level` propio; reglas con confidence `low` no penalizan score interno.
- Dimensiones bloqueadas (R-FAULT-* hoy) **no** penalizan; se reportan como `unscored`.

## Dimensiones

10 dimensiones, cada una asociada a un grupo de reglas y a un peso para el score global.

| Dim | Nombre | Reglas | Peso global | Notas |
|-----|--------|--------|-------------|-------|
| D1 | Coherencia térmica | R-T-01..05 | 0.12 | inercia, drift, ganancia, convergencia |
| D2 | Coherencia HVAC | R-HVAC-MODE-01, R-HVAC-EN-01..03, R-VLV-01..02 | 0.13 | activación, modo, válvula |
| D3 | Coherencia energética | R-PW-01..03, R-EN-01..03 | 0.12 | descomposición, conservación, monotonicidad |
| D4 | Coherencia ocupación/CO₂ | R-CO2-01..05, R-OCC-01..03 | 0.15 | la dimensión más rica en señales BMS |
| D5 | Coherencia meteo/contexto | R-OT-01..02, R-DL-01, R-WX-01, R-WD-01 | 0.08 | estacionalidad y continuidad |
| D6 | Coherencia humedad | R-RH-01..03 | 0.05 | bajo peso porque modelo simplista |
| D7 | Coherencia averías | R-FAULT-01..05 | 0.10 | unscored mientras L-PV-02 sin resolver |
| D8 | Coherencia anomalías de dato | R-AN-01..03 | 0.05 | simple cobertura de rates |
| D9 | Reproducibilidad | R-INF-02 (subset) | 0.10 | crítico — sin esto no hay validación robusta |
| D10 | Compatibilidad CAPTIA | R-INF-01, R-INF-03..05 | 0.10 | schema, naming, freq, tz |
| **Total** | | **53 reglas** | **1.00** | |

## Cómputo del score por dimensión

Para cada dimensión `d`:

```text
rules_d = reglas asignadas a d
applicable_rules_d = reglas con applicable_when(scenario, inventory) == True
                     AND not skipped (skip explícito en config)
                     AND confidence_level >= "medium"  (excluye "low" del score interno)

passed_d = sum(1 for r in applicable_rules_d if r.passed)
weighted_d = sum(severity_weight(r.severity) for r in applicable_rules_d if r.passed)
total_weighted_d = sum(severity_weight(r.severity) for r in applicable_rules_d)

score_d = weighted_d / total_weighted_d  if total_weighted_d > 0 else None  (unscored)

severity_weight:
  error: 3
  warning: 2
  info: 1
```

**Decisión**: errores pesan 3× más que info. Si una regla error falla, hunde el score más que muchas info pasando.

## Cómputo del score global

```text
applicable_dimensions = {d for d in [D1..D10] if score_d is not None}

score_global = sum(weight_d * score_d for d in applicable_dimensions) / sum(weight_d for d in applicable_dimensions)
```

Si una dimensión no tiene reglas aplicables (e.g., D7 en código actual), su peso se redistribuye proporcionalmente entre el resto. **No** se interpreta como score 0.

## Score interno vs externo

### Score interno (sin ground-truth)

- Calculado con las 53 reglas observables que solo requieren las propias salidas + literatura.
- Excluye reglas `confidence: low` del cómputo (reportadas en `diagnostics`).
- Es lo que se reporta hoy, sin esperar L-01.

### Score externo (futuro, post-L-01)

- Adicionalmente, calcula RMSE / MAPE contra datos reales IES Simarro:
  - Por aula, por variable, por ventana mensual.
  - Métricas:
    - `co2_rmse_per_aula_ppm`
    - `temperature_mae_per_aula_C`
    - `power_daily_mae_per_aula_W`
    - `occupancy_correlation_per_aula`
- Score externo combina `score_interno · (1 - clip(rmse_normalizado, 0, 0.5))`.
- **Hoy**: no aplicable. Reportado como `unscored`.

## Estructura del PhysicalRealismScore

```yaml
PhysicalRealismScore:
  score_internal_global: float (0..1)  # interno
  score_external_global: float | null  # externo (null si no hay GT)
  per_dimension:
    D1_thermal_coherence:
      score: float | null
      weight: float (0.12)
      rules_evaluated: int
      rules_passed: int
      rules_skipped_low_confidence: int
      diagnostics: list[RuleResult]  # las low-confidence
    D2_hvac_coherence: {...}
    ... (por D3..D10)
  global_summary:
    confidence: enum {high, medium, low}  # média ponderada de confidence_level
    blocked_dimensions: list[str]  # ["D7"] hoy
    most_failed_rules: list[(rule_id, fail_count)]
    recommendations: list[str]  # priorizadas
```

## Interpretación cualitativa

| Score interno global | Interpretación |
|---------------------|---------------|
| ≥ 0.95 | Generador físicamente plausible; usable para entrenamiento ML. |
| 0.85-0.95 | Plausible con caveats menores; consultar `diagnostics` para gaps conocidos. |
| 0.70-0.85 | Aceptable para demo / desarrollo; revisar reglas error fallidas. |
| 0.50-0.70 | Problemas estructurales detectados; **no** usar para entrenamiento. |
| < 0.50 | Generador no plausible; bloquear hasta corregir. |

## Estimación a priori del score (con código actual)

Usando supuestos:
- Reglas error fallidas: 0 (asumido OK porque no hay violaciones de schema obvias).
- Reglas warning fallidas: ~5 (R-RH-02, R-HVAC-EN-03, R-VLV-02, R-OCC-01 si L-PV-06 sin resolver, R-FAULT-* skipped).
- Reglas info fallidas: ~3 (oscilaciones, tasa de spikes).
- Reglas low confidence omitidas (no penalizan): R-RH-02, R-HVAC-EN-03, R-VLV-02 → no entran en score interno.

**Resultado preliminar**:
- D1 thermal: 5/5 high-confidence pasan → 1.00
- D2 HVAC: 5/6 (R-HVAC-EN-03 omitida) high-confidence pasan → ~0.90
- D3 energy: 6/6 pasan → 1.00
- D4 occ/CO₂: 7/8 pasan (R-OCC-01 puede fallar por L-PV-06) → ~0.87
- D5 meteo: 5/5 pasan → 1.00
- D6 humidity: 1/2 pasan (R-RH-02 omitida) → 1.00 (de las medium-high)
- D7 faults: unscored
- D8 anomalies: 3/3 pasan → 1.00
- D9 reproducibility: 1/1 pasa → 1.00
- D10 CAPTIA: 4/5 pasan (R-INF-03 catalog incompleto por relays) → 0.80

**Score interno global** (D7 unscored, redistribución):
```
weights_total = 1.0 - 0.10 (D7) = 0.90
weighted_sum =
  0.12·1.00 + 0.13·0.90 + 0.12·1.00 + 0.15·0.87 + 0.08·1.00 + 0.05·1.00
  + 0.05·1.00 + 0.10·1.00 + 0.10·0.80
  = 0.12 + 0.117 + 0.12 + 0.1305 + 0.08 + 0.05 + 0.05 + 0.10 + 0.08
  = 0.8475
score_interno_global ≈ 0.8475 / 0.90 ≈ 0.94
```

**Conclusión preliminar**: el generador está en banda **0.85-0.95** (plausible con caveats). Los caveats son los gaps conocidos (L-PV-02, L-PV-06, L-PV-07, L-PV-09).

## Recomendaciones derivadas del score

El `RealismScorer` produce `recommendations` ordenadas por impacto:

1. **Resolver L-PV-02** (cablear FaultEventSink): activa D7 entera, sumando ~0.10 al score global.
2. **Resolver L-PV-06** (calendario unificado): R-OCC-01 pasa con confianza, sube D4 a ~0.95.
3. **Implementar MinOnOffTimer** (L-PV-07): R-HVAC-EN-03 sube de low a high → D2 a ~1.00.
4. **Modelar deshumidification cooling** (L-PV-09): R-RH-02 sube de low a medium → D6 más robusto.
5. **Generar relay_1..relay_4** (L-PV-01 sub-issue): R-INF-03 pasa → D10 a 1.00.
6. **Calibrar gen_ppm con datos reales** (L-01): score externo aplicable → eleva confidence.

## Severity weights — justificación

```yaml
error: 3
warning: 2
info: 1
```

- **error** son violaciones críticas (schema, conservación, monotonicidad). Si fallan, los datos no son confiables.
- **warning** son desviaciones notables (rate of change, banda esperada). Indican modelado pobre, no falla estructural.
- **info** son métricas diagnósticas (oscilación, ratios) que se consultan pero no bloquean.

Alternativas consideradas:
- 5/3/1 (más punitivo con errors): descartado porque inflarían el sesgo si una regla falla por edge case.
- 1/1/1 (uniforme): descartado porque pone todo al mismo nivel y oculta criticidad.
- Logarítmico (10/3/1): considerado pero excesivo para 53 reglas.

## Confidence weight — propuesta v2 (no aplicado en v1)

Para v2, sumar componente de confidence:

```text
weighted_d = sum(severity_weight(r.severity) · confidence_weight(r.confidence_level)
                 for r in applicable_rules_d if r.passed)

confidence_weight:
  high: 1.0
  medium: 0.7
  low: 0.4
```

En v1 simplemente excluimos low del cómputo (ya implementado). Para v2, incluirlas con peso atenuado.

## Métricas Prometheus emitidas (alineado con `09-*`)

```text
captia_physics_realism_score_global  (gauge)
captia_physics_realism_score_dimension{dimension="D1_thermal_coherence"}  (gauge)
captia_physics_realism_score_confidence{level}  (gauge)
captia_physics_recommendation{priority, description}  (counter o info)
```

## Cómo se usa el score

| Stakeholder | Uso |
|-------------|-----|
| Equipo desarrollo | Antes de comprometer cambio en physics, comprobar score baseline → no degradar > 0.05. |
| Equipo ML | Antes de entrenar modelos sobre dataset sintético, verificar score ≥ 0.85. |
| Equipo CAPTIA Tech | Score externo (futuro) cuantifica fidelidad vs datos reales — input a decisión de "ya es suficientemente realista". |
| CI/CD | Gate: score < 0.70 → fail. Score 0.70-0.85 → warning. Score ≥ 0.85 → pass. |
| Dashboard | Panel principal en `bms_physics_validation.json` con score global + breakdown. |

## Limitaciones del score

1. **Sesgo por reglas implementadas**: el score solo mide lo que las 53 reglas miden. Brechas no cubiertas no se reflejan.
2. **Dependencia de window size**: reglas con window grande (estacionalidad) requieren ≥ 1 mes de datos; en runs cortos quedan `pending` y no contribuyen.
3. **Sin comparación entre runs**: el score actual es absoluto. Una métrica útil futura: `delta_score_vs_baseline`.
4. **Penalización binaria**: regla pasa o falla. Reglas con tolerancia fina podrían tener score continuo (0..1 dentro de la regla); v1 mantiene binario por simplicidad.
5. **No mide novelty**: un generador determinista que repite el mismo patrón pasaría todas las reglas pero sería inutilizable para ML — no medido.

## Política de evolución del score

- Cuando se añada una nueva regla, asignar a una dimensión existente (no crear D11+ salvo justificación).
- Cambiar pesos requiere ADR en `09-physical-observability.md` (NO crear ADR aquí — el spec set se queda con el peso v1).
- El score es **comparable entre runs del mismo dominio** (`bms_classrooms`); no es comparable entre dominios distintos.

## Plantilla del reporte de score

```text
PHYSICS REALISM SCORE — bms_classrooms
=======================================

Run: <uuid> | Seed: 42 | Duration: 7d | N_assets: 10

Score interno global: 0.94 ✓
Confidence: high

Per dimension:
  D1 Thermal coherence    : 1.00  (5/5 reglas, weight 0.12)  ✓
  D2 HVAC coherence       : 0.90  (5/6 reglas + 1 low-conf omitida, weight 0.13)  ⚠
  D3 Energy coherence     : 1.00  (6/6 reglas, weight 0.12)  ✓
  D4 Occupancy/CO2        : 0.87  (7/8 reglas, weight 0.15)  ⚠
  D5 Weather/context      : 1.00  (5/5 reglas, weight 0.08)  ✓
  D6 Humidity coherence   : 1.00  (1/2 reglas + 1 low-conf omitida, weight 0.05)  ✓
  D7 Faults               : UNSCORED  (5 reglas bloqueadas por L-PV-02, weight 0.10)
  D8 Data anomalies       : 1.00  (3/3 reglas, weight 0.05)  ✓
  D9 Reproducibility      : 1.00  (1/1 regla, weight 0.10)  ✓
  D10 CAPTIA compat       : 0.80  (4/5 reglas, R-INF-03 fail catalog, weight 0.10)  ⚠

Recommendations (ordered by impact on score):
  1. [+0.10] Resolve L-PV-02: wire FaultEventSink (activates D7).
  2. [+0.04] Resolve L-PV-06: unified calendar (activates R-OCC-01 with confidence).
  3. [+0.02] Add relay_1..relay_4 generation (closes R-INF-03 catalog gap).

Diagnostics (low-confidence rules, not in score):
  - R-HVAC-EN-03 (anti short-cycle): short_cycle_ratio = 0.18 → exceeds 0.05 threshold.
  - R-RH-02 (cooling anti-correlation): RH slope in cooling-on windows: +0.02 %RH/min (expected negative).
  - R-VLV-02 (rate limiter): max valve_pos diff/min: 100% (expected ≤ 30%).

Score externo (vs ground truth): NOT AVAILABLE (L-01 pending).
```

Este reporte es lo que `validate_csv_long()` devuelve serializado en JSON.
