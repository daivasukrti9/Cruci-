# Memoria del Proyecto — Cruci

Proyecto **adoptado** (existía antes de daRevelation, con su propio git,
`.claude/` y `CLAUDE.md` — no se reorganizó su estructura interna para no
romper rutas relativas de `app.py`, `iniciar.bat`, `pytest.ini`, etc.).
Estructura original preservada tal cual, en vez del layout
`workspace/`/`context/` estándar de `projects/_template/`.

## Última actualización
2026-07-26 — traslado desde `Downloads\Apps\Cruci` a `daRevelation\projects\Cruci`, sin cambios de contenido.

## Decisiones arquitectónicas
(fuente de verdad: `manage_adr` de codebase-memory-mcp una vez indexado —
acá solo se referencia el ID, no se duplica el contenido)
-

## Dependencias clave
- App Flask de crucigramas (`app.py`, `templates/`, `static/`, `tools/`)
- Ver `requirements.txt` / `requirements-dev.txt`
- Docs propios: `CLAUDE.md`, `PLAN_CORRECCIONES.md`, `ESQUEMA_JUEGOS_PENDIENTES.md`, `docs/`

## Estimado FinOps
- Tokens/llamadas esperadas:
- APIs de pago involucradas:

## Pendientes
- Ver `PLAN_CORRECCIONES.md` (correcciones pendientes ya documentadas por el usuario)
- Indexar con `index_repository` (codebase-memory-mcp) la primera vez que se trabaje acá

## Commits relevantes
- Tiene su propio historial git independiente (no se tocó al moverlo)
