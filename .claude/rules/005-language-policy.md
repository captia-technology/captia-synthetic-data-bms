# Regla 005 — Política de idioma

## Documentación

- Specs en `docs/specs/synthetic-bms/` → **español** (alineado con docs/ existentes).
- `README.md` raíz → **español** con cabecera bilingüe opcional.
- Comentarios técnicos cortos en código → **español** cuando aporten contexto de dominio.

## Código

- Identificadores (variables, funciones, clases, módulos) → **inglés** snake_case.
- Excepciones: claves del schema canónico CAPTIA (`captia_env`, `domain_id`, `site_id`, `asset_id`, `variable`).
- Mensajes de log → **inglés** (procesables por herramientas).
- Mensajes de error a usuario humano (UI, API responses) → **español**.

## Commits

- Commit messages → **inglés** Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`).

## Diacríticos

Conservar siempre tildes y eñes (ñ/Ñ) en español. No transliterar ("año" no "ano", "función" no "funcion").
