# Plantilla obligatoria de notebook didáctico

Cada `.ipynb` de `notebooks/0X_case_*/` debe seguir las 18 secciones de
abajo. La cabecera de cada celda Markdown corresponde a una sección. Las
celdas de código quedan dentro de la sección correspondiente y siempre
tienen una breve celda Markdown previa que las explica.

```markdown
# {Nombre del notebook}

> _Caso de uso: {A-J}/{nombre} · Capa Medallion: {bronce/plata/oro/transversal} · Spec: {ruta de la spec}_

## 1. Objetivo
Una frase clara: qué se logrará al terminar este notebook.

## 2. Qué se aprende
- Conceptos clave que el alumno se llevará.
- Técnicas que practicará.
- Dónde podrá reutilizar lo aprendido.

## 3. Contexto del caso de uso
Resumen del caso (3–4 párrafos) ligado al material docente IES Simarro.

## 4. Relación con CENTINELA+
Cómo encaja este notebook en el sistema real CENTINELA+ (qué reproducimos,
qué simulamos, qué cambia con datos reales).

## 5. Relación con Medallion
- De qué capa se lee.
- En qué capa se escribe.
- Qué transformación implementa.

## 6. Datos de entrada
- Datasets reales esperados.
- Mocks usados (etiquetados como `MOCK — sintético`).
- Tamaño/formato.

## 7. Schema CAPTIA esperado
Constantes de `notebooks/_common/captia_schema.py` y line protocol de ejemplo.

## 8. Setup y variables de entorno
- Imports.
- `load_env()`.
- Comprobación opcional de stack levantado.

## 9. Carga de datos o mock
Lectura del CSV / generación del mock.

## 10. Exploración paso a paso
EDA breve con plots y observaciones.

## 11. Transformación bronce → plata
Si aplica: mapping a `captia_point` con 5 tags y unidades.

## 12. Construcción de capa oro
Si aplica: features ML, embeddings, agregaciones, modelos.

## 13. Visualizaciones explicativas
Plots adicionales que ayuden a entender el resultado.

## 14. Validaciones
Checks: schema, rangos, sin leakage, reproducibilidad.

## 15. Errores comunes
- Lista numerada con causa probable y arreglo.

## 16. Ejercicios propuestos
1–3 ejercicios con dificultad creciente. Pista incluida.

## 17. Cómo se reutiliza con datos reales
Qué hay que cambiar (`.env`, dataset_id, query) para pasar de mock/CSV
público a `simarro-prod` o a otro centro CENTINELA+.

## 18. Resumen final y próximos pasos
- Recordatorio de los conceptos.
- Enlaces al siguiente notebook y a la doc web.
```

## Convenciones

- **Markdown abundante:** cada celda de código va precedida por una celda
  Markdown que la explica.
- **Diagramas Mermaid:** cuando ayuden, especialmente en secciones 4 y 5.
- **Determinismo:** `SEED = 42` declarado al inicio.
- **Mocks etiquetados:** comentario explícito `# MOCK — sintético, no
  representa datos reales`.
- **Sin secretos:** `from notebooks._common.connection import load_env, get_influx_client`.
- **Cierre con enlaces:** sección 18 incluye `[Documento web del caso →
  ../../docs/use-cases/case-X-...md]`.
