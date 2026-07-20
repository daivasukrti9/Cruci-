import random
import math


# Fracción de callejones sin salida que se convierten en bucles (atajo extra),
# de más fácil a más difícil. Un laberinto "perfecto" (0.0) tiene una única
# solución y muchos callejones; al trenzar (braid) se abren atajos y se vuelve
# más fácil de resolver a simple vista.
_BRAID_BY_DIFFICULTY = {'kids': 0.6, 'easy': 0.3, 'medium': 0.05, 'hard': 0.0}


def generate_rectangular_maze(rows, cols, difficulty='medium'):
    """
    Classic rectangular maze using recursive backtracking (DFS).
    Returns (maze, solution_path) where maze is a 2D grid (1=pared, 0=paso).
    Grid dimensions: (2*rows+1) x (2*cols+1); cell (r,c) -> grid[2r+1][2c+1].
    `difficulty` controla el "trenzado" (braid): cuantos callejones sin salida
    se abren en bucle para crear atajos (kids/easy = más fácil, hard = laberinto
    perfecto con una única solución).
    """
    # Initialize all walls
    grid = [[1]*(2*cols+1) for _ in range(2*rows+1)]

    # Mark cell centers as passages
    for r in range(rows):
        for c in range(cols):
            grid[2*r+1][2*c+1] = 0

    visited = [[False]*cols for _ in range(rows)]

    def carve(r, c):
        visited[r][c] = True
        directions = [(0,1),(0,-1),(1,0),(-1,0)]
        random.shuffle(directions)
        for dr, dc in directions:
            nr, nc = r+dr, c+dc
            if 0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc]:
                # Remove wall between (r,c) and (nr,nc)
                wr, wc = 2*r+1+dr, 2*c+1+dc
                grid[wr][wc] = 0
                carve(nr, nc)

    carve(0, 0)

    # Entry and exit
    grid[1][0] = 0  # left entrance
    grid[2*rows-1][2*cols] = 0  # right exit

    _braid(grid, rows, cols, _BRAID_BY_DIFFICULTY.get(difficulty, 0.05))

    # Find solution path using BFS
    from collections import deque
    start = (1, 0)
    end = (2*rows-1, 2*cols)
    queue = deque([(start, [start])])
    seen = {start}
    solution_path = []
    while queue:
        (r, c), path = queue.popleft()
        if (r, c) == end:
            solution_path = path
            break
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < 2*rows+1 and 0 <= nc < 2*cols+1 and (nr,nc) not in seen and grid[nr][nc] == 0:
                seen.add((nr,nc))
                queue.append(((nr,nc), path+[(nr,nc)]))

    return grid, solution_path


def _braid(grid, rows, cols, fraction):
    """Abre callejones sin salida en bucle (atajo) con probabilidad `fraction`,
    para volver el laberinto más fácil. Opera sobre el grid ya carvado."""
    if fraction <= 0:
        return
    dead_ends = []
    for r in range(rows):
        for c in range(cols):
            open_sides = 0
            for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
                wr, wc = 2*r+1+dr, 2*c+1+dc
                if 0 <= wr < len(grid) and 0 <= wc < len(grid[0]) and grid[wr][wc] == 0:
                    open_sides += 1
            if open_sides == 1:
                dead_ends.append((r, c))

    random.shuffle(dead_ends)
    for r, c in dead_ends:
        if random.random() > fraction:
            continue
        candidates = []
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            nr, nc = r+dr, c+dc
            wr, wc = 2*r+1+dr, 2*c+1+dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[wr][wc] == 1:
                candidates.append((wr, wc))
        if candidates:
            wr, wc = random.choice(candidates)
            grid[wr][wc] = 0


def _dfs_spanning_tree(cells, neighbors_fn, start=None):
    """Árbol de expansión por 'recursive backtracker' (DFS iterativo). A
    diferencia de Kruskal/Prim/Aldous-Broder, produce corredores largos y
    sinuosos (alto factor 'river'): el camino entre dos extremos fijos recorre
    buena parte del laberinto, dando soluciones LARGAS y poco predecibles (no
    una diagonal directa entrada→salida). El grafo de vecinos debe ser conexo.
    `neighbors_fn` recibe una celda y devuelve sus vecinas.
    Devuelve el conjunto de connections (frozenset de pares de celdas)."""
    start = start if start is not None else cells[0]
    visited = {start}
    connections = set()
    stack = [start]
    while stack:
        cur = stack[-1]
        unvisited = [n for n in neighbors_fn(cur) if n not in visited]
        if not unvisited:
            stack.pop()
            continue
        nxt = random.choice(unvisited)
        visited.add(nxt)
        connections.add(frozenset([cur, nxt]))
        stack.append(nxt)
    return connections


def hex_offset_neighbors(row, col):
    """Vecinos de una celda hexagonal en coordenadas OFFSET "odd-r" (hexágonos
    pointy-top; las filas impares se desplazan media celda a la derecha). Esta
    disposición da un contorno RECTANGULAR (no romboidal). 6 vecinos."""
    if row % 2 == 0:   # fila par
        return [(row, col-1), (row, col+1),
                (row-1, col-1), (row-1, col),
                (row+1, col-1), (row+1, col)]
    else:              # fila impar (desplazada)
        return [(row, col-1), (row, col+1),
                (row-1, col), (row-1, col+1),
                (row+1, col), (row+1, col+1)]


def generate_hexagonal_maze(rows, cols, difficulty='medium'):
    """
    Laberinto hexagonal sobre coordenadas OFFSET "odd-r" (contorno rectangular)
    con hexágonos pointy-top y 6 vecinos por celda. Se genera con DFS
    (recursive backtracker), que da rutas largas y sinuosas. `difficulty`
    controla el trenzado (braid).
    Returns (cells, connections, walls, solution_path).
    cells: lista de (row, col). walls/connections: frozenset({cell1, cell2}).
    """
    cells = [(row, col) for row in range(rows) for col in range(cols)]
    cell_set = set(cells)

    def neighbors(cell):
        return [n for n in hex_offset_neighbors(*cell) if n in cell_set]

    connections = _dfs_spanning_tree(cells, neighbors)

    # Paredes = todas las aristas posibles del panal que no son conexión.
    seen_edges = set()
    for cell in cells:
        for n in neighbors(cell):
            seen_edges.add(frozenset([cell, n]))
    walls = {pair for pair in seen_edges if pair not in connections}

    _braid_generic(cells, lambda r, c: neighbors((r, c)), connections, walls,
                   _BRAID_BY_DIFFICULTY.get(difficulty, 0.05))

    # BFS para la solución: esquina superior izquierda → inferior derecha.
    from collections import deque
    start = (0, 0)
    end = (rows-1, cols-1)
    queue = deque([(start, [start])])
    seen = {start}
    solution_path = []
    while queue:
        cell, path = queue.popleft()
        if cell == end:
            solution_path = path
            break
        for n in neighbors(cell):
            if n not in seen and frozenset([cell, n]) in connections:
                seen.add(n)
                queue.append((n, path+[n]))

    return cells, list(connections), walls, solution_path


def tri_orientation(r, c):
    """En la malla en forma de triángulo equilátero, la celda (r, c) apunta
    hacia arriba ('up', base abajo) si c es par, y hacia abajo ('down', base
    arriba) si c es impar. La fila r tiene 2·r+1 celdas (c = 0 … 2·r)."""
    return 'up' if c % 2 == 0 else 'down'


def tri_neighbors(r, c, size):
    """3 vecinos de una celda triangular dentro del triángulo equilátero de
    lado `size` filas: izquierda/derecha en la misma fila, y el vecino vertical
    (abajo si 'up', arriba si 'down')."""
    nbrs = []
    if c > 0:
        nbrs.append((r, c-1))
    if c < 2*r:
        nbrs.append((r, c+1))
    if c % 2 == 0:            # 'up' → vecino ABAJO
        if r + 1 < size:
            nbrs.append((r+1, c+1))
    else:                     # 'down' → vecino ARRIBA
        nbrs.append((r-1, c-1))
    return nbrs


def generate_triangular_maze(size, difficulty='medium'):
    """
    Laberinto sobre una malla TRIANGULAR con forma de triángulo equilátero: la
    fila r tiene 2·r+1 celdas triangulares (▲ si c par, ▽ si c impar), 3 vecinos
    cada una. Se genera con DFS (recursive backtracker), que da rutas largas y
    sinuosas (no una franja pegada a la base).
    Entrada y salida se abren en las dos esquinas inferiores de la base.
    Returns (cells, connections, walls, solution_path, size, size).
    """
    cells = [(r, c) for r in range(size) for c in range(2*r + 1)]
    cell_set = set(cells)

    def neighbors(r, c):
        return tri_neighbors(r, c, size)

    connections = _dfs_spanning_tree(cells, lambda cell: neighbors(*cell))

    walls = set()
    for cell in cells:
        r, c = cell
        for nbr in neighbors(r, c):
            pair = frozenset([cell, nbr])
            if pair not in connections:
                walls.add(pair)

    _braid_generic(cells, neighbors, connections, walls,
                    _BRAID_BY_DIFFICULTY.get(difficulty, 0.05))

    # La solución cruza la base: entra por la esquina inferior IZQUIERDA y sale
    # por la inferior DERECHA (ambas celdas 'up' del último renglón).
    from collections import deque
    sol_start = (size - 1, 0)
    sol_end = (size - 1, 2*(size - 1))
    queue = deque([(sol_start, [sol_start])])
    seen = {sol_start}
    solution_path = []
    while queue:
        cell, path = queue.popleft()
        if cell == sol_end:
            solution_path = path
            break
        r, c = cell
        for nbr in neighbors(r, c):
            if nbr not in seen and frozenset([cell, nbr]) in connections:
                seen.add(nbr)
                queue.append((nbr, path+[nbr]))

    return cells, list(connections), walls, solution_path, size, size


def tri_sq_neighbors(r, c, rows, cols):
    """3 vecinos en la malla TRIANGULAR RECTANGULAR (contorno cuadrado): la
    celda (r,c) apunta ▲ si (r+c) es par, ▽ si impar. Vecinos: izquierda,
    derecha, y el vertical (abajo si ▲, arriba si ▽)."""
    nbrs = []
    if c > 0:
        nbrs.append((r, c-1))
    if c < cols - 1:
        nbrs.append((r, c+1))
    if (r + c) % 2 == 0:          # ▲ up → vecino ABAJO
        if r + 1 < rows:
            nbrs.append((r+1, c))
    else:                          # ▽ down → vecino ARRIBA
        if r - 1 >= 0:
            nbrs.append((r-1, c))
    return nbrs


def generate_triangular_sq_maze(rows, cols, difficulty='medium'):
    """
    Laberinto TRIANGULAR de contorno RECTANGULAR/cuadrado: rejilla de rows×cols
    triángulos (▲ si (r+c) par, ▽ si impar), 3 vecinos. Se genera con DFS
    (recursive backtracker), que da rutas largas y sinuosas (no una diagonal
    directa). Entrada arriba-izquierda, salida abajo-derecha.
    Returns (cells, connections, walls, solution_path, rows, cols).
    """
    cells = [(r, c) for r in range(rows) for c in range(cols)]
    cell_set = set(cells)

    def neighbors(cell):
        return tri_sq_neighbors(cell[0], cell[1], rows, cols)

    connections = _dfs_spanning_tree(cells, neighbors)

    seen_edges = set()
    for cell in cells:
        for n in neighbors(cell):
            seen_edges.add(frozenset([cell, n]))
    walls = {pair for pair in seen_edges if pair not in connections}

    _braid_generic(cells, lambda r, c: neighbors((r, c)), connections, walls,
                   _BRAID_BY_DIFFICULTY.get(difficulty, 0.05))

    from collections import deque
    start, end = (0, 0), (rows-1, cols-1)
    queue = deque([(start, [start])])
    seen = {start}
    solution_path = []
    while queue:
        cell, path = queue.popleft()
        if cell == end:
            solution_path = path
            break
        for n in neighbors(cell):
            if n not in seen and frozenset([cell, n]) in connections:
                seen.add(n)
                queue.append((n, path+[n]))

    return cells, list(connections), walls, solution_path, rows, cols


def _ring_sector_counts(rings, sectors_per_ring):
    """Subdivisión de anillos: el número de sectores se DUPLICA a medida que
    crece el radio, para que las celdas no se vuelvan demasiado anchas hacia
    afuera (técnica estándar de laberintos polares/"Theta")."""
    counts = [sectors_per_ring]
    for r in range(1, rings):
        prev = counts[-1]
        arc_width = 2 * math.pi * r / prev  # ancho aprox. de celda en "unidades de anillo"
        counts.append(prev * 2 if arc_width > 1.5 else prev)
    return counts


def generate_circular_maze(rings, sectors_per_ring=8, difficulty='medium'):
    """
    Laberinto circular polar con subdivisión real de anillos (más sectores
    hacia afuera) y generación por el algoritmo de PRIM (frontera aleatoria).
    Cada celda es (ring, sector); ring 0 = centro, ring n-1 = exterior.
    Returns (all_cells, sector_counts, connections, walls, solution_path).
    """
    sector_counts = _ring_sector_counts(rings, sectors_per_ring)
    all_cells = [(r, s) for r in range(rings) for s in range(sector_counts[r])]
    cell_set = set(all_cells)

    def same_ring_neighbors(r, s):
        sc = sector_counts[r]
        return [(r, (s-1) % sc), (r, (s+1) % sc)]

    def inner_neighbor(r, s):
        if r == 0:
            return None
        sc, inner_sc = sector_counts[r], sector_counts[r-1]
        k = sc // inner_sc
        return (r-1, s // k)

    def outer_neighbors(r, s):
        if r == rings - 1:
            return []
        sc, outer_sc = sector_counts[r], sector_counts[r+1]
        k = outer_sc // sc
        return [(r+1, s*k+i) for i in range(k)]

    def neighbors(r, s):
        nbrs = same_ring_neighbors(r, s)
        inn = inner_neighbor(r, s)
        if inn is not None:
            nbrs.append(inn)
        nbrs.extend(outer_neighbors(r, s))
        return [n for n in nbrs if n in cell_set]

    # DFS (recursive backtracker) desde el centro: produce corredores largos y
    # sinuosos, de modo que la solución serpentea entre anillos en vez de ir
    # casi directa por el borde exterior.
    connections = _dfs_spanning_tree(all_cells, lambda cell: neighbors(*cell), start=(0, 0))

    walls = set()
    for cell in all_cells:
        for nbr in neighbors(*cell):
            pair = frozenset([cell, nbr])
            if pair not in connections:
                walls.add(pair)

    _braid_generic(all_cells, neighbors, connections, walls,
                    _BRAID_BY_DIFFICULTY.get(difficulty, 0.05))

    # La solución ENTRA y SALE por el borde exterior en sectores opuestos, de
    # modo que atraviesa todo el disco (no termina "encerrada" en el centro).
    outer = rings - 1
    sc_outer = sector_counts[outer]
    sol_start = (outer, 0)
    sol_end = (outer, sc_outer // 2)

    from collections import deque
    queue = deque([(sol_start, [sol_start])])
    seen = {sol_start}
    solution_path = []
    while queue:
        cell, path = queue.popleft()
        if cell == sol_end:
            solution_path = path
            break
        for nbr in neighbors(*cell):
            if nbr not in seen and frozenset([cell, nbr]) in connections:
                seen.add(nbr)
                queue.append((nbr, path+[nbr]))

    return all_cells, sector_counts, list(connections), walls, solution_path


def _braid_generic(cells, neighbors_fn, connections, walls, fraction):
    """Versión genérica de `_braid`/`_braid_hex` para grafos de celdas
    arbitrarios (usada por el laberinto circular)."""
    if fraction <= 0:
        return
    dead_ends = []
    for cell in cells:
        open_sides = sum(1 for n in neighbors_fn(*cell) if frozenset([cell, n]) in connections)
        if open_sides == 1:
            dead_ends.append(cell)

    random.shuffle(dead_ends)
    for cell in dead_ends:
        if random.random() > fraction:
            continue
        candidates = [n for n in neighbors_fn(*cell) if frozenset([cell, n]) in walls]
        if candidates:
            other = random.choice(candidates)
            pair = frozenset([cell, other])
            walls.discard(pair)
            connections.add(pair)


# Cruces (pasos elevados) por dificultad: a MÁS difícil, MÁS cruces. Cada cruce
# obliga a seguir con la vista qué vía continúa, que es el engaño propio de este
# juego. Se conservan cruces en todos los niveles para no perder el "tejido".
_WEAVE_CROSS_BY_DIFFICULTY = {'kids': 0.15, 'easy': 0.35, 'medium': 0.60, 'hard': 0.85}
# Trenzado: abre callejones y crea atajos ⇒ MÁS fácil y callejones más cortos.
# En difícil es 0: laberinto perfecto, ruta única y callejones profundos.
_WEAVE_BRAID_BY_DIFFICULTY = {'kids': 0.55, 'easy': 0.30, 'medium': 0.10, 'hard': 0.0}

_DIRS4 = [(0, 1), (0, -1), (1, 0), (-1, 0)]


def _weave_degree(cell, connections):
    r, c = cell
    return sum(1 for dr, dc in _DIRS4
               if frozenset([cell, (r+dr, c+dc)]) in connections)


def _weave_straight_axis(cell, connections):
    """'h'/'v' si la celda ya es un pasillo RECTO (grado 2 sin giro); None si no."""
    r, c = cell
    if _weave_degree(cell, connections) != 2:
        return None
    if (frozenset([cell, (r, c-1)]) in connections
            and frozenset([cell, (r, c+1)]) in connections):
        return 'h'
    if (frozenset([cell, (r-1, c)]) in connections
            and frozenset([cell, (r+1, c)]) in connections):
        return 'v'
    return None


def _braid_weave(cells, cell_set, connections, bridges, fraction):
    """Abre callejones sin salida (crea atajos ⇒ más fácil y recorridos falsos
    más cortos). Nunca toca una celda-puente: su pasillo de abajo debe seguir
    recto para que el paso elevado siga teniendo sentido."""
    if fraction <= 0:
        return
    dead = [c for c in cells
            if c not in bridges and _weave_degree(c, connections) == 1]
    random.shuffle(dead)
    for cell in dead:
        if random.random() > fraction:
            continue
        r, c = cell
        cand = [(r+dr, c+dc) for dr, dc in _DIRS4
                if (r+dr, c+dc) in cell_set
                and (r+dr, c+dc) not in bridges
                and frozenset([cell, (r+dr, c+dc)]) not in connections]
        if cand:
            connections.add(frozenset([cell, random.choice(cand)]))


def _weave_once(rows, cols, difficulty):
    """
    Laberinto de PUENTES (weave) con los cruces INTEGRADOS en el carvado: al
    avanzar, el DFS puede dar un paso normal a una celda sin visitar, o bien
    SALTAR por encima de un pasillo recto ya hecho hasta la celda siguiente
    (paso elevado). Como el salto también aterriza en una celda SIN visITAR, la
    arista sigue siendo de árbol: el laberinto es PERFECTO (ruta única) aunque
    tenga muchos cruces. Antes los puentes se añadían al final como aristas
    extra, y cada uno creaba un bucle (atajos) — por eso la dificultad salía
    plana e invertida.
    `difficulty` sube los cruces y baja el trenzado conforme sube la dificultad.
    Returns (cells, connections, bridges, solution_path, rows, cols).
    bridges: dict {celda_saltada: eje del pasillo de abajo} ('h' o 'v').
    """
    cells = [(r, c) for r in range(rows) for c in range(cols)]
    cell_set = set(cells)
    p_cross = _WEAVE_CROSS_BY_DIFFICULTY.get(difficulty, 0.60)

    connections = set()
    bridges = {}
    start_cell = (0, 0)
    visited = {start_cell}
    stack = [start_cell]

    while stack:
        cur = stack[-1]
        if cur in bridges:
            # Celda bajo un paso elevado: queda BLOQUEADA para que su pasillo
            # siga recto. No pierde nada: al saltarla, su única vecina sin
            # visitar era justo el destino del salto (las otras dos ya están
            # conectadas en el corredor).
            stack.pop()
            continue
        r, c = cur
        steps, jumps = [], []
        for dr, dc in _DIRS4:
            nxt = (r+dr, c+dc)
            if nxt not in cell_set:
                continue
            if nxt not in visited:
                steps.append(nxt)
                continue
            # Salto por encima de `nxt` (que debe ser un pasillo RECTO
            # perpendicular al salto) hasta la celda siguiente sin visitar.
            jump = (r + 2*dr, c + 2*dc)
            if (jump in cell_set and jump not in visited
                    and nxt not in bridges
                    and _weave_straight_axis(nxt, connections) == ('h' if dr else 'v')):
                jumps.append((jump, nxt))
        if not steps and not jumps:
            stack.pop()
            continue
        if jumps and (not steps or random.random() < p_cross):
            nxt, mid = random.choice(jumps)
            bridges[mid] = _weave_straight_axis(mid, connections)
        else:
            nxt = random.choice(steps)
        connections.add(frozenset([cur, nxt]))
        visited.add(nxt)
        stack.append(nxt)

    _braid_weave(cells, cell_set, connections, bridges,
                 _WEAVE_BRAID_BY_DIFFICULTY.get(difficulty, 0.10))

    # BFS para la solución. Los puentes son aristas normales del grafo (saltan
    # la celda intermedia), así que una lista de adyacencia basta.
    from collections import deque, defaultdict
    adjacency = defaultdict(set)
    for pair in connections:
        a, b = tuple(pair)
        adjacency[a].add(b)
        adjacency[b].add(a)

    start, end = (0, 0), (rows-1, cols-1)
    queue = deque([(start, [start])])
    seen = {start}
    solution_path = []
    while queue:
        cell, path = queue.popleft()
        if cell == end:
            solution_path = path
            break
        for nb in adjacency[cell]:
            if nb not in seen:
                seen.add(nb)
                queue.append((nb, path+[nb]))

    return cells, list(connections), bridges, solution_path, rows, cols


# Fracción del tablero que debería recorrer la ruta correcta en cada nivel. El
# carvado es aleatorio y su varianza es alta, así que se generan varios
# candidatos y se elige el que mejor se ajusta: si no, un "fácil" puede salir
# más largo que un "medio", que es inaceptable en un libro.
_WEAVE_ROUTE_TARGET = {'kids': 0.15, 'easy': 0.25, 'medium': 0.35, 'hard': 0.48}


def generate_weave_maze(rows, cols, difficulty='medium', attempts=14):
    """Laberinto de puentes ajustado al objetivo de ruta de su dificultad.
    Ver `_weave_once` para el algoritmo de carvado con cruces integrados."""
    target = _WEAVE_ROUTE_TARGET.get(difficulty, 0.35)
    best, best_err = None, None
    for _ in range(attempts):
        res = _weave_once(rows, cols, difficulty)
        cells, _, _, sol, _, _ = res
        err = abs(len(sol) / len(cells) - target)
        if best_err is None or err < best_err:
            best, best_err = res, err
        if err <= 0.04:                 # suficientemente cerca del objetivo
            break
    return best

