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

## Reglas de trabajo (IMPORTANTE)

1. **Modificación mínima invasiva.** Cambia solo las líneas que causan el problema.
   No reescribas archivos ni funciones que ya funcionan.
2. **Ediciones quirúrgicas.** Usa `Edit` (reemplazo exacto), nunca `Write` sobre un
   archivo existente salvo que el usuario pida rehacerlo entero.
3. **Análisis de impacto antes de editar.** Menciona qué otras funciones/puzzles
   podrían verse afectados por el cambio.
4. **Verifica con tests.** Antes y después de un cambio en `puzzles/`, corre la suite:
   `python -m pytest -q`. Si tocas una familia, corre al menos su test.
   Un cambio no está "listo" hasta que los tests pasan.
5. **Trabajo arriesgado → rama.** Para refactors o cambios grandes:
   `git checkout -b fix/<algo>`. Correcciones puntuales pueden ir directo, pero
   **commitea un baseline antes** de empezar algo que pueda romper.
6. **El usuario lidera la revisión de juegos.** No auditar los 16 por cuenta propia
   ni "mejorar" lo que no se pidió. Esperar el reporte concreto y corregir ese punto.
7. **Idioma:** responder siempre en español.

## Reglas que la app DEBE cumplir (invariantes)

- Sudoku (todas las variantes y tamaños): sin repetidos en fila, columna ni caja;
  todos los símbolos presentes. La solución es un tablero completo y válido.
- El puzzle mostrado es un subconjunto de la solución (nunca contradice la solución).
- Solución = mismo diseño del puzzle, con los valores que faltaban en **negrita** y
  celdas pobladas sombreadas (ver `renderer.py`).
- Estos invariantes están cubiertos por `tests/` — si agregas/editas un juego,
  agrega su test de reglas.
