"""
SVG Renderer for all puzzle types.
Supports three visual styles:
  - 'flat'      : Classic clean grid
  - 'isometric' : Faux-3D isometric projection (KDP B&W with grey shading)
  - 'geometric' : Bold geometric / origami style
"""
import math


# ─── Style presets ───────────────────────────────────────────────────────────

STYLES = {
    'flat': {
        'stroke': '#000000', 'fill_empty': '#ffffff', 'fill_black': '#000000',
        'fill_clue': '#e8e8e8', 'stroke_width': 1.5, 'font': 'Arial',
        'font_bold': 'Arial', 'shadow': False, 'iso': False,
    },
    'isometric': {
        'stroke': '#000000', 'fill_empty': '#ffffff', 'fill_black': '#1a1a1a',
        'fill_clue': '#d0d0d0', 'stroke_width': 1.0, 'font': 'Arial',
        'font_bold': 'Arial Black', 'shadow': True, 'iso': True,
        'iso_depth': 6, 'iso_shade': '#b0b0b0',
    },
    'geometric': {
        'stroke': '#000000', 'fill_empty': '#ffffff', 'fill_black': '#111111',
        'fill_clue': '#cccccc', 'stroke_width': 2.5, 'font': 'Georgia',
        'font_bold': 'Georgia', 'shadow': False, 'iso': False,
    },
}


def _svg_header(width, height):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">\n'
            f'<rect width="{width}" height="{height}" fill="white"/>\n')


def _svg_footer():
    return '</svg>'


def _rect(x, y, w, h, fill, stroke, sw, rx=0):
    return (f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" rx="{rx}"/>\n')


def _text(x, y, content, font, size, bold=False, color='#000000', anchor='middle'):
    weight = 'bold' if bold else 'normal'
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-family="{font}" '
            f'font-size="{size}" font-weight="{weight}" fill="{color}" '
            f'text-anchor="{anchor}" dominant-baseline="central">{content}</text>\n')


def _dash(x1, y1, x2, y2, color, sw=1.4):
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{sw}" stroke-dasharray="4,3"/>\n')


def _cage_line(x1, y1, x2, y2, color='#888888', sw=1.0):
    """Línea gris fina para marcar jaulas de cálculo (más delgada que el borde negro)."""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{sw}"/>\n')


def _ineq_symbol(op, vertical):
    """Símbolo de desigualdad de Futoshiki. `op` es la relación de la primera celda
    (izquierda si horizontal, ARRIBA si vertical) respecto a la segunda. El vértice
    del símbolo apunta al número MENOR. `<`/`>` se escapan para no romper el SVG."""
    if vertical:
        return '∧' if op == '<' else '∨'   # arriba<abajo => vértice arriba (∧)
    return '&lt;' if op == '<' else '&gt;'


def _iso_box(x, y, w, h, depth, fill, shade, stroke, sw):
    """Draw an isometric-style box (flat top with right and bottom faces)."""
    svg = ''
    # Top face
    svg += (f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>\n')
    # Right shadow face
    rx = x + w
    ry = y + depth
    svg += (f'<polygon points="{rx:.1f},{y:.1f} {rx+depth:.1f},{y+depth:.1f} '
            f'{rx+depth:.1f},{y+h+depth:.1f} {rx:.1f},{y+h:.1f}" '
            f'fill="{shade}" stroke="{stroke}" stroke-width="{sw}"/>\n')
    # Bottom shadow face
    bx = x + depth
    by = y + h
    svg += (f'<polygon points="{x:.1f},{by:.1f} {bx:.1f},{by+depth:.1f} '
            f'{x+w+depth:.1f},{by+depth:.1f} {x+w:.1f},{by:.1f}" '
            f'fill="{shade}" stroke="{stroke}" stroke-width="{sw}"/>\n')
    return svg


# ─── SUDOKU ──────────────────────────────────────────────────────────────────

def render_sudoku(puzzle, solution, size=9, style='flat', stroke_width=1.5,
                  show_solution=False, regions=None, diagonals=False,
                  cages=None, is_letters=False):
    """
    Renderiza un Sudoku (puzzle o solución) como SVG.

    La solución usa la MISMA plantilla que el puzzle (jaulas, regiones, diagonales);
    solo cambia qué números se muestran:
      - puzzle:   solo las pistas dadas.
      - solución: todos los números; las respuestas que faltaban van en NEGRITA.
    Sombreado por variante:
      - Sudoku X (diagonals): se sombrean solo las dos diagonales.
      - Asesino (cages):      sin sombreado.
      - resto:                se sombrean las casillas dadas (pistas).
    """
    st = {**STYLES.get(style, STYLES['flat']), 'stroke_width': stroke_width}
    cell = 48  # cell size px
    margin = 30
    box_size = int(math.isqrt(size)) if size in (9, 16, 4, 25) else 3
    box_h = 3 if size == 12 else box_size
    box_w = 4 if size == 12 else box_size

    grid_px = cell * size
    depth = st.get('iso_depth', 6) if st['iso'] else 0
    W = margin * 2 + grid_px + depth
    H = margin * 2 + grid_px + depth

    svg = _svg_header(W, H)

    SHADE = '#d9d9d9'
    # El Asesino (con jaulas) adopta el diseño del KenKen: cuadrícula en GRIS y las
    # jaulas en NEGRO grueso, que se entiende mucho mejor.
    grid_color = '#a8a8a8' if cages else st['stroke']

    def _is_given(r, c):
        return puzzle[r][c] not in (0, '', None)

    def _shaded(r, c):
        if diagonals:                 # Sudoku X: resaltar solo las diagonales
            return (r == c) or (r + c == size - 1)
        if cages:                     # Asesino: sin sombreado
            return False
        return _is_given(r, c)        # resto: resaltar las pistas dadas

    # Celdas: fondo (sombreado por variante) + número
    for r in range(size):
        for c in range(size):
            x = margin + c * cell
            y = margin + r * cell
            fill = SHADE if _shaded(r, c) else st['fill_empty']

            if st['iso']:
                svg += _iso_box(x, y, cell, cell, depth // 2,
                                 fill, st['iso_shade'], st['stroke'], st['stroke_width'])
            else:
                svg += _rect(x, y, cell, cell, fill, grid_color, st['stroke_width'])

            if show_solution:
                val = solution[r][c]
                bold = not _is_given(r, c)   # lo que faltaba va en negrita
            else:
                val = puzzle[r][c]
                bold = False
            if val not in (0, '', None):
                svg += _text(x + cell/2, y + cell/2, str(val),
                             st['font_bold'] if bold else st['font'],
                             cell * 0.45, bold=bold)

    # Draw box borders (thicker)
    bsw = st['stroke_width'] * 2.5
    for i in range(size + 1):
        thick_r = (i % box_h == 0) if regions is None else (i in (0, size))
        thick_c = (i % box_w == 0) if regions is None else (i in (0, size))
        sw_r = bsw if thick_r else st['stroke_width']
        sw_c = bsw if thick_c else st['stroke_width']
        # Horizontal line
        svg += (f'<line x1="{margin}" y1="{margin + i*cell}" '
                f'x2="{margin + size*cell}" y2="{margin + i*cell}" '
                f'stroke="{grid_color}" stroke-width="{sw_r}"/>\n')
        # Vertical line
        svg += (f'<line x1="{margin + i*cell}" y1="{margin}" '
                f'x2="{margin + i*cell}" y2="{margin + size*cell}" '
                f'stroke="{grid_color}" stroke-width="{sw_c}"/>\n')

    # Draw Jigsaw region borders
    if regions:
        for r in range(size):
            for c in range(size):
                rid = regions[r][c]
                # Right border
                if c + 1 < size and regions[r][c+1] != rid:
                    x1 = margin + (c+1)*cell
                    svg += (f'<line x1="{x1}" y1="{margin+r*cell}" '
                            f'x2="{x1}" y2="{margin+(r+1)*cell}" '
                            f'stroke="{st["stroke"]}" stroke-width="{bsw}"/>\n')
                # Bottom border
                if r + 1 < size and regions[r+1][c] != rid:
                    y1 = margin + (r+1)*cell
                    svg += (f'<line x1="{margin+c*cell}" y1="{y1}" '
                            f'x2="{margin+(c+1)*cell}" y2="{y1}" '
                            f'stroke="{st["stroke"]}" stroke-width="{bsw}"/>\n')

    # Jaulas del Asesino: contorno NEGRO grueso hacia adentro (inset), como el KenKen.
    if cages:
        inset = 5
        for cage in cages:
            cage_cells = set(map(tuple, cage['cells']))
            for (r, c) in cage_cells:
                x = margin + c * cell
                y = margin + r * cell
                x0, y0 = x + inset, y + inset
                x1, y1 = x + cell - inset, y + cell - inset
                if (r-1, c) not in cage_cells:
                    svg += _cage_line(x0, y0, x1, y0, color='#000000', sw=2.2)
                if (r+1, c) not in cage_cells:
                    svg += _cage_line(x0, y1, x1, y1, color='#000000', sw=2.2)
                if (r, c-1) not in cage_cells:
                    svg += _cage_line(x0, y0, x0, y1, color='#000000', sw=2.2)
                if (r, c+1) not in cage_cells:
                    svg += _cage_line(x1, y0, x1, y1, color='#000000', sw=2.2)
            # Etiqueta de la suma en la celda superior-izquierda de la jaula
            min_cell = min(cage['cells'], key=lambda p: (p[0], p[1]))
            lx = margin + min_cell[1] * cell + inset + 1
            ly = margin + min_cell[0] * cell + inset + 8
            svg += (f'<text x="{lx}" y="{ly}" font-family="Arial" '
                    f'font-size="10" font-weight="bold" fill="#000">{cage["sum"]}</text>\n')

    svg += _svg_footer()
    return svg


# ─── CROSSWORD ───────────────────────────────────────────────────────────────

def render_crossword(puzzle_grid, solution_grid, across_entries, down_entries,
                     cell_numbers, style='flat', stroke_width=1.5,
                     show_solution=False, title=''):
    if show_solution:
        # Mostrar en tabla de respuestas
        answers = {}
        answers['RESPUESTAS HORIZONTALES'] = '\n'.join([f"{e['number']}. {e['word']}" for e in across_entries])
        answers['RESPUESTAS VERTICALES'] = '\n'.join([f"{e['number']}. {e['word']}" for e in down_entries])
        return render_solution_table(answers, 'Crucigrama SOLUCIONES')

    st = {**STYLES.get(style, STYLES['flat']), 'stroke_width': stroke_width}
    size = len(puzzle_grid)
    cell = 36
    margin = 20
    W = margin * 2 + cell * size
    H = margin * 2 + cell * size

    svg = _svg_header(W, H)
    grid = puzzle_grid

    for r in range(size):
        for c in range(size):
            x = margin + c * cell
            y = margin + r * cell
            val = grid[r][c] if grid[r][c] is not None else None
            if val is None:
                # Black cell
                svg += _rect(x, y, cell, cell, st['fill_black'], st['stroke'], st['stroke_width'])
            else:
                svg += _rect(x, y, cell, cell, st['fill_empty'], st['stroke'], st['stroke_width'])
                if show_solution and val:
                    svg += _text(x + cell/2, y + cell/2 + 2, str(val),
                                 st['font_bold'], cell * 0.5, bold=True)
                # Cell number
                num = cell_numbers.get((r, c))
                if num:
                    svg += (f'<text x="{x+2}" y="{y+9}" font-family="Arial" '
                            f'font-size="8" fill="#000">{num}</text>\n')

    svg += _svg_footer()
    return svg


# ─── WORD SEARCH ─────────────────────────────────────────────────────────────

def render_word_search(grid, solution_grid, placed_words, word_positions,
                       style='flat', stroke_width=1.0, show_solution=False):
    if show_solution:
        words_with_pos = {}
        for word, info in word_positions.items():
            dr, dc = info['direction']
            r1, c1 = info['cells'][0]
            words_with_pos[word] = f"↓({r1},{c1})" if dr > 0 else f"→({r1},{c1})" if dc > 0 else f"↙({r1},{c1})"
        return render_solution_table(words_with_pos, 'Sopa de Letras SOLUCIÓN', cols=2)

    st = {**STYLES.get(style, STYLES['flat']), 'stroke_width': stroke_width}
    rows = len(grid)
    cols = len(grid[0])
    cell = 30
    margin = 20
    W = margin * 2 + cell * cols
    H = margin * 2 + cell * rows

    svg = _svg_header(W, H)
    disp = grid

    # Highlight word cells in solution
    sol_cells = set()
    if show_solution:
        for word, info in word_positions.items():
            for r, c in info['cells']:
                sol_cells.add((r, c))

    for r in range(rows):
        for c in range(cols):
            x = margin + c * cell
            y = margin + r * cell
            fill = '#d8d8d8' if (r, c) in sol_cells else st['fill_empty']
            svg += _rect(x, y, cell, cell, fill, st['stroke'], st['stroke_width'])
            ch = disp[r][c]
            if ch:
                svg += _text(x + cell/2, y + cell/2, ch.upper(),
                             st['font'], cell * 0.5)

    svg += _svg_footer()
    return svg


# ─── KENKEN ──────────────────────────────────────────────────────────────────

def render_kenken(puzzle, solution, cages, size, style='flat', stroke_width=1.5,
                  show_solution=False):
    """KenKen sobre la MISMA plantilla. La cuadrícula de celdas va en GRIS y las
    jaulas de cálculo se marcan con una línea NEGRA gruesa hacia adentro, para que
    resalten (mejor legibilidad). La solución usa esa misma plantilla."""
    st = {**STYLES.get(style, STYLES['flat']), 'stroke_width': stroke_width}
    cell = 60
    margin = 30
    grid_gray = '#a8a8a8'                 # cuadrícula en gris
    cage_black = '#000000'                # jaulas en negro
    W = margin * 2 + cell * size
    H = margin * 2 + cell * size
    svg = _svg_header(W, H)

    # Celdas (borde GRIS) + números (en la solución todos son respuesta)
    for r in range(size):
        for c in range(size):
            x = margin + c * cell
            y = margin + r * cell
            svg += _rect(x, y, cell, cell, st['fill_empty'], grid_gray, 1.0)
            val = solution[r][c] if show_solution else puzzle[r][c]
            if val:
                svg += _text(x + cell / 2, y + cell / 2 + 2, str(val),
                             st['font'], cell * 0.45, bold=show_solution)

    # Borde externo (gris, marco)
    svg += _rect(margin, margin, cell * size, cell * size, 'none', grid_gray, 2.0)

    # Jaulas: contorno NEGRO grueso hacia adentro (inset) + etiqueta de la operación
    inset = 5
    for cage in cages:
        cage_cells = set(map(tuple, cage['cells']))
        for (r, c) in cage_cells:
            x = margin + c * cell
            y = margin + r * cell
            x0, y0 = x + inset, y + inset
            x1, y1 = x + cell - inset, y + cell - inset
            if (r - 1, c) not in cage_cells:
                svg += _cage_line(x0, y0, x1, y0, color=cage_black, sw=2.5)
            if (r + 1, c) not in cage_cells:
                svg += _cage_line(x0, y1, x1, y1, color=cage_black, sw=2.5)
            if (r, c - 1) not in cage_cells:
                svg += _cage_line(x0, y0, x0, y1, color=cage_black, sw=2.5)
            if (r, c + 1) not in cage_cells:
                svg += _cage_line(x1, y0, x1, y1, color=cage_black, sw=2.5)
        op_sym = {'*': '×', '/': '÷', '=': ''}.get(cage['op'], cage['op'])
        label = f'{cage["target"]}{op_sym}'
        min_cell = min(cage['cells'], key=lambda p: (p[0], p[1]))
        lx = margin + min_cell[1] * cell + inset + 2
        ly = margin + min_cell[0] * cell + inset + 9
        svg += (f'<text x="{lx}" y="{ly}" font-family="Arial" '
                f'font-size="11" font-weight="bold" fill="#000">{label}</text>\n')

    svg += _svg_footer()
    return svg


# ─── MAZE (Rectangular) ──────────────────────────────────────────────────────

def render_maze_rect(grid, solution_path, style='flat', stroke_width=2.0,
                     show_solution=False, cell_size=20):
    if show_solution:
        # Mostrar solución como lista de pasos
        steps = {}
        for i, (r, c) in enumerate(solution_path[:20]):  # Primeros 20 pasos
            steps[f'Paso {i+1}'] = f'({r}, {c})'
        return render_solution_table(steps, 'Laberinto SOLUCIÓN', cols=2)

    st = {**STYLES.get(style, STYLES['flat']), 'stroke_width': stroke_width}
    rows = len(grid)
    cols = len(grid[0])
    margin = 20
    W = margin * 2 + cols * cell_size
    H = margin * 2 + rows * cell_size
    svg = _svg_header(W, H)

    sol_set = set(solution_path)

    for r in range(rows):
        for c in range(cols):
            x = margin + c * cell_size
            y = margin + r * cell_size
            if grid[r][c] == 1:
                svg += _rect(x, y, cell_size, cell_size, st['fill_black'], st['fill_black'], 0)
            elif show_solution and (r, c) in sol_set:
                svg += _rect(x, y, cell_size, cell_size, '#aaaaaa', 'none', 0)

    # Outer border
    svg += _rect(margin, margin, cols*cell_size, rows*cell_size,
                 'none', st['stroke'], stroke_width * 2)

    svg += _svg_footer()
    return svg


# ─── MAZE (Hexagonal) ────────────────────────────────────────────────────────

def render_maze_hex(cells, connections, walls, solution_path, rows, cols,
                    style='flat', stroke_width=2.0, show_solution=False):
    if show_solution:
        steps = {}
        for i, (r, c) in enumerate(solution_path[:15]):
            steps[f'Paso {i+1}'] = f'({r}, {c})'
        return render_solution_table(steps, 'Laberinto Hexagonal SOLUCIÓN', cols=2)

    st = {**STYLES.get(style, STYLES['flat']), 'stroke_width': stroke_width}
    hex_size = 20  # radius
    margin = 30
    sol_set = set(solution_path)

    def hex_center(r, c):
        offset = hex_size if r % 2 == 1 else 0
        cx = margin + c * hex_size * 1.75 + offset + hex_size
        cy = margin + r * hex_size * 1.5 + hex_size
        return cx, cy

    def hex_points(cx, cy, size):
        pts = []
        for i in range(6):
            angle = math.pi / 180 * (60 * i - 30)
            pts.append((cx + size * math.cos(angle), cy + size * math.sin(angle)))
        return pts

    max_r, max_c = max(r for r,c in cells), max(c for r,c in cells)
    cx_max, cy_max = hex_center(max_r, max_c)
    W = int(cx_max + hex_size * 2 + margin)
    H = int(cy_max + hex_size * 2 + margin)
    svg = _svg_header(W, H)

    for (r, c) in cells:
        cx, cy = hex_center(r, c)
        pts = hex_points(cx, cy, hex_size - 1)
        pt_str = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        fill = '#cccccc' if (show_solution and (r,c) in sol_set) else st['fill_empty']
        svg += (f'<polygon points="{pt_str}" fill="{fill}" '
                f'stroke="{st["stroke"]}" stroke-width="{stroke_width}"/>\n')

    svg += _svg_footer()
    return svg


# ─── HASHI (Bridges) ─────────────────────────────────────────────────────────

def render_hashi(islands, bridges, rows=14, cols=10, style='flat',
                 stroke_width=1.5, show_solution=False):
    """Hashi sobre CUADRÍCULA GRIS. Islas = cuadros redondeados con su número. La
    solución traza los puentes (líneas dobles si son 2) sobre la misma plantilla."""
    st = {**STYLES.get(style, STYLES['flat']), 'stroke_width': stroke_width}
    cell = 42
    margin = 22
    W = margin * 2 + cols * cell
    H = margin * 2 + rows * cell
    svg = _svg_header(W, H)

    # Cuadrícula gris
    grid_gray = '#cccccc'
    for i in range(rows + 1):
        y = margin + i * cell
        svg += _cage_line(margin, y, margin + cols * cell, y, color=grid_gray, sw=1.0)
    for j in range(cols + 1):
        x = margin + j * cell
        svg += _cage_line(x, margin, x, margin + rows * cell, color=grid_gray, sw=1.0)

    def center(r, c):
        return margin + c * cell + cell / 2, margin + r * cell + cell / 2

    # Puentes (solo en la solución), por debajo de las islas
    if show_solution:
        idmap = {i['id']: i for i in islands}
        for b in bridges:
            a, d = idmap[b['from']], idmap[b['to']]
            x1, y1 = center(a['row'], a['col'])
            x2, y2 = center(d['row'], d['col'])
            if b['count'] == 2:
                off = 4
                if a['row'] == d['row']:      # horizontal
                    for o in (-off, off):
                        svg += _cage_line(x1, y1 + o, x2, y2 + o, color=st['stroke'], sw=2.2)
                else:                          # vertical
                    for o in (-off, off):
                        svg += _cage_line(x1 + o, y1, x2 + o, y2, color=st['stroke'], sw=2.2)
            else:
                svg += _cage_line(x1, y1, x2, y2, color=st['stroke'], sw=2.2)

    # Islas: cuadros redondeados con el número
    isz = cell * 0.68
    for isl in islands:
        cx, cy = center(isl['row'], isl['col'])
        svg += _rect(cx - isz / 2, cy - isz / 2, isz, isz,
                     st['fill_empty'], st['stroke'], 2.0, rx=7)
        svg += _text(cx, cy, str(isl['count']), st['font_bold'], isz * 0.55, bold=True)

    svg += _svg_footer()
    return svg


# ─── HITORI ──────────────────────────────────────────────────────────────────

def render_hitori(puzzle, solution, style='flat', stroke_width=1.5, show_solution=False):
    """Hitori sobre la MISMA plantilla. Puzzle: todos los números. Solución: las
    celdas tachadas van en NEGRO con el número en blanco; las blancas normales."""
    st = {**STYLES.get(style, STYLES['flat']), 'stroke_width': stroke_width}
    rows = len(puzzle)
    cols = len(puzzle[0])
    cell = 44
    margin = 20
    W = margin * 2 + cols * cell
    H = margin * 2 + rows * cell
    svg = _svg_header(W, H)

    for r in range(rows):
        for c in range(cols):
            x = margin + c * cell
            y = margin + r * cell
            is_black = show_solution and solution[r][c] == -1
            fill = st['fill_black'] if is_black else st['fill_empty']
            svg += _rect(x, y, cell, cell, fill, st['stroke'], st['stroke_width'])
            val = puzzle[r][c]
            if val is not None and val != '':
                color = '#ffffff' if is_black else '#000000'
                svg += _text(x + cell / 2, y + cell / 2, str(val),
                             st['font'], cell * 0.42, bold=False, color=color)

    svg += _svg_footer()
    return svg


# ─── NURIKABE ────────────────────────────────────────────────────────────────

def render_nurikabe(puzzle, solution, style='flat', stroke_width=1.5, show_solution=False):
    """Nurikabe sobre la MISMA plantilla. Puzzle: solo las pistas numéricas.
    Solución: el muro/océano en NEGRO y las islas blancas con su número."""
    st = {**STYLES.get(style, STYLES['flat']), 'stroke_width': stroke_width}
    rows = len(puzzle)
    cols = len(puzzle[0])
    cell = 50
    margin = 20
    W = margin * 2 + cols * cell
    H = margin * 2 + rows * cell
    svg = _svg_header(W, H)

    grid = puzzle

    for r in range(rows):
        for c in range(cols):
            x = margin + c * cell
            y = margin + r * cell
            val = grid[r][c] if grid else puzzle[r][c]
            sol_val = solution[r][c] if solution else None

            if show_solution:
                fill = st['fill_black'] if sol_val == 0 else st['fill_empty']
            else:
                fill = st['fill_empty']

            svg += _rect(x, y, cell, cell, fill, st['stroke'], st['stroke_width'])

            # Clue number
            pv = puzzle[r][c]
            if pv is not None and pv > 0:
                txt_fill = '#ffffff' if show_solution and sol_val == 0 else '#000000'
                svg += _text(x + cell/2, y + cell/2, str(pv), st['font_bold'],
                             cell * 0.4, bold=True, color=txt_fill)

    svg += _svg_footer()
    return svg


# ─── FUTOSHIKI ───────────────────────────────────────────────────────────────

def render_futoshiki(puzzle, solution, inequalities, style='flat',
                     stroke_width=1.5, show_solution=False):
    st = {**STYLES.get(style, STYLES['flat']), 'stroke_width': stroke_width}
    size = len(puzzle)
    cell = 44            # cuadros más pequeños
    gap = 26             # más espacio para símbolos grandes de mayor/menor
    margin = 30
    sym_size = 28        # símbolos < > ∧ ∨ grandes (accesibilidad)
    W = margin * 2 + size * cell + (size - 1) * gap
    H = margin * 2 + size * cell + (size - 1) * gap
    svg = _svg_header(W, H)

    # Celdas: las PISTAS numéricas (números dados) van en negro NORMAL; las respuestas
    # que se completan en la solución van en negro y NEGRITA. Así se distinguen igual
    # que en el Sudoku (pista normal vs respuesta en negrita). Misma plantilla en ambas.
    for r in range(size):
        for c in range(size):
            x = margin + c * (cell + gap)
            y = margin + r * (cell + gap)
            # Esquinas ligeramente redondeadas (distribución tipo "cuadros sueltos")
            svg += _rect(x, y, cell, cell, st['fill_empty'], st['stroke'], st['stroke_width'], rx=5)
            given = puzzle[r][c] not in (0, '', None)
            if show_solution:
                val = solution[r][c]
                if val:
                    svg += _text(x + cell/2, y + cell/2, str(val), st['font'],
                                 cell * 0.56, bold=not given, color='#000000')
            elif given:
                svg += _text(x + cell/2, y + cell/2, str(puzzle[r][c]), st['font'],
                             cell * 0.56, bold=False, color='#000000')

    # Inequalities
    for ineq in inequalities:
        r1, c1 = ineq['r1'], ineq['c1']
        r2, c2 = ineq['r2'], ineq['c2']
        op = ineq['op']
        if r1 == r2:  # horizontal: (r1,c1) es la celda de la izquierda
            x = margin + c1 * (cell + gap) + cell + gap / 2
            y = margin + r1 * (cell + gap) + cell / 2
            svg += _text(x, y, _ineq_symbol(op, vertical=False), st['font_bold'], sym_size, bold=True)
        else:  # vertical: (r1,c1) es la celda de ARRIBA
            x = margin + c1 * (cell + gap) + cell / 2
            y = margin + r1 * (cell + gap) + cell + gap / 2
            svg += _text(x, y, _ineq_symbol(op, vertical=True), st['font_bold'], sym_size, bold=True)

    svg += _svg_footer()
    return svg


# ─── AKARI ───────────────────────────────────────────────────────────────────

def render_akari(puzzle, solution, style='flat', stroke_width=1.5, show_solution=False):
    """Akari sobre la MISMA plantilla. Muros = celdas negras (con número en blanco).
    Solución: bombillas como discos, y las celdas iluminadas sombreadas suavemente."""
    st = {**STYLES.get(style, STYLES['flat']), 'stroke_width': stroke_width}
    rows = len(puzzle)
    cols = len(puzzle[0])
    cell = 32
    margin = 16
    W = margin * 2 + cols * cell
    H = margin * 2 + rows * cell
    svg = _svg_header(W, H)

    black = {(r, c) for r in range(rows) for c in range(cols) if puzzle[r][c] is not None}
    bulbs = set()
    lit = set()
    if show_solution:
        bulbs = {(r, c) for r in range(rows) for c in range(cols) if solution[r][c] == 'L'}
        for (br, bc) in bulbs:
            lit.add((br, bc))
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = br + dr, bc + dc
                while 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in black:
                    lit.add((nr, nc))
                    nr += dr
                    nc += dc

    for r in range(rows):
        for c in range(cols):
            x = margin + c * cell
            y = margin + r * cell
            pv = puzzle[r][c]
            if pv is not None:               # muro
                svg += _rect(x, y, cell, cell, st['fill_black'], st['stroke'], st['stroke_width'])
                if isinstance(pv, int) and pv >= 0:
                    svg += _text(x + cell / 2, y + cell / 2, str(pv), st['font_bold'],
                                 cell * 0.5, bold=True, color='#ffffff')
            else:
                fill = '#e9e9e9' if (r, c) in lit else st['fill_empty']
                svg += _rect(x, y, cell, cell, fill, st['stroke'], st['stroke_width'])
                if (r, c) in bulbs:          # bombilla
                    cx, cy = x + cell / 2, y + cell / 2
                    svg += (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{cell*0.32}" '
                            f'fill="{st["fill_black"]}" stroke="#000000" stroke-width="1"/>\n')
                    svg += (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{cell*0.13}" '
                            f'fill="#ffffff"/>\n')

    svg += _svg_footer()
    return svg


# ─── MASYU ───────────────────────────────────────────────────────────────────

def render_masyu(puzzle, solution_path, pearls, style='flat', stroke_width=1.5,
                 show_solution=False):
    """Masyu sobre CUADRÍCULA GRIS con perlas (○ blanca, ● negra). La solución traza
    el bucle (línea negra gruesa) sobre la misma plantilla."""
    st = {**STYLES.get(style, STYLES['flat']), 'stroke_width': stroke_width}
    rows, cols = len(puzzle), len(puzzle[0])
    cell = 32
    margin = 18
    W = margin * 2 + cols * cell
    H = margin * 2 + rows * cell
    svg = _svg_header(W, H)

    # Cuadrícula gris
    grid_gray = '#c8c8c8'
    for i in range(rows + 1):
        y = margin + i * cell
        svg += _cage_line(margin, y, margin + cols * cell, y, color=grid_gray, sw=1.0)
    for j in range(cols + 1):
        x = margin + j * cell
        svg += _cage_line(x, margin, x, margin + rows * cell, color=grid_gray, sw=1.0)

    # Bucle solución (negro grueso), por debajo de las perlas
    if show_solution and solution_path:
        pts = [(margin + c * cell + cell / 2, margin + r * cell + cell / 2)
               for r, c in solution_path]
        path_d = (f'M {pts[0][0]:.1f} {pts[0][1]:.1f} '
                  + ' '.join(f'L {x:.1f} {y:.1f}' for x, y in pts[1:]) + ' Z')
        svg += (f'<path d="{path_d}" fill="none" stroke="{st["stroke"]}" '
                f'stroke-width="3" stroke-linejoin="round"/>\n')

    # Perlas
    for (r, c), ptype in pearls.items():
        cx = margin + c * cell + cell / 2
        cy = margin + r * cell + cell / 2
        if ptype == 'B':
            svg += (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{cell*0.30}" '
                    f'fill="{st["fill_black"]}" stroke="{st["fill_black"]}" stroke-width="1"/>\n')
        else:
            svg += (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{cell*0.30}" '
                    f'fill="#ffffff" stroke="{st["fill_black"]}" stroke-width="2.5"/>\n')

    svg += _svg_footer()
    return svg


# ─── CIRCULAR MAZE ───────────────────────────────────────────────────────────

def render_maze_circular(all_cells, sector_counts, connections, walls, solution_path,
                          style='flat', stroke_width=2.0, show_solution=False):
    if show_solution:
        steps = {}
        for i, (r, s) in enumerate(solution_path):
            steps[f'Paso {i+1}'] = f'Anillo {r}, Sector {s}'
        return render_solution_table(steps, 'Laberinto Circular SOLUCIÓN', cols=2)

    st = {**STYLES.get(style, STYLES['flat']), 'stroke_width': stroke_width}
    rings = len(sector_counts)
    ring_width = 35
    margin = 20
    R = rings * ring_width + margin
    W = H = R * 2 + margin * 2
    cx, cy = W // 2, H // 2
    svg = _svg_header(W, H)
    svg += f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="{st["fill_empty"]}" stroke="{st["stroke"]}" stroke-width="{stroke_width}"/>\n'

    conn_set = set(map(frozenset, [frozenset(c) for c in connections]))
    sol_set = set(solution_path)

    for ring in range(rings):
        sc = sector_counts[ring]
        r_inner = ring * ring_width
        r_outer = (ring + 1) * ring_width
        for s in range(sc):
            angle1 = 2 * math.pi * s / sc - math.pi/2
            angle2 = 2 * math.pi * (s+1) / sc - math.pi/2
            cell = (ring, s)
            fill = '#aaaaaa' if (show_solution and cell in sol_set) else st['fill_empty']

            # Draw sector arc
            x1_i = cx + r_inner * math.cos(angle1)
            y1_i = cy + r_inner * math.sin(angle1)
            x2_i = cx + r_inner * math.cos(angle2)
            y2_i = cy + r_inner * math.sin(angle2)
            x1_o = cx + r_outer * math.cos(angle1)
            y1_o = cy + r_outer * math.sin(angle1)
            x2_o = cx + r_outer * math.cos(angle2)
            y2_o = cy + r_outer * math.sin(angle2)

            path = (f'M {x1_i:.2f} {y1_i:.2f} '
                    f'A {r_inner} {r_inner} 0 0 1 {x2_i:.2f} {y2_i:.2f} '
                    f'L {x2_o:.2f} {y2_o:.2f} '
                    f'A {r_outer} {r_outer} 0 0 0 {x1_o:.2f} {y1_o:.2f} Z')
            svg += f'<path d="{path}" fill="{fill}" stroke="{st["stroke"]}" stroke-width="{stroke_width}"/>\n'

    svg += _svg_footer()
    return svg


# ─── SOLUCIÓN GENÉRICA EN TABLA (MUY DIFERENTE AL DISEÑO) ───────────────────

def render_solution_table(data, title='SOLUCIÓN', cols=1):
    """Renderiza solución en formato tabla clara y simple."""
    W, H = 800, 600
    svg = _svg_header(W, H)
    svg += f'<text x="400" y="30" font-family="Arial" font-size="18" font-weight="bold" text-anchor="middle">— {title} —</text>\n'

    x, y = 40, 70
    col_width = (W - 80) // cols
    line_height = 24

    if isinstance(data, dict):
        items = [(str(k), str(v)) for k, v in data.items()]
    elif isinstance(data, list):
        items = [(str(i+1), str(v)) for i, v in enumerate(data)]
    else:
        items = [(str(data))]

    for idx, (key, val) in enumerate(items):
        col = idx % cols
        row = idx // cols
        curr_x = x + col * col_width
        curr_y = y + row * line_height

        # Caja con fondo alterno
        bg = '#f5f5f5' if row % 2 == 0 else '#ffffff'
        svg += f'<rect x="{curr_x-5}" y="{curr_y-15}" width="{col_width-10}" height="20" fill="{bg}" stroke="#ddd" stroke-width="0.5"/>\n'

        svg += _text(curr_x, curr_y, f'{key}: {val}', 'Courier', 11, color='#000', anchor='start')

    svg += _svg_footer()
    return svg


# ─── CLUE SHEET ──────────────────────────────────────────────────────────────

def render_clue_sheet(across_entries, down_entries, title='CRUCIGRAMA', style='flat'):
    """Render a text clue sheet for crossword puzzles."""
    st = STYLES.get(style, STYLES['flat'])
    W, H = 500, max(400, (len(across_entries)+len(down_entries)) * 18 + 100)
    svg = _svg_header(W, H)
    svg += _text(W/2, 25, title, st['font_bold'], 16, bold=True)
    y = 55
    svg += _text(20, y, 'HORIZONTAL', st['font_bold'], 12, bold=True, anchor='start')
    y += 18
    for e in across_entries:
        line = f'{e["number"]}. {e["clue"]}'
        svg += _text(20, y, line, st['font'], 10, anchor='start')
        y += 14
    y += 8
    svg += _text(20, y, 'VERTICAL', st['font_bold'], 12, bold=True, anchor='start')
    y += 18
    for e in down_entries:
        line = f'{e["number"]}. {e["clue"]}'
        svg += _text(20, y, line, st['font'], 10, anchor='start')
        y += 14
    svg += _svg_footer()
    return svg
