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


def _svg_header(width, height, extra_attrs=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}"{extra_attrs}>\n'
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


def _cage_line(x1, y1, x2, y2, color='#888888', sw=1.0):
    """Línea gris fina para marcar jaulas de cálculo (más delgada que el borde negro)."""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{sw}"/>\n')


# ─── LABERINTOS: estilo homogéneo de paredes ────────────────────────────────
# Paredes finas negras de grosor UNIFORME en todos los laberintos (para
# armonizar la familia) y solución en rojo del mismo grosor. El Puente (weave)
# usa su propio estilo de tubo/cinta (ver render_maze_weave).
MAZE_WALL_COLOR = '#000000'
MAZE_SOLUTION_COLOR = '#e63232'
MAZE_WALL_STROKE = 2.6        # grosor único de pared para TODOS los laberintos
MAZE_SOLUTION_STROKE = 2.6    # grosor de la línea de solución (roja)
WEAVE_SOLUTION_STROKE = 4.6   # línea de solución del weave: más gruesa (tubo ancho)


def _pipe_wall(x1, y1, x2, y2, sw=MAZE_WALL_STROKE, color=MAZE_WALL_COLOR):
    """Segmento de pared: trazo fino con extremos/uniones redondeadas. Los
    extremos redondeados de segmentos contiguos se solapan en las esquinas,
    dando una malla continua sin necesidad de unir los trazos."""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{sw:.1f}" stroke-linecap="round"/>\n')


def _pipe_solution(points, sw=MAZE_SOLUTION_STROKE):
    """Línea de solución roja y fina que recorre los centros del camino."""
    pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)
    return (f'<polyline points="{pts}" fill="none" stroke="{MAZE_SOLUTION_COLOR}" '
            f'stroke-width="{sw:.1f}" stroke-linecap="round" stroke-linejoin="round"/>\n')


def _tri_edge_mid(cell_a, cell_b, cell_geom):
    """Punto medio de la arista COMPARTIDA entre dos triángulos contiguos (la
    "puerta" por la que pasa el corredor). Devuelve None si no comparten arista."""
    va, vb = cell_geom(*cell_a), cell_geom(*cell_b)
    shared = [p for p in va
              if any(abs(p[0]-q[0]) < 0.5 and abs(p[1]-q[1]) < 0.5 for q in vb)]
    if len(shared) >= 2:
        return ((shared[0][0]+shared[1][0])/2, (shared[0][1]+shared[1][1])/2)
    return None


def _tri_solution_points(path, cell_geom):
    """Puntos interiores de la línea de solución de un laberinto triangular:
    los puntos medios de las aristas compartidas a lo largo del camino. Al pasar
    por las puertas reales (y no por los centroides), la línea sigue el corredor
    de forma uniforme, sin picos. Los extremos (entrada/salida) los añade cada
    render según dónde abra su borde."""
    return [m for i in range(len(path)-1)
            if (m := _tri_edge_mid(path[i], path[i+1], cell_geom)) is not None]


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
    """Crucigrama sobre la MISMA plantilla. Puzzle: casillas blancas vacías.
    Solución: la plantilla se rellena con las palabras, en negrita."""
    st = {**STYLES.get(style, STYLES['flat']), 'stroke_width': stroke_width}
    size = len(puzzle_grid)
    cell = 36
    margin = 20
    W = margin * 2 + cell * size
    H = margin * 2 + cell * size

    svg = _svg_header(W, H)

    for r in range(size):
        for c in range(size):
            x = margin + c * cell
            y = margin + r * cell
            is_wall = puzzle_grid[r][c] is None
            if is_wall:
                # Black cell
                svg += _rect(x, y, cell, cell, st['fill_black'], st['stroke'], st['stroke_width'])
            else:
                svg += _rect(x, y, cell, cell, st['fill_empty'], st['stroke'], st['stroke_width'])
                if show_solution:
                    val = solution_grid[r][c]
                    if val:
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
    """Sopa de letras sobre la MISMA plantilla. Puzzle: todas las letras normales.
    Solución: las celdas de las palabras encontradas van en NEGRO con la letra en
    blanco; el resto de celdas (relleno) se mantiene igual."""
    st = {**STYLES.get(style, STYLES['flat']), 'stroke_width': stroke_width}
    rows = len(grid)
    cols = len(grid[0])
    cell = 30
    margin = 20
    W = margin * 2 + cell * cols
    H = margin * 2 + cell * rows

    svg = _svg_header(W, H)
    disp = grid

    # Celdas de las palabras encontradas (solo se marcan en la solución)
    sol_cells = set()
    if show_solution:
        for word, info in word_positions.items():
            for r, c in info['cells']:
                sol_cells.add((r, c))

    for r in range(rows):
        for c in range(cols):
            x = margin + c * cell
            y = margin + r * cell
            is_word_cell = (r, c) in sol_cells
            fill = st['fill_black'] if is_word_cell else st['fill_empty']
            svg += _rect(x, y, cell, cell, fill, st['stroke'], st['stroke_width'])
            ch = disp[r][c]
            if ch:
                color = '#ffffff' if is_word_cell else '#000000'
                svg += _text(x + cell/2, y + cell/2, ch.upper(),
                             st['font'], cell * 0.5, bold=is_word_cell, color=color)

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
    """Laberinto rectangular: paredes finas negras de grosor uniforme con
    uniones redondeadas. La entrada (borde izquierdo) y la salida (borde
    derecho) quedan abiertas. La solución es una línea roja fina."""
    rows = (len(grid) - 1) // 2
    cols = (len(grid[0]) - 1) // 2
    margin = 20
    W = margin * 2 + cols * cell_size
    H = margin * 2 + rows * cell_size
    svg = _svg_header(W, H)

    # Paredes verticales: grid[2r+1][2c], entre la celda (r,c-1) y (r,c).
    # (grid[...]==0 en la entrada/salida ⇒ no se dibuja pared ⇒ borde abierto.)
    for r in range(rows):
        for c in range(cols + 1):
            if grid[2*r+1][2*c] == 1:
                x = margin + c * cell_size
                y1 = margin + r * cell_size
                y2 = y1 + cell_size
                svg += _pipe_wall(x, y1, x, y2)

    # Paredes horizontales: grid[2r][2c+1], entre la celda (r-1,c) y (r,c).
    for r in range(rows + 1):
        for c in range(cols):
            if grid[2*r][2*c+1] == 1:
                y = margin + r * cell_size
                x1 = margin + c * cell_size
                x2 = x1 + cell_size
                svg += _pipe_wall(x1, y, x2, y)

    if show_solution and solution_path:
        # solution_path está en coordenadas de la cuadrícula DOBLADA (celdas y
        # puntos medios de pared alternados); cada paso equivale a media celda.
        half = cell_size / 2
        pts = [(margin + gc*half, margin + gr*half) for gr, gc in solution_path]
        svg += _pipe_solution(pts)

    svg += _svg_footer()
    return svg


# ─── MAZE (Hexagonal) ────────────────────────────────────────────────────────

# Arista i del hexágono pointy-top (entre vértice i e i+1, con vértices en
# ángulos 60·i − 30°) → dirección de brújula del vecino al otro lado.
_HEX_EDGE_DIR = {0: 'E', 1: 'SE', 2: 'SW', 3: 'W', 4: 'NW', 5: 'NE'}


def _hex_edge_neighbor(row, col, direction):
    """Vecino offset "odd-r" en la dirección de brújula dada."""
    even = (row % 2 == 0)
    return {
        'E':  (row, col+1),
        'W':  (row, col-1),
        'NW': (row-1, col-1) if even else (row-1, col),
        'NE': (row-1, col)   if even else (row-1, col+1),
        'SW': (row+1, col-1) if even else (row+1, col),
        'SE': (row+1, col)   if even else (row+1, col+1),
    }[direction]


def render_maze_hex(cells, connections, walls, solution_path, rows, cols,
                    style='flat', stroke_width=2.0, show_solution=False):
    """Laberinto hexagonal de contorno RECTANGULAR (coordenadas offset odd-r).
    Solo se dibujan las paredes reales, con grosor uniforme. La entrada (borde
    izquierdo de la celda 0,0) y la salida (borde derecho de la última celda)
    quedan abiertas. La solución es una línea roja fina por los centros."""
    hex_size = 16  # radio
    margin = 24
    conn_set = set(connections)
    cell_set = set(cells)
    w = math.sqrt(3) * hex_size          # ancho de celda

    def hex_center(row, col):
        cx = margin + col * w + (row % 2) * (w / 2) + w / 2
        cy = margin + row * 1.5 * hex_size + hex_size
        return cx, cy

    def hex_points(cx, cy, size):
        return [(cx + size * math.cos(math.pi/180 * (60*i - 30)),
                 cy + size * math.sin(math.pi/180 * (60*i - 30))) for i in range(6)]

    centers = {cell: hex_center(*cell) for cell in cells}
    xs = [c[0] for c in centers.values()]
    ys = [c[1] for c in centers.values()]
    W = int(max(xs) + w + margin)
    H = int(max(ys) + hex_size + margin)
    svg = _svg_header(W, H)

    # Aperturas de entrada/salida (arista de borde que se deja sin dibujar).
    entrance = ((0, 0), 'W')
    exit_ = ((rows-1, cols-1), 'E')

    for cell in cells:
        cx, cy = centers[cell]
        pts = hex_points(cx, cy, hex_size)
        for i in range(6):
            direction = _HEX_EDGE_DIR[i]
            neighbor = _hex_edge_neighbor(cell[0], cell[1], direction)
            is_open = neighbor in cell_set and frozenset([cell, neighbor]) in conn_set
            if is_open:
                continue
            if (cell, direction) == entrance or (cell, direction) == exit_:
                continue  # apertura de entrada/salida
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % 6]
            svg += _pipe_wall(x1, y1, x2, y2)

    if show_solution and solution_path:
        pts = [centers[cell] for cell in solution_path]
        svg += _pipe_solution(pts)

    svg += _svg_footer()
    return svg


# ─── MAZE (Triangular) ───────────────────────────────────────────────────────

def render_maze_tri(cells, connections, walls, solution_path, size, _unused=None,
                    style='flat', stroke_width=2.0, show_solution=False):
    """Laberinto TRIANGULAR con forma de triángulo equilátero (fila r con 2·r+1
    celdas ▲/▽). Solo se dibujan las paredes reales, con grosor uniforme. La
    entrada y la salida se abren en las dos esquinas inferiores de la base. La
    solución es una línea roja fina que sigue el corredor por las puertas
    (puntos medios de las aristas compartidas)."""
    b = 22.0                 # base de cada triángulo pequeño (más estrecho: caminos
    unit = b / 2             # menos anchos, en línea con los otros laberintos)
    h = b * math.sqrt(3) / 2
    margin = 20
    W = margin * 2 + int(size * b)
    H = margin * 2 + int(size * h)
    svg = _svg_header(W, H)

    conn_set = set(connections)

    # Celdas de entrada/salida (extremos de la solución): se abre su base.
    open_base = set()
    if solution_path:
        open_base = {solution_path[0], solution_path[-1]}

    def cell_geom(r, c):
        # x0 = borde izquierdo de la celda; la fila r se centra en el triángulo.
        x0 = margin + (size - 1 - r) * unit + c * unit
        y_top = margin + r * h
        y_bot = y_top + h
        if c % 2 == 0:   # ▲ up: base abajo (A,B), ápice arriba (C)
            return (x0, y_bot), (x0 + b, y_bot), (x0 + unit, y_top)
        else:            # ▽ down: base arriba (A,B), ápice abajo (C)
            return (x0, y_top), (x0 + b, y_top), (x0 + unit, y_bot)


    for r, c in cells:
        A, B, C = cell_geom(r, c)
        up = c % 2 == 0

        # Arista izquierda (A-C): borde en c==0, o pared interior con (r,c-1).
        if c == 0 or frozenset([(r, c), (r, c-1)]) not in conn_set:
            svg += _pipe_wall(A[0], A[1], C[0], C[1])
        # Arista derecha (B-C): solo se dibuja como borde derecho (c==2r); las
        # interiores las cubre la arista izquierda de la celda siguiente.
        if c == 2*r:
            svg += _pipe_wall(B[0], B[1], C[0], C[1])
        # Base (A-B): solo desde celdas ▲ (la comparten con la ▽ de abajo). Las
        # ▽ tienen su base arriba, cubierta por la ▲ superior.
        if up:
            if r == size - 1:
                if (r, c) not in open_base:      # borde inferior (abre entrada/salida)
                    svg += _pipe_wall(A[0], A[1], B[0], B[1])
            else:
                below = (r+1, c+1)
                if frozenset([(r, c), below]) not in conn_set:
                    svg += _pipe_wall(A[0], A[1], B[0], B[1])

    if show_solution and solution_path:
        pts = _tri_solution_points(solution_path, cell_geom)
        # Extremos: la entrada/salida abren la BASE (A-B) de las esquinas inferiores;
        # se ancla la línea en el medio de esa base y se prolonga hacia abajo.
        A0, B0, _ = cell_geom(*solution_path[0])
        m0 = ((A0[0]+B0[0])/2, (A0[1]+B0[1])/2)
        An, Bn, _ = cell_geom(*solution_path[-1])
        mn = ((An[0]+Bn[0])/2, (An[1]+Bn[1])/2)
        pts = [(m0[0], m0[1] + h*0.5), m0] + pts + [mn, (mn[0], mn[1] + h*0.5)]
        svg += _pipe_solution(pts)

    svg += _svg_footer()
    return svg


# ─── MAZE (Triangular de contorno cuadrado) ──────────────────────────────────

def render_maze_tri_sq(cells, connections, walls, solution_path, rows, cols,
                       style='flat', stroke_width=2.0, show_solution=False):
    """Laberinto TRIANGULAR de contorno RECTANGULAR/cuadrado (rejilla rows×cols
    de triángulos ▲/▽). Solo se dibujan las paredes reales, con grosor uniforme;
    entrada arriba-izquierda y salida abajo-derecha abiertas. Solución en rojo."""
    b = 20.0                 # base de cada triángulo
    unit = b / 2
    h = b * math.sqrt(3) / 2
    margin = 18
    W = margin * 2 + int((cols + 1) * unit)
    H = margin * 2 + int(rows * h)
    svg = _svg_header(W, H)

    conn_set = set(connections)
    open_edges = set()
    if solution_path:
        open_edges = {solution_path[0], solution_path[-1]}

    def cell_geom(r, c):
        x0 = margin + c * unit
        y_top = margin + r * h
        y_bot = y_top + h
        if (r + c) % 2 == 0:   # ▲ up: base abajo
            return (x0, y_bot), (x0 + b, y_bot), (x0 + unit, y_top)
        else:                  # ▽ down: base arriba
            return (x0, y_top), (x0 + b, y_top), (x0 + unit, y_bot)


    for r, c in cells:
        A, B, C = cell_geom(r, c)
        up = (r + c) % 2 == 0

        # Arista izquierda (A-C): borde en c==0 (entrada), o pared con (r,c-1).
        if c == 0 or frozenset([(r, c), (r, c-1)]) not in conn_set:
            if not (c == 0 and (r, c) in open_edges):
                svg += _pipe_wall(A[0], A[1], C[0], C[1])
        # Arista derecha (B-C): solo borde derecho (c==cols-1, salida).
        if c == cols - 1:
            if (r, c) not in open_edges:
                svg += _pipe_wall(B[0], B[1], C[0], C[1])
        # Base (A-B): las ▲ la comparten con la ▽ de abajo; las ▽ solo dibujan
        # su base (arriba) cuando son borde superior (r==0).
        if up:
            if r == rows - 1:
                svg += _pipe_wall(A[0], A[1], B[0], B[1])   # borde inferior
            elif frozenset([(r, c), (r+1, c)]) not in conn_set:
                svg += _pipe_wall(A[0], A[1], B[0], B[1])
        elif r == 0:
            svg += _pipe_wall(A[0], A[1], B[0], B[1])       # borde superior

    if show_solution and solution_path:
        pts = _tri_solution_points(solution_path, cell_geom)
        # Extremos: entrada por el borde IZQUIERDO (arista A-C) de la primera celda,
        # salida por el borde DERECHO (arista B-C) de la última; se prolonga en horizontal.
        A0, _, C0 = cell_geom(*solution_path[0])
        m0 = ((A0[0]+C0[0])/2, (A0[1]+C0[1])/2)
        _, Bn, Cn = cell_geom(*solution_path[-1])
        mn = ((Bn[0]+Cn[0])/2, (Bn[1]+Cn[1])/2)
        pts = [(m0[0] - unit, m0[1]), m0] + pts + [mn, (mn[0] + unit, mn[1])]
        svg += _pipe_solution(pts)

    svg += _svg_footer()
    return svg


# ─── MAZE (Puentes / Weave) — renderizado por CORREDORES en dos capas ────────
# El estilo real: el CAMINO es un tubo blanco con contorno negro. Se dibuja por
# capas (algoritmo del pintor): primero el plano inferior (pasillos normales +
# la dirección "subterránea" de cada puente), luego el plano superior (la
# dirección "elevada" de los puentes), que corta visualmente al de abajo.
# `corner='sharp'` da esquinas rectas (Bridge); `corner='round'` da curvas de
# 90° (Round Bridge). Las paredes son el negro que queda entre pasillos.

def _corridor_paths(cx, cy, dirs, r, tip=0.0):
    """Segmentos SVG (d-strings) del pasillo de una celda hacia sus direcciones
    conectadas. En 'round' los giros salen curvos SOLO por el `stroke-linejoin
    ="round"` nativo de SVG sobre el mismo trazado recto que 'sharp' (ver
    `join` en `render_maze_weave`) — NO se construyen arcos ('A') a mano.
    Un arco manual con radio r=S/2 y un tubo casi tan ancho como r hace que el
    borde INTERIOR de la curva casi toque el centro de curvatura (radio
    interior ≈ 0), y el trazo degenera en una "coma" rota en vez de una curva
    limpia. El linejoin nativo del navegador no tiene ese problema."""
    ends = {'N': (cx, cy - r), 'S': (cx, cy + r),
            'W': (cx - r, cy), 'E': (cx + r, cy)}
    opp = {'N': 'S', 'S': 'N', 'W': 'E', 'E': 'W'}
    dset = set(dirs)
    if len(dset) == 1:
        # Callejón sin salida: el tubo entra por el borde conectado, cruza el
        # centro y llena la celda hasta cerca de la pared muerta (no un muñón
        # que corta en el centro sin sentido).
        d = next(iter(dset))
        ex, ey = ends[d]
        ox, oy = ends[opp[d]]
        fx, fy = cx + (ox - cx) * 0.55, cy + (oy - cy) * 0.55
        if tip:
            # El trazo NEGRO se alarga justo el grosor del muro para cerrar la
            # punta del callejón (con 'square' se desbordaría medio grosor y
            # dejaría un pegote negro).
            ux, uy = ox - cx, oy - cy
            n = (ux * ux + uy * uy) ** 0.5 or 1.0
            fx += ux / n * tip
            fy += uy / n * tip
        return [f'M {ex:.1f} {ey:.1f} L {fx:.1f} {fy:.1f}']
    # Trazos CONECTADOS (no radios sueltos): así el 'miter'/'round' cierra las
    # esquinas sin muescas y no quedan extremos encimados.
    paths = []
    rest = set(dset)
    for a, b in (('N', 'S'), ('W', 'E')):
        if a in rest and b in rest:
            (ax, ay), (bx, by) = ends[a], ends[b]
            paths.append(f'M {ax:.1f} {ay:.1f} L {cx:.1f} {cy:.1f} L {bx:.1f} {by:.1f}')
            rest -= {a, b}
    if len(rest) == 2:                       # giro en L: un solo trazo con vértice
        a, b = tuple(rest)
        (ax, ay), (bx, by) = ends[a], ends[b]
        paths.append(f'M {ax:.1f} {ay:.1f} L {cx:.1f} {cy:.1f} L {bx:.1f} {by:.1f}')
        rest.clear()
    for d in rest:                           # ramal suelto (T): del centro al borde
        ex, ey = ends[d]
        paths.append(f'M {cx:.1f} {cy:.1f} L {ex:.1f} {ey:.1f}')
    return paths


def _weave_bridge_groups(bridges):
    """Agrupa puentes CONTIGUOS con el mismo eje de puente elevado (misma fila
    para elevado vertical, misma columna para elevado horizontal). Sin agrupar,
    el hueco de pared entre dos puentes vecinos deja asomar el borde del
    pasillo de abajo: una 'ventanita' que rompe el efecto de paso elevado
    limpio. Devuelve [(axis, [celdas ordenadas]), ...]."""
    used = set()
    groups = []
    for cell, axis in bridges.items():
        if cell in used:
            continue
        r0, c0 = cell
        if axis == 'h':            # elevado vertical: agrupar por FILA
            xs = [c0]
            c = c0 + 1
            while (r0, c) in bridges and bridges[(r0, c)] == 'h':
                xs.append(c); c += 1
            c = c0 - 1
            while (r0, c) in bridges and bridges[(r0, c)] == 'h':
                xs.append(c); c -= 1
            xs.sort()
            member_cells = [(r0, x) for x in xs]
        else:                        # elevado horizontal: agrupar por COLUMNA
            ys = [r0]
            rr = r0 + 1
            while (rr, c0) in bridges and bridges[(rr, c0)] == 'v':
                ys.append(rr); rr += 1
            rr = r0 - 1
            while (rr, c0) in bridges and bridges[(rr, c0)] == 'v':
                ys.append(rr); rr -= 1
            ys.sort()
            member_cells = [(y, c0) for y in ys]
        used.update(member_cells)
        groups.append((axis, member_cells))
    return groups


def _weave_solution_layers(solution_path, center, r):
    """Separa la ruta de solución en tramos de SUELO (pasos normales, 1 celda)
    y tramos de PUENTE (saltos de 2 celdas, usan el paso elevado). Los de suelo
    se dibujan ANTES de los puentes, para que un puente que cruce por encima
    los oculte (no debe tocar/verse sobre otro camino); los de puente se
    dibujan DESPUÉS, sobre el tubo elevado. Devuelve [(tag, [puntos]), ...]."""
    segments = []
    run = [solution_path[0]]
    for i in range(len(solution_path) - 1):
        a, b = solution_path[i], solution_path[i + 1]
        if abs(a[0]-b[0]) + abs(a[1]-b[1]) == 2:   # salto elevado
            if len(run) > 1:
                segments.append(('ground', run))
            segments.append(('elevated', [a, b]))
            run = [b]
        else:
            run.append(b)
    if len(run) > 1:
        segments.append(('ground', run))

    pt_segments = [(tag, [center(c) for c in cells]) for tag, cells in segments]
    if pt_segments:
        pts0 = pt_segments[0][1]
        pts0.insert(0, (pts0[0][0] - r, pts0[0][1]))
        ptsN = pt_segments[-1][1]
        ptsN.append((ptsN[-1][0] + r, ptsN[-1][1]))
    return pt_segments


def render_maze_weave(cells, connections, bridges, solution_path, rows, cols,
                      style='flat', stroke_width=2.0, show_solution=False,
                      cell_size=26, corner='sharp'):
    """Laberinto de puentes (weave) ortogonal renderizado por corredores en dos
    capas. `corner='sharp'` = Bridge (esquinas rectas); `corner='round'` =
    Round Bridge (curvas de 90°). La solución es una línea roja fina."""
    margin = 18
    S = cell_size
    r = S / 2
    # Doble trazo compuesto (algoritmo del pintor): el NEGRO ocupa la celda
    # completa (grosor S) y el BLANCO va encima (grosor S·0.65). Así el negro de
    # celdas contiguas se funde en una masa y las PAREDES son las franjas negras
    # (≈ S·0.175 por lado) que quedan entre los pasillos blancos.
    outer = S * 0.90     # ancho del TUBO (90%: solo ~10% de separación entre tubos)
    inner = outer - 6.0  # relleno blanco; deja ~3px de contorno negro por lado
    W = margin * 2 + cols * S
    H = margin * 2 + rows * S
    # 'sharp' es 100% ortogonal (sin curvas): shape-rendering="crispEdges" apaga
    # el antialiasing y fuerza los bordes al píxel exacto. Sin esto, dos trazos
    # del mismo color que se TOCAN en un borde matemático (p.ej. el fondo de un
    # grupo de puentes con el tubo blanco de cada uno, o dos celdas contiguas)
    # dejan una costura gris translúcida ahí donde el antialiasing de cada
    # trazo se difumina por separado contra el fondo en vez de fundirse entre
    # sí. 'round' conserva el antialiasing (tiene arcos; crispEdges los vería
    # dentados) — ese estilo se revisa aparte.
    extra = ' shape-rendering="crispEdges"' if corner == 'sharp' else ''
    svg = _svg_header(W, H, extra)

    conn_set = set(connections)

    def center(rc):
        rr, cc = rc
        return margin + cc*S + r, margin + rr*S + r

    # Direcciones de conexión de distancia 1 (excluye los saltos de puente,
    # que son conexiones de distancia 2 y se dibujan aparte en la capa superior).
    DIRS = {'N': (-1, 0), 'S': (1, 0), 'W': (0, -1), 'E': (0, 1)}

    # Los extremos del puente (p1/p2) llevan su pasillo HACIA la celda saltada en
    # la capa inferior, para que se una con 'miter' al resto de sus pasillos. Si
    # se dibujara como una banda de p1 a p2 en la capa superior, esa banda taparía
    # los otros pasillos de p1/p2 y rompería sus conexiones.
    extra_dirs = {}
    for (br, bc), axis in bridges.items():
        if axis == 'h':                    # bajo horizontal ⇒ elevado vertical
            extra_dirs.setdefault((br-1, bc), []).append('S')
            extra_dirs.setdefault((br+1, bc), []).append('N')
        else:                              # bajo vertical ⇒ elevado horizontal
            extra_dirs.setdefault((br, bc-1), []).append('E')
            extra_dirs.setdefault((br, bc+1), []).append('W')

    def cell_dirs(cell):
        rr, cc = cell
        ds = [d for d, (dr, dc) in DIRS.items()
              if frozenset([cell, (rr+dr, cc+dc)]) in conn_set]
        ds += extra_dirs.get(cell, [])
        if cell == (0, 0):
            ds.append('W')                 # entrada (abertura en el borde izq.)
        if cell == (rows-1, cols-1):
            ds.append('E')                 # salida (abertura en el borde der.)
        return ds

    # Dos versiones de la capa inferior: la NEGRA alarga la punta de los callejones
    # el grosor del muro (para cerrarlos); la BLANCA termina exacta.
    wall = (outer - inner) / 2.0
    layer0_k, layer0_w = [], []
    for cell in cells:
        cx, cy = center(cell)
        ds = cell_dirs(cell)
        layer0_k += _corridor_paths(cx, cy, ds, r, tip=wall)
        layer0_w += _corridor_paths(cx, cy, ds, r)


    # Capa superior: SOLO el tramo que cruza la celda saltada (de borde a borde).
    layer1 = []
    for (br, bc), axis in bridges.items():
        bx, by = center((br, bc))
        if axis == 'h':                    # bajo horizontal ⇒ elevado vertical
            layer1.append(f'M {bx:.1f} {by-r:.1f} L {bx:.1f} {by+r:.1f}')
        else:                              # bajo vertical ⇒ elevado horizontal
            layer1.append(f'M {bx-r:.1f} {by:.1f} L {bx+r:.1f} {by:.1f}')

    # Fondo de cada GRUPO de puentes contiguos: una franja NEGRA continua del
    # ancho completo de celda (S, sin el 10% de separación de los tubos
    # normales) que cubre TODO el tramo. Sin esto, el pasillo de abajo asoma
    # su borde por el hueco de pared entre dos puentes vecinos.
    masks = []
    for axis, member_cells in _weave_bridge_groups(bridges):
        fx, fy = center(member_cells[0])
        lx, ly = center(member_cells[-1])
        if axis == 'h':
            masks.append(f'M {fx-r:.1f} {fy:.1f} L {lx+r:.1f} {fy:.1f}')
        else:
            masks.append(f'M {fx:.1f} {fy-r:.1f} L {fx:.1f} {ly+r:.1f}')

    join = 'round' if corner == 'round' else 'miter'

    def stroke(paths, width, color, cap, sw=None):
        if not paths:
            return ''
        d = ' '.join(paths)
        return (f'<path d="{d}" fill="none" stroke="{color}" '
                f'stroke-width="{width:.1f}" stroke-linecap="{cap}" '
                f'stroke-linejoin="{join}"/>\n')

    if show_solution and solution_path:
        segs = _weave_solution_layers(solution_path, center, r)
        ground_pts = [pts for tag, pts in segs if tag == 'ground']
        elevated_pts = [pts for tag, pts in segs if tag == 'elevated']
    else:
        ground_pts, elevated_pts = [], []

    # Capa 1 (inferior): todo el negro (muros) antes que todo el blanco (camino).
    svg += stroke(layer0_k, outer, MAZE_WALL_COLOR, 'butt')   # muros
    svg += stroke(layer0_w, inner, '#ffffff', 'butt')         # camino libre
    # Solución de SUELO: se dibuja aquí (antes de los puentes) para que un
    # puente que cruce por encima la oculte, en vez de montarse sobre él.
    for pts in ground_pts:
        svg += _pipe_solution(pts, sw=WEAVE_SOLUTION_STROKE)
    # Capa 2 (superior): pasos ELEVADOS. El fondo negro del grupo tapa TODO el
    # tramo (incluye lo que asomaba en los huecos de pared); encima, el tubo
    # blanco de cada puente individual (más angosto, deja ver el muro del
    # fondo negro entre puentes vecinos).
    svg += stroke(masks, S, MAZE_WALL_COLOR, 'butt')
    svg += stroke(layer1, inner, '#ffffff', 'butt')
    # Solución ELEVADA: se dibuja al final, sobre el tubo del puente.
    for pts in elevated_pts:
        svg += _pipe_solution(pts, sw=WEAVE_SOLUTION_STROKE)

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
            svg += _text(x, y, _ineq_symbol(op, vertical=False), st['font'], sym_size, bold=False)
        else:  # vertical: (r1,c1) es la celda de ARRIBA
            x = margin + c1 * (cell + gap) + cell / 2
            y = margin + r1 * (cell + gap) + cell + gap / 2
            svg += _text(x, y, _ineq_symbol(op, vertical=True), st['font'], sym_size, bold=False)

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

def _pipe_arc(cx, cy, r, a1, a2, sw=MAZE_WALL_STROKE):
    """Arco de pared: mismo trazo fino con extremos redondeados que
    `_pipe_wall`, pero curvo (para los anillos del laberinto circular)."""
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    x2, y2 = cx + r * math.cos(a2), cy + r * math.sin(a2)
    return (f'<path d="M {x1:.2f} {y1:.2f} A {r:.2f} {r:.2f} 0 0 1 {x2:.2f} {y2:.2f}" '
            f'fill="none" stroke="{MAZE_WALL_COLOR}" stroke-width="{sw:.1f}" '
            f'stroke-linecap="round"/>\n')


CIRCULAR_RING_WIDTH = 24   # distancia entre anillos (compacto y homogéneo)


def render_maze_circular(all_cells, sector_counts, connections, walls, solution_path,
                          style='flat', stroke_width=2.0, show_solution=False):
    """Laberinto circular polar. Solo se dibujan las paredes reales (arcos y
    radios sin conexión). La entrada y la salida se abren en el borde exterior
    en sectores opuestos, de modo que el camino atraviesa todo el disco. La
    solución es una línea roja fina por los centros del camino."""
    rings = len(sector_counts)
    ring_width = CIRCULAR_RING_WIDTH
    margin = 20
    R = rings * ring_width + margin
    W = H = R * 2 + margin * 2
    cx, cy = W // 2, H // 2
    svg = _svg_header(W, H)

    conn_set = set(connections)
    # Sectores de entrada/salida (extremos de la solución, sobre el anillo
    # exterior): ahí NO se dibuja el arco de borde ⇒ apertura que atraviesa.
    open_outer = set()
    if solution_path:
        for cell in (solution_path[0], solution_path[-1]):
            if cell[0] == rings - 1:
                open_outer.add(cell[1])

    def sector_angles(ring, s):
        sc = sector_counts[ring]
        a1 = 2 * math.pi * s / sc - math.pi/2
        a2 = 2 * math.pi * (s+1) / sc - math.pi/2
        return a1, a2

    for ring in range(rings):
        sc = sector_counts[ring]
        r_inner = ring * ring_width
        r_outer = (ring + 1) * ring_width
        for s in range(sc):
            angle1, angle2 = sector_angles(ring, s)
            cell = (ring, s)

            # Radial: pared hacia el sector siguiente (sentido horario)
            next_cell = (ring, (s + 1) % sc)
            if frozenset([cell, next_cell]) not in conn_set:
                x1 = cx + r_inner * math.cos(angle2)
                y1 = cy + r_inner * math.sin(angle2)
                x2 = cx + r_outer * math.cos(angle2)
                y2 = cy + r_outer * math.sin(angle2)
                svg += _pipe_wall(x1, y1, x2, y2)

            # Arco interior: pared hacia el anillo interno (si no hay conexión)
            if ring > 0:
                inner_sc = sector_counts[ring - 1]
                k = sc // inner_sc
                inner_cell = (ring - 1, s // k)
                if frozenset([cell, inner_cell]) not in conn_set:
                    svg += _pipe_arc(cx, cy, r_inner, angle1, angle2)

            # Borde exterior (frontera), abierto en los sectores de entrada/salida
            if ring == rings - 1 and s not in open_outer:
                svg += _pipe_arc(cx, cy, r_outer, angle1, angle2)

    if show_solution and solution_path:
        def cell_center(ring, s):
            a1, a2 = sector_angles(ring, s)
            amid = (a1 + a2) / 2
            rmid = ring * ring_width + ring_width / 2
            return cx + rmid * math.cos(amid), cy + rmid * math.sin(amid)

        pts = [cell_center(*c) for c in solution_path]
        # Prolongar los extremos hasta cruzar el borde (efecto entrada/salida).
        if solution_path[0][0] == rings - 1:
            a1, a2 = sector_angles(*solution_path[0])
            amid = (a1 + a2) / 2
            pts.insert(0, (cx + R * math.cos(amid), cy + R * math.sin(amid)))
        if solution_path[-1][0] == rings - 1:
            a1, a2 = sector_angles(*solution_path[-1])
            amid = (a1 + a2) / 2
            pts.append((cx + R * math.cos(amid), cy + R * math.sin(amid)))
        svg += _pipe_solution(pts)

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
