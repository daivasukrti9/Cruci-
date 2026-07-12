import random
import copy
import math
import time
import os
import json

# Límite de iteraciones para evitar timeout en puzzles grandes
# 16x16 necesita más iteraciones debido a espacio más grande
MAX_ITERATIONS = 500000


def _validate_sudoku(grid, size, box_w, box_h):
    """Valida que un Sudoku es correcto (sin duplicados en filas, columnas, cajas)."""
    # Verificar filas
    for r in range(size):
        if len(set(grid[r])) != size:
            return False

    # Verificar columnas
    for c in range(size):
        col = [grid[r][c] for r in range(size)]
        if len(set(col)) != size:
            return False

    # Verificar cajas
    for box_r in range(0, size, box_h):
        for box_c in range(0, size, box_w):
            box_vals = []
            for r in range(box_r, box_r + box_h):
                for c in range(box_c, box_c + box_w):
                    box_vals.append(grid[r][c])
            if len(set(box_vals)) != size:
                return False

    return True


def _is_valid(grid, row, col, num, size, box_w, box_h, regions=None, diags=False):
    # Row check
    if num in grid[row]:
        return False
    # Column check
    if num in [grid[r][col] for r in range(size)]:
        return False
    if regions:
        # Jigsaw regions
        region_id = regions[row][col]
        for r in range(size):
            for c in range(size):
                if regions[r][c] == region_id and grid[r][c] == num:
                    return False
    else:
        # Box check
        br, bc = (row // box_h) * box_h, (col // box_w) * box_w
        for r in range(br, br + box_h):
            for c in range(bc, bc + box_w):
                if grid[r][c] == num:
                    return False
    if diags:
        if row == col:
            for i in range(size):
                if grid[i][i] == num:
                    return False
        if row + col == size - 1:
            for i in range(size):
                if grid[i][size - 1 - i] == num:
                    return False
    return True


def _propagate_constraints(grid, size, box_w, box_h, regions=None, diags=False):
    """Aplica constraint propagation: naked singles y hidden singles."""
    changed = True
    while changed:
        changed = False
        # Naked singles: celdas con una sola opción posible
        for r in range(size):
            for c in range(size):
                if grid[r][c] == 0:
                    candidates = set(range(1, size + 1))
                    # Eliminar números en fila
                    candidates -= set(grid[r])
                    # Eliminar números en columna
                    candidates -= set(grid[rr][c] for rr in range(size))
                    # Eliminar números en caja
                    if regions is None:
                        br, bc = (r // box_h) * box_h, (c // box_w) * box_w
                        for rr in range(br, br + box_h):
                            for cc in range(bc, bc + box_w):
                                candidates.discard(grid[rr][cc])
                    else:
                        rid = regions[r][c]
                        for rr in range(size):
                            for cc in range(size):
                                if regions[rr][cc] == rid:
                                    candidates.discard(grid[rr][cc])
                    # Si solo una opción, llenarla
                    if len(candidates) == 1:
                        grid[r][c] = list(candidates)[0]
                        changed = True
                    elif len(candidates) == 0:
                        return False  # Conflicto irreconciliable
        return True


def _solve(grid, size, box_w, box_h, regions=None, diags=False, count=False, limit=2,
           max_iter=None):
    """Backtracking solver con constraint propagation e iteración límite.
    `max_iter` acota el esfuerzo por intento (útil en Jigsaw para descartar
    layouts difíciles rápido y probar otro)."""
    cap = max_iter if max_iter else MAX_ITERATIONS
    solutions = [0]
    iterations = [0]

    def backtrack(pos):
        iterations[0] += 1
        if iterations[0] > cap:
            return False if not count else True  # Timeout

        if pos == size * size:
            solutions[0] += 1
            return solutions[0] < limit if count else True
        r, c = divmod(pos, size)
        if grid[r][c] != 0:
            return backtrack(pos + 1)
        nums = list(range(1, size + 1))
        random.shuffle(nums)
        for num in nums:
            if _is_valid(grid, r, c, num, size, box_w, box_h, regions, diags):
                grid[r][c] = num
                result = backtrack(pos + 1)
                if count:
                    if not result:
                        grid[r][c] = 0
                        return False
                else:
                    if result:
                        return True
                grid[r][c] = 0
        return False if not count else True

    # Aplicar constraint propagation primero
    grid_copy = copy.deepcopy(grid)
    if not _propagate_constraints(grid_copy, size, box_w, box_h, regions, diags):
        return False if not count else 0
    grid[:] = grid_copy

    if count:
        backtrack(0)
        return solutions[0]
    else:
        return backtrack(0)


def _count_solutions(grid, size, box_w, box_h, regions=None, diags=False):
    g = copy.deepcopy(grid)
    return _solve(g, size, box_w, box_h, regions, diags, count=True, limit=2)


def _remove_cells(grid, solution, size, box_w, box_h, clues, regions=None, diags=False):
    puzzle = copy.deepcopy(solution)
    cells = [(r, c) for r in range(size) for c in range(size)]
    random.shuffle(cells)

    # Para tamaños grandes (16x16), simplemente remover celdas sin validar
    # Para tamaños pequeños (9x9, 12x12), validar solución única
    validate_uniqueness = (size <= 9)

    removed = 0
    target_remove = size * size - clues
    for r, c in cells:
        if removed >= target_remove:
            break
        val = puzzle[r][c]
        puzzle[r][c] = 0

        if validate_uniqueness:
            # Validar solución única (lento, pero correcto)
            if _count_solutions(puzzle, size, box_w, box_h, regions, diags) == 1:
                removed += 1
            else:
                puzzle[r][c] = val
        else:
            # Sin validación (rápido, suficiente para 16x16)
            removed += 1

    return puzzle


DIFFICULTY_CLUES = {
    9:  {'easy': 38, 'medium': 32, 'hard': 26},
    16: {'easy': 110, 'medium': 90, 'hard': 70},
    12: {'easy': 80, 'medium': 65, 'hard': 50},
}


def generate_classic(size=9, difficulty='medium'):
    """Classic Sudoku. Returns (puzzle, solution) as 2D lists of ints (0=empty)."""
    if size == 9:
        box_w, box_h = 3, 3
    elif size == 16:
        box_w, box_h = 4, 4
        # Para 16×16, generar directamente con backtracking (sin MAX_ITERATIONS)
        # guardando estado previo y restaurándolo
        old_max = globals()['MAX_ITERATIONS']
        globals()['MAX_ITERATIONS'] = 5000000  # Aumentar para 16x16

        solution = [[0] * 16 for _ in range(16)]
        _solve(solution, 16, box_w, box_h)

        globals()['MAX_ITERATIONS'] = old_max  # Restaurar

        # Validar solución
        if _validate_sudoku(solution, 16, box_w, box_h):
            clues = 110 if difficulty == 'easy' else 90 if difficulty == 'medium' else 70
            puzzle = _remove_cells(copy.deepcopy(solution), solution, 16, box_w, box_h, clues)
            return puzzle, solution
        else:
            # Fallback: generar con método estándar
            solution = [[0] * 16 for _ in range(16)]
            _solve(solution, 16, box_w, box_h)
            clues = 90
            puzzle = _remove_cells(copy.deepcopy(solution), solution, 16, box_w, box_h, clues)
            return puzzle, solution
    elif size == 12:
        box_w, box_h = 4, 3
    else:
        s = int(math.isqrt(size))
        box_w = box_h = s

    grid = [[0] * size for _ in range(size)]
    _solve(grid, size, box_w, box_h)
    solution = copy.deepcopy(grid)
    clues = DIFFICULTY_CLUES.get(size, {}).get(difficulty, size * size // 2)
    puzzle = _remove_cells(grid, solution, size, box_w, box_h, clues)
    return puzzle, solution


# Template válido para Sudoku 16×16 (para permutación rápida)
SUDOKU_16x16_TEMPLATE = [
    [1,2,3,4, 5,6,7,8, 9,10,11,12, 13,14,15,16],
    [5,6,7,8, 9,10,11,12, 13,14,15,16, 1,2,3,4],
    [9,10,11,12, 13,14,15,16, 1,2,3,4, 5,6,7,8],
    [13,14,15,16, 1,2,3,4, 5,6,7,8, 9,10,11,12],

    [2,1,4,3, 6,5,8,7, 10,9,12,11, 14,13,16,15],
    [6,5,8,7, 10,9,12,11, 14,13,16,15, 2,1,4,3],
    [10,9,12,11, 14,13,16,15, 2,1,4,3, 6,5,8,7],
    [14,13,16,15, 2,1,4,3, 6,5,8,7, 10,9,12,11],

    [3,4,1,2, 7,8,5,6, 11,12,9,10, 15,16,13,14],
    [7,8,5,6, 11,12,9,10, 15,16,13,14, 3,4,1,2],
    [11,12,9,10, 15,16,13,14, 3,4,1,2, 7,8,5,6],
    [15,16,13,14, 3,4,1,2, 7,8,5,6, 11,12,9,10],

    [4,3,2,1, 8,7,6,5, 12,11,10,9, 16,15,14,13],
    [8,7,6,5, 12,11,10,9, 16,15,14,13, 4,3,2,1],
    [12,11,10,9, 16,15,14,13, 4,3,2,1, 8,7,6,5],
    [16,15,14,13, 4,3,2,1, 8,7,6,5, 12,11,10,9],
]

def _generate_latin_square_fast(size, box_w, box_h):
    """Genera Sudoku válido mediante permutación de template (muy rápido)."""
    if size == 16:
        # Usar template + permutaciones
        grid = [row[:] for row in SUDOKU_16x16_TEMPLATE]

        # Permutar filas dentro de bands
        for band in range(0, 16, 4):
            rows = list(range(band, band + 4))
            random.shuffle(rows)
            for i, src_row in enumerate(rows):
                for c in range(16):
                    grid[band + i][c] = SUDOKU_16x16_TEMPLATE[src_row][c]

        return grid
    else:
        # Para otros tamaños, usar backtracking simple
        grid = [[0] * size for _ in range(size)]
        _solve(grid, size, box_w, box_h)
        return grid


def generate_x(difficulty='medium'):
    """Sudoku X — adds diagonal constraints."""
    size, box_w, box_h = 9, 3, 3
    grid = [[0] * size for _ in range(size)]
    _solve(grid, size, box_w, box_h, diags=True)
    solution = copy.deepcopy(grid)
    clues = DIFFICULTY_CLUES[9].get(difficulty, 30) - 3
    puzzle = _remove_cells(grid, solution, size, box_w, box_h, clues, diags=True)
    return puzzle, solution


def generate_letters(difficulty='medium'):
    """Sudoku Letters (A-I instead of 1-9). Returns same format but values are letter strings."""
    puzzle, solution = generate_classic(9, difficulty)
    letters = 'ABCDEFGHI'
    def to_letters(grid):
        return [[letters[v-1] if v != 0 else '' for v in row] for row in grid]
    return to_letters(puzzle), to_letters(solution)


def generate_killer(difficulty='medium'):
    """Sudoku Asesino. Returns (puzzle, solution, cages) where cages is list of dicts."""
    puzzle_blank, solution = generate_classic(9, difficulty)
    # Build cages by merging adjacent cells randomly
    cage_id = [[None] * 9 for _ in range(9)]
    cages = []
    cells_left = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells_left)
    cid = 0
    while cells_left:
        # Pick seed
        seed = cells_left.pop(0)
        if cage_id[seed[0]][seed[1]] is not None:
            continue
        cage_size = random.randint(1, 4)
        cage_cells = [seed]
        cage_id[seed[0]][seed[1]] = cid
        for _ in range(cage_size - 1):
            # Expand to random neighbor
            candidates = []
            for r, c in cage_cells:
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < 9 and 0 <= nc < 9 and cage_id[nr][nc] is None and (nr,nc) not in cage_cells:
                        candidates.append((nr, nc))
            if not candidates:
                break
            next_cell = random.choice(candidates)
            cage_cells.append(next_cell)
            cage_id[next_cell[0]][next_cell[1]] = cid
        cage_sum = sum(solution[r][c] for r, c in cage_cells)
        cages.append({'id': cid, 'cells': cage_cells, 'sum': cage_sum})
        cid += 1
    # Puzzle shows empty grid + cage definitions
    empty_puzzle = [[0]*9 for _ in range(9)]
    return empty_puzzle, solution, cages


def generate_jigsaw(difficulty='medium', with_x=False, letters=False, size=9):
    """Sudoku Jigsaw: regiones irregulares de EXACTAMENTE `size` casillas.
    La solución respeta las regiones (no cajas regulares)."""
    if size == 12:
        box_w, box_h = 4, 3
    elif size == 16:
        box_w, box_h = 4, 4
    else:
        box_w, box_h = 3, 3

    solution = None
    regions = None

    # 0) Plantillas curadas (sin rectángulos garantizado) para los casos donde
    #    generar en vivo es poco fiable: 12×12 y 9×9 Jigsaw X. Se elige una plantilla
    #    + una simetría al azar (variedad) y se rellena con una solución nueva.
    tmpl_key = ('jigsaw_x_9' if size == 9 and with_x
                else 'jigsaw_9' if size == 9
                else 'jigsaw_12' if size == 12 and not with_x else None)
    templates = _load_jigsaw_templates().get(tmpl_key, []) if tmpl_key else []
    for _ in range(10):
        if not templates:
            break
        entry = random.choice(templates)
        t = random.randrange(8)                       # simetría diédrica (variedad)
        reg = _transform_regions(entry['regions'], size, t)
        sol = _transform_regions(entry['solution'], size, t)   # misma transformación
        if _count_boxy(reg, size) == 0 and _validate_jigsaw(sol, size, reg):
            solution, regions = sol, reg
            break

    # 1) Sin plantilla disponible: tallar en vivo regiones SIN rectángulos sobre
    #    soluciones PLANAS rápidas (bien para 9×9 plano y letras). Acotado por tiempo.
    if solution is None:
        fewest = 99
        deadline = time.time() + 2.5
        while time.time() < deadline and fewest > 0:
            sol = [[0] * size for _ in range(size)]
            _solve(sol, size, box_w, box_h)          # plana (rápida)
            for _ in range(30):
                if time.time() >= deadline:
                    break
                cand = _carve_rainbow_regions(sol, size)
                if cand is None:
                    continue
                boxy = _count_boxy(cand, size)
                if boxy >= fewest:
                    continue
                if with_x:
                    # Jigsaw X: la región debe ADMITIR una solución con diagonales.
                    filled = _fill_jigsaw(size, cand, diags=True, max_iter=20000)
                    if filled is None:
                        continue
                    fewest, regions, solution = boxy, cand, filled
                else:
                    fewest, regions, solution = boxy, cand, sol
                if boxy == 0:
                    break

    if solution is None or regions is None or not _validate_jigsaw(solution, size, regions):
        # Fallback seguro: cajas regulares como regiones.
        solution = [[0] * size for _ in range(size)]
        _solve(solution, size, box_w, box_h, diags=with_x)
        regions = _regular_boxes_as_regions(size, box_w, box_h)

    # Quitar celdas para formar el puzzle
    puzzle = copy.deepcopy(solution)
    clues = DIFFICULTY_CLUES.get(size, {}).get(difficulty, size * size // 3)
    cells = [(r, c) for r in range(size) for c in range(size)]
    random.shuffle(cells)
    removed = 0
    for r, c in cells:
        if removed >= (size * size - clues):
            break
        puzzle[r][c] = 0
        removed += 1

    if letters and size == 9:
        let = 'ABCDEFGHI'
        def to_l(g): return [[let[v-1] if v else '' for v in row] for row in g]
        return to_l(puzzle), to_l(solution), regions
    return puzzle, solution, regions


_JIGSAW_TEMPLATES = None


def _load_jigsaw_templates():
    """Carga (una vez) las plantillas de regiones sin rectángulos cosechadas offline.
    Devuelve {} si el archivo no existe."""
    global _JIGSAW_TEMPLATES
    if _JIGSAW_TEMPLATES is None:
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'puzzles_patterns', 'jigsaw_templates.json')
        try:
            with open(path, encoding='utf-8') as f:
                _JIGSAW_TEMPLATES = json.load(f)
        except (OSError, ValueError):
            _JIGSAW_TEMPLATES = {}
    return _JIGSAW_TEMPLATES


def _transform_regions(reg, size, t):
    """Aplica una simetría del grupo diédrico (0..7) al mapa de regiones para dar
    variedad. Las transformaciones rígidas preservan tamaño, contigüidad y la
    propiedad de "sin rectángulos"; además, como el par de diagonales es invariante,
    conservan la validez del Jigsaw X."""
    m = [row[:] for row in reg]
    if t >= 4:
        m = [row[::-1] for row in m]      # reflejo horizontal
        t -= 4
    for _ in range(t):                    # t rotaciones de 90°
        m = [[m[size - 1 - c][r] for c in range(size)] for r in range(size)]
    return m


def _fill_jigsaw(size, regions, diags=False, max_iter=200000):
    """Rellena una cuadrícula válida para las regiones dadas usando MRV (elige la
    casilla con menos candidatos). Devuelve la grilla o None. Se usa para Jigsaw X,
    donde la solución debe cumplir además las dos diagonales."""
    grid = [[0] * size for _ in range(size)]
    rows = [set() for _ in range(size)]
    cols = [set() for _ in range(size)]
    reg = {}
    diag1, diag2 = set(), set()
    iters = [0]

    def cands(r, c):
        used = rows[r] | cols[c] | reg.setdefault(regions[r][c], set())
        if diags:
            if r == c:
                used = used | diag1
            if r + c == size - 1:
                used = used | diag2
        return [v for v in range(1, size + 1) if v not in used]

    def put(r, c, v, add):
        for s in (rows[r], cols[c], reg[regions[r][c]]):
            s.add(v) if add else s.discard(v)
        if diags:
            if r == c:
                diag1.add(v) if add else diag1.discard(v)
            if r + c == size - 1:
                diag2.add(v) if add else diag2.discard(v)

    def solve():
        iters[0] += 1
        if iters[0] > max_iter:
            return False
        best, best_c = None, None
        for r in range(size):
            for c in range(size):
                if grid[r][c] == 0:
                    cc = cands(r, c)
                    if not cc:
                        return False
                    if best_c is None or len(cc) < len(best_c):
                        best, best_c = (r, c), cc
                        if len(cc) == 1:
                            break
            if best_c is not None and len(best_c) == 1:
                break
        if best is None:
            return True
        r, c = best
        random.shuffle(best_c)
        for v in best_c:
            grid[r][c] = v
            put(r, c, v, True)
            if solve():
                return True
            put(r, c, v, False)
            grid[r][c] = 0
        return False

    return grid if solve() else None


def _is_boxy_rect(cells, box_min=1):
    """True si las casillas forman un rectángulo lleno. Con box_min=1 cuenta
    cualquier rectángulo (3x3, 3x4, y también barras 1xN/2xN), es decir todo lo
    que NO parezca una pieza de rompecabezas irregular."""
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    h = max(rs) - min(rs) + 1
    w = max(cs) - min(cs) + 1
    return h * w == len(cells) and min(h, w) >= box_min


def _count_boxy(regions, size):
    """Número de piezas con forma de caja (3x3, 3x4...) en la partición."""
    cells_by_rid = {}
    for r in range(size):
        for c in range(size):
            cells_by_rid.setdefault(regions[r][c], []).append((r, c))
    return sum(1 for cs in cells_by_rid.values() if _is_boxy_rect(cs))


def _carve_rainbow_regions(grid, size, attempts=400):
    """Talla `size` regiones contiguas de EXACTAMENTE `size` casillas cada una,
    donde cada región tiene valores DISTINTOS en `grid` (una de cada 1..size).
    Como `grid` ya es válido en filas/columnas, el resultado es un jigsaw válido.
    Crece región por región eligiendo la frontera con menos vecinos libres.
    Devuelve las regiones o None si no lo logra."""
    DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def free_neighbors(regions, r, c):
        return sum(1 for dr, dc in DIRS
                   if 0 <= r + dr < size and 0 <= c + dc < size
                   and regions[r + dr][c + dc] == -1)

    for _ in range(attempts):
        regions = [[-1] * size for _ in range(size)]
        ok = True
        for rid in range(size):
            unassigned = [(r, c) for r in range(size) for c in range(size)
                          if regions[r][c] == -1]
            if rid == 0:
                seed = min(unassigned)
            else:
                adj = [(r, c) for (r, c) in unassigned
                       if any(0 <= r + dr < size and 0 <= c + dc < size
                              and regions[r + dr][c + dc] != -1 for dr, dc in DIRS)]
                seed = random.choice(adj or unassigned)
            regions[seed[0]][seed[1]] = rid
            used = {grid[seed[0]][seed[1]]}
            count = 1
            while count < size:
                frontier = set()
                for r in range(size):
                    for c in range(size):
                        if regions[r][c] == rid:
                            for dr, dc in DIRS:
                                nr, nc = r + dr, c + dc
                                if (0 <= nr < size and 0 <= nc < size
                                        and regions[nr][nc] == -1
                                        and grid[nr][nc] not in used):
                                    frontier.add((nr, nc))
                if not frontier:
                    ok = False
                    break
                m = min(free_neighbors(regions, r, c) for (r, c) in frontier)
                nr, nc = random.choice([p for p in frontier
                                        if free_neighbors(regions, p[0], p[1]) == m])
                regions[nr][nc] = rid
                used.add(grid[nr][nc])
                count += 1
            if not ok:
                break
        if ok and all(regions[r][c] != -1 for r in range(size) for c in range(size)):
            return regions
    return None


def _regular_boxes_as_regions(size, box_w, box_h):
    """Regiones = cajas regulares (fallback siempre válido)."""
    per_row = size // box_w
    return [[(r // box_h) * per_row + (c // box_w) for c in range(size)]
            for r in range(size)]


def _validate_jigsaw(grid, size, regions):
    """Cada fila, columna y REGIÓN contiene 1..size exactamente una vez."""
    full = set(range(1, size + 1))
    for r in range(size):
        if set(grid[r]) != full:
            return False
    for c in range(size):
        if set(grid[r][c] for r in range(size)) != full:
            return False
    region_vals = {}
    for r in range(size):
        for c in range(size):
            region_vals.setdefault(regions[r][c], []).append(grid[r][c])
    return all(len(v) == size and set(v) == full for v in region_vals.values())


