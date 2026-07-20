"""
Red de seguridad para la familia de Laberintos (Fase F).
"""
import xml.etree.ElementTree as ET
from collections import deque

import pytest
from puzzles import maze as M
from puzzles import renderer as R


def _reachable_cells(grid, rows, cols):
    """BFS sobre el grid doblado (2*rows+1 x 2*cols+1) partiendo de la celda (0,0)."""
    seen = {(1, 1)}
    stack = [(1, 1)]
    while stack:
        r, c = stack.pop()
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 2*rows+1 and 0 <= nc < 2*cols+1 and grid[nr][nc] == 0 and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))
    return seen


@pytest.mark.parametrize('difficulty', ['kids', 'easy', 'medium', 'hard'])
def test_rect_maze_conectividad(difficulty):
    rows, cols = 10, 10
    grid, sol_path = M.generate_rectangular_maze(rows, cols, difficulty)

    # Todas las celdas deben ser alcanzables entre sí (sin importar el trenzado).
    reached = _reachable_cells(grid, rows, cols)
    all_cells = {(2*r+1, 2*c+1) for r in range(rows) for c in range(cols)}
    assert all_cells.issubset(reached)

    # Existe un camino de la entrada a la salida.
    assert sol_path
    assert sol_path[0] == (1, 0)
    assert sol_path[-1] == (2*rows-1, 2*cols)


def test_rect_maze_trenzado_reduce_callejones():
    rows, cols = 12, 12
    grid_hard, _ = M.generate_rectangular_maze(rows, cols, 'hard')
    grid_kids, _ = M.generate_rectangular_maze(rows, cols, 'kids')

    def count_dead_ends(grid):
        dead = 0
        for r in range(rows):
            for c in range(cols):
                open_sides = 0
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    wr, wc = 2*r+1+dr, 2*c+1+dc
                    if 0 <= wr < len(grid) and 0 <= wc < len(grid[0]) and grid[wr][wc] == 0:
                        open_sides += 1
                if open_sides == 1:
                    dead += 1
        return dead

    # kids (braid alto) debe tener notablemente menos callejones sin salida que hard.
    assert count_dead_ends(grid_kids) < count_dead_ends(grid_hard)


def test_rect_maze_dificultad_escala_con_ruta():
    """La dificultad no es solo el tamaño de la plantilla: a más difícil, la
    ruta correcta debe recorrer una fracción MAYOR del tablero (más cruces de
    tablero, no solo más callejones). Se promedian varias muestras porque la
    generación es aleatoria; los rangos no deben solaparse entre niveles."""
    rows, cols = 12, 12

    def avg_route(diff, n=6):
        vals = []
        for _ in range(n):
            grid, sol = M.generate_rectangular_maze(rows, cols, diff)
            vals.append(sum(1 for r, c in sol if r % 2 == 1 and c % 2 == 1) / (rows * cols))
        return sum(vals) / n

    r_kids, r_easy, r_medium, r_hard = (avg_route(d) for d in ('kids', 'easy', 'medium', 'hard'))
    assert r_kids < r_easy < r_medium < r_hard


def test_rect_maze_render_svg():
    grid, sol_path = M.generate_rectangular_maze(8, 8, 'medium')
    puzzle_svg = R.render_maze_rect(grid, sol_path, 'flat', 2.0, False, 20)
    solution_svg = R.render_maze_rect(grid, sol_path, 'flat', 2.0, True, 20)
    ET.fromstring(puzzle_svg)
    ET.fromstring(solution_svg)

    # El puzzle no debe mostrar la línea de solución; la solución sí.
    assert '<polyline' not in puzzle_svg
    assert '<polyline' in solution_svg


# ─── HEXAGONAL (coords axiales, Kruskal) ─────────────────────────────────────

@pytest.mark.parametrize('difficulty', ['kids', 'easy', 'medium', 'hard'])
def test_hex_maze_conectividad(difficulty):
    rows, cols = 6, 8
    cells, connections, walls, sol_path = M.generate_hexagonal_maze(rows, cols, difficulty)
    conn_set = set(connections)
    cell_set = set(cells)

    # Contorno rectangular: rows·cols celdas offset (row, col).
    assert cell_set == {(r, c) for r in range(rows) for c in range(cols)}

    # Todas las celdas deben quedar conectadas entre sí (BFS desde (0,0)).
    seen = {(0, 0)}
    stack = [(0, 0)]
    while stack:
        cell = stack.pop()
        for n in M.hex_offset_neighbors(*cell):
            if n in cell_set and n not in seen and frozenset([cell, n]) in conn_set:
                seen.add(n)
                stack.append(n)
    assert seen == cell_set

    assert sol_path
    assert sol_path[0] == (0, 0)
    assert sol_path[-1] == (rows - 1, cols - 1)


def test_hex_maze_trenzado_reduce_callejones():
    rows, cols = 8, 10

    def count_dead_ends(cells, connections):
        cell_set = set(cells)
        conn_set = set(connections)
        dead = 0
        for cell in cells:
            open_sides = sum(1 for n in M.hex_offset_neighbors(*cell)
                              if n in cell_set and frozenset([cell, n]) in conn_set)
            if open_sides == 1:
                dead += 1
        return dead

    cells_h, conn_h, _, _ = M.generate_hexagonal_maze(rows, cols, 'hard')
    cells_k, conn_k, _, _ = M.generate_hexagonal_maze(rows, cols, 'kids')
    assert count_dead_ends(cells_k, conn_k) < count_dead_ends(cells_h, conn_h)


def test_hex_maze_dificultad_escala_con_ruta():
    rows, cols = 10, 10

    def avg_route(diff, n=6):
        vals = []
        for _ in range(n):
            cells, _, _, sol = M.generate_hexagonal_maze(rows, cols, diff)
            vals.append(len(sol) / len(cells))
        return sum(vals) / n

    r_kids, r_easy, r_medium, r_hard = (avg_route(d) for d in ('kids', 'easy', 'medium', 'hard'))
    assert r_kids < r_easy < r_medium < r_hard


def test_hex_maze_render_svg():
    cells, connections, walls, sol_path = M.generate_hexagonal_maze(5, 6, 'medium')
    puzzle_svg = R.render_maze_hex(cells, connections, walls, sol_path, 5, 6, 'flat', 1.5, False)
    solution_svg = R.render_maze_hex(cells, connections, walls, sol_path, 5, 6, 'flat', 1.5, True)
    ET.fromstring(puzzle_svg)
    ET.fromstring(solution_svg)
    assert '<polyline' not in puzzle_svg
    assert '<polyline' in solution_svg


# ─── CIRCULAR (subdivisión de anillos, Prim) ─────────────────────────────────

def _circ_neighbors(rings, sector_counts, r, s):
    nbrs = []
    sc = sector_counts[r]
    nbrs.append((r, (s-1) % sc))
    nbrs.append((r, (s+1) % sc))
    if r > 0:
        inner_sc = sector_counts[r-1]
        k = sc // inner_sc
        nbrs.append((r-1, s // k))
    if r < rings - 1:
        outer_sc = sector_counts[r+1]
        k = outer_sc // sc
        nbrs.extend((r+1, s*k+i) for i in range(k))
    return nbrs


def test_circular_maze_subdivision_crece():
    cells, sector_counts, connections, walls, sol_path = M.generate_circular_maze(6, difficulty='medium')
    # El número de sectores no puede DISMINUIR hacia afuera, y debe crecer en algún punto.
    assert all(sector_counts[i] <= sector_counts[i+1] for i in range(len(sector_counts)-1))
    assert sector_counts[-1] > sector_counts[0]


@pytest.mark.parametrize('difficulty', ['kids', 'easy', 'medium', 'hard'])
def test_circular_maze_conectividad(difficulty):
    rings = 6
    cells, sector_counts, connections, walls, sol_path = M.generate_circular_maze(rings, difficulty=difficulty)
    conn_set = set(connections)
    cell_set = set(cells)

    seen = {(0, 0)}
    stack = [(0, 0)]
    while stack:
        r, s = stack.pop()
        for n in _circ_neighbors(rings, sector_counts, r, s):
            if n in cell_set and n not in seen and frozenset([(r, s), n]) in conn_set:
                seen.add(n)
                stack.append(n)
    assert seen == cell_set

    # La solución entra y sale por el ANILLO EXTERIOR en sectores opuestos.
    assert sol_path
    outer = rings - 1
    sc_outer = sector_counts[outer]
    assert sol_path[0] == (outer, 0)
    assert sol_path[-1] == (outer, sc_outer // 2)


def test_circular_maze_trenzado_reduce_callejones():
    rings = 6

    def count_dead_ends(cells, sector_counts, connections):
        conn_set = set(connections)
        cell_set = set(cells)
        dead = 0
        for r, s in cells:
            open_sides = sum(1 for n in _circ_neighbors(rings, sector_counts, r, s)
                              if n in cell_set and frozenset([(r, s), n]) in conn_set)
            if open_sides == 1:
                dead += 1
        return dead

    cells_h, sc_h, conn_h, _, _ = M.generate_circular_maze(rings, difficulty='hard')
    cells_k, sc_k, conn_k, _, _ = M.generate_circular_maze(rings, difficulty='kids')
    assert count_dead_ends(cells_k, sc_k, conn_k) < count_dead_ends(cells_h, sc_h, conn_h)


def test_circular_maze_dificultad_escala_con_ruta():
    rings = 6

    def avg_route(diff, n=6):
        vals = []
        for _ in range(n):
            cells, _, _, _, sol = M.generate_circular_maze(rings, difficulty=diff)
            vals.append(len(sol) / len(cells))
        return sum(vals) / n

    r_kids, r_easy, r_medium, r_hard = (avg_route(d) for d in ('kids', 'easy', 'medium', 'hard'))
    assert r_kids < r_easy < r_medium < r_hard


def test_circular_maze_render_svg():
    cells, sector_counts, connections, walls, sol_path = M.generate_circular_maze(5, difficulty='medium')
    puzzle_svg = R.render_maze_circular(cells, sector_counts, connections, walls, sol_path, 'flat', 1.5, False)
    solution_svg = R.render_maze_circular(cells, sector_counts, connections, walls, sol_path, 'flat', 1.5, True)
    ET.fromstring(puzzle_svg)
    ET.fromstring(solution_svg)
    assert '<polyline' not in puzzle_svg
    assert '<polyline' in solution_svg


# ─── TRIANGULAR (triángulo equilátero, Aldous-Broder) ────────────────────────

@pytest.mark.parametrize('difficulty', ['kids', 'easy', 'medium', 'hard'])
def test_tri_maze_conectividad(difficulty):
    size = 10
    cells, connections, walls, sol_path, sz, _ = M.generate_triangular_maze(size, difficulty)
    conn_set = set(connections)
    cell_set = set(cells)

    # La forma es triángulo equilátero: fila r tiene 2·r+1 celdas.
    assert cell_set == {(r, c) for r in range(size) for c in range(2*r + 1)}

    seen = {(0, 0)}
    stack = [(0, 0)]
    while stack:
        r, c = stack.pop()
        for n in M.tri_neighbors(r, c, size):
            if n in cell_set and n not in seen and frozenset([(r, c), n]) in conn_set:
                seen.add(n)
                stack.append(n)
    assert seen == cell_set

    # La solución cruza la base: esquina inferior izquierda → inferior derecha.
    assert sol_path
    assert sol_path[0] == (size - 1, 0)
    assert sol_path[-1] == (size - 1, 2*(size - 1))


def test_tri_maze_trenzado_reduce_callejones():
    def count_dead_ends(cells, connections, size):
        conn_set = set(connections)
        dead = 0
        for r, c in cells:
            open_sides = sum(1 for n in M.tri_neighbors(r, c, size)
                              if frozenset([(r, c), n]) in conn_set)
            if open_sides == 1:
                dead += 1
        return dead

    cells_h, conn_h, _, _, sz, _ = M.generate_triangular_maze(12, 'hard')
    cells_k, conn_k, _, _, _, _ = M.generate_triangular_maze(12, 'kids')
    assert count_dead_ends(cells_k, conn_k, sz) < count_dead_ends(cells_h, conn_h, sz)


def test_tri_maze_dificultad_escala_con_ruta():
    size = 10

    def avg_route(diff, n=6):
        vals = []
        for _ in range(n):
            cells, _, _, sol, _, _ = M.generate_triangular_maze(size, diff)
            vals.append(len(sol) / len(cells))
        return sum(vals) / n

    r_kids, r_easy, r_medium, r_hard = (avg_route(d) for d in ('kids', 'easy', 'medium', 'hard'))
    assert r_kids < r_easy < r_medium < r_hard


def test_tri_maze_render_svg():
    cells, connections, walls, sol_path, sz, _ = M.generate_triangular_maze(8, 'medium')
    puzzle_svg = R.render_maze_tri(cells, connections, walls, sol_path, sz, sz, 'flat', 1.5, False)
    solution_svg = R.render_maze_tri(cells, connections, walls, sol_path, sz, sz, 'flat', 1.5, True)
    ET.fromstring(puzzle_svg)
    ET.fromstring(solution_svg)
    assert '<polyline' not in puzzle_svg
    assert '<polyline' in solution_svg


# ─── TRIANGULAR CUADRADO (rejilla rectangular de triángulos, Kruskal) ─────────

@pytest.mark.parametrize('difficulty', ['kids', 'easy', 'medium', 'hard'])
def test_tri_sq_maze_conectividad(difficulty):
    rows, cols = 12, 20
    cells, connections, walls, sol_path, rr, cc = M.generate_triangular_sq_maze(rows, cols, difficulty)
    conn_set = set(connections)
    cell_set = set(cells)
    assert cell_set == {(r, c) for r in range(rows) for c in range(cols)}

    seen = {(0, 0)}
    stack = [(0, 0)]
    while stack:
        cell = stack.pop()
        for n in M.tri_sq_neighbors(cell[0], cell[1], rows, cols):
            if n in cell_set and n not in seen and frozenset([cell, n]) in conn_set:
                seen.add(n)
                stack.append(n)
    assert seen == cell_set

    assert sol_path
    assert sol_path[0] == (0, 0)
    assert sol_path[-1] == (rows - 1, cols - 1)


def test_tri_sq_maze_dificultad_escala_con_ruta():
    rows, cols = 10, 20

    def avg_route(diff, n=6):
        vals = []
        for _ in range(n):
            cells, _, _, sol, _, _ = M.generate_triangular_sq_maze(rows, cols, diff)
            vals.append(len(sol) / len(cells))
        return sum(vals) / n

    r_kids, r_easy, r_medium, r_hard = (avg_route(d) for d in ('kids', 'easy', 'medium', 'hard'))
    assert r_kids < r_easy < r_medium < r_hard


def test_tri_sq_maze_render_svg():
    cells, connections, walls, sol_path, rr, cc = M.generate_triangular_sq_maze(10, 16, 'medium')
    puzzle_svg = R.render_maze_tri_sq(cells, connections, walls, sol_path, rr, cc, 'flat', 1.5, False)
    solution_svg = R.render_maze_tri_sq(cells, connections, walls, sol_path, rr, cc, 'flat', 1.5, True)
    ET.fromstring(puzzle_svg)
    ET.fromstring(solution_svg)
    assert '<polyline' not in puzzle_svg
    assert '<polyline' in solution_svg


# ─── PUENTES / WEAVE (DFS con saltos) ────────────────────────────────────────

@pytest.mark.parametrize('difficulty', ['kids', 'easy', 'medium', 'hard'])
def test_weave_maze_conectividad_y_puentes(difficulty):
    rows, cols = 14, 14
    cells, connections, bridges, sol_path, rows, cols = M.generate_weave_maze(rows, cols, difficulty)
    conn_set = set(connections)
    cell_set = set(cells)

    # Al menos un puente (identidad "weave" incluso en difícil).
    assert len(bridges) >= 1

    # Cada puente conecta un eje perpendicular al de la celda que salta.
    for (r, c), axis in bridges.items():
        assert axis in ('h', 'v')
        if axis == 'h':
            assert frozenset([(r-1, c), (r+1, c)]) in conn_set
        else:
            assert frozenset([(r, c-1), (r, c+1)]) in conn_set

    # Conectividad total vía BFS sobre las aristas (incluye saltos de puente).
    from collections import defaultdict, deque
    adjacency = defaultdict(set)
    for pair in connections:
        a, b = tuple(pair)
        adjacency[a].add(b)
        adjacency[b].add(a)
    seen = {(0, 0)}
    queue = deque([(0, 0)])
    while queue:
        cell = queue.popleft()
        for n in adjacency[cell]:
            if n not in seen:
                seen.add(n)
                queue.append(n)
    assert seen == cell_set

    assert sol_path
    assert sol_path[0] == (0, 0)
    assert sol_path[-1] == (rows - 1, cols - 1)


def test_weave_dificultad_escala_con_cruces_y_ruta():
    """La dificultad NO depende solo del tamaño de la plantilla: a más difícil,
    MÁS cruces (cada paso elevado obliga a seguir qué vía continúa) y ruta MÁS
    larga. Se promedian varias muestras porque la generación es aleatoria."""
    rows, cols = 16, 16

    def sample(diff, n=5):
        cruces, ruta = [], []
        for _ in range(n):
            cells, _, br, sol, _, _ = M.generate_weave_maze(rows, cols, diff)
            cruces.append(len(br))
            ruta.append(len(sol) / len(cells))
        return sum(cruces) / n, sum(ruta) / n

    c_kids, r_kids = sample('kids')
    c_hard, r_hard = sample('hard')
    assert c_hard > c_kids, 'difícil debe tener MÁS cruces que kids'
    assert r_hard > r_kids, 'difícil debe recorrer más tablero que kids'


def test_weave_hard_es_laberinto_perfecto():
    """En difícil no hay trenzado: los cruces van integrados en el árbol, así que
    el grafo sigue siendo un árbol (aristas == celdas-1) ⇒ RUTA ÚNICA."""
    cells, connections, bridges, sol, _, _ = M.generate_weave_maze(14, 14, 'hard')
    assert len(connections) == len(cells) - 1
    assert len(bridges) >= 1


def test_weave_maze_render_svg():
    cells, connections, bridges, sol_path, rows, cols = M.generate_weave_maze(10, 10, 'medium')
    puzzle_svg = R.render_maze_weave(cells, connections, bridges, sol_path, rows, cols, 'flat', 2.0, False)
    solution_svg = R.render_maze_weave(cells, connections, bridges, sol_path, rows, cols, 'flat', 2.0, True)
    ET.fromstring(puzzle_svg)
    ET.fromstring(solution_svg)
    assert '<polyline' not in puzzle_svg
    assert '<polyline' in solution_svg


# ─── PUENTE CIRCULAR (weave ortogonal, render con esquinas redondeadas) ───────
# Round Bridge usa el MISMO generador ortogonal que Bridge; solo cambia el
# render (corner='round'). Por eso comparte los invariantes del weave.

def test_round_weave_render_corner_round():
    cells, connections, bridges, sol_path, rows, cols = M.generate_weave_maze(12, 12, 'medium')
    sharp = R.render_maze_weave(cells, connections, bridges, sol_path, rows, cols,
                                'flat', 2.0, False, corner='sharp')
    roundd = R.render_maze_weave(cells, connections, bridges, sol_path, rows, cols,
                                 'flat', 2.0, False, corner='round')
    ET.fromstring(sharp)
    ET.fromstring(roundd)
    # El estilo redondeado introduce arcos (comando 'A' en los paths).
    assert ' A ' in roundd
    # Ambos renders usan el modelo de corredores (relleno blanco sobre negro).
    assert 'stroke="#ffffff"' in sharp and 'stroke="#ffffff"' in roundd
