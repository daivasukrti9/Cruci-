# KDP Puzzle Book Generator

App Flask que genera puzzles (Sudoku y variantes, KenKen, Futoshiki, laberintos,
crucigramas, lógica) y los exporta como SVG/PNG/PDF listos para Amazon KDP.

## Cómo arrancar

- Python: `C:\Users\Maximiliano Marinero\AppData\Local\Programs\Python\Python313\python.exe`
- Arranque: `iniciar.bat` o el python de arriba con `app.py` → http://localhost:5000
- Tras editar código de puzzles, **reiniciar el servidor** para que tome los cambios.

## Estructura

- `app.py` — Flask, endpoints `/api/generate`, `/api/export`, `/api/batch_pdf`. Caché en memoria.
- `puzzles/sudoku.py` — Sudoku clásico/16×16/X/Killer/Jigsaw/Letras. Lógica + validación de reglas.
- `puzzles/kenken.py`, `logic_puzzles.py`, `maze.py`, `crossword.py` — el resto de familias.
- `puzzles/renderer.py` — todo el SVG (puzzle y solución). Estilos: flat / isometric / geometric.
- `puzzles/exporter.py` — PDF/PNG/SVG con tamaños KDP.
- `puzzles_patterns/catalog.json` — catálogo maestro de tipos de puzzle.
- `tests/` — suite de reglas (red de seguridad contra regresiones).

## Reglas de trabajo (específicas de este proyecto)

Las reglas generales (edición mínima invasiva, Git como red, análisis de impacto,
idioma) están en el `CLAUDE.md` global. Aquí solo lo propio de Cruci:

Para revisión visual de la UI web (no del SVG de los puzzles en sí, eso lo
cubren los `tests/` de reglas) usar el subagente `frontend-designer`
(`daRevelation/.claude/agents/frontend-designer.md`) — ver
`_global/skills-registry.md` para el arsenal disponible y su valoración.

1. **Tests con pytest.** Antes y después de un cambio en `puzzles/`, corre:
   `python -m pytest`. Si tocas una familia de puzzle, corre al menos su test.
   Baseline en git = commit `95eebab` (estado funcional de partida).
2. **El usuario lidera la revisión de juegos.** No auditar los 16 por cuenta propia
   ni "mejorar" lo que no se pidió. Esperar el reporte concreto y corregir ese punto.
3. **Reiniciar el servidor** tras editar código de puzzles para que tome los cambios.

## Reglas que la app DEBE cumplir (invariantes)

- Sudoku (todas las variantes y tamaños): sin repetidos en fila, columna ni caja;
  todos los símbolos presentes. La solución es un tablero completo y válido.
- El puzzle mostrado es un subconjunto de la solución (nunca contradice la solución).
- Solución = mismo diseño del puzzle, con los valores que faltaban en **negrita** y
  celdas pobladas sombreadas (ver `renderer.py`).
- Estos invariantes están cubiertos por `tests/` — si agregas/editas un juego,
  agrega su test de reglas.
