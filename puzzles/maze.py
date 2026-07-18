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


def generate_weave_maze(rows, cols, difficulty='medium'):
    """
    Laberinto de PUENTES (weave): un laberinto rectangular normal (DFS) al que,
    tras la carva inicial, se le añaden "saltos": en cada celda recta (grado 2,
    con sus dos conexiones en un mismo eje, sin giro) se puede tender un puente
    perpendicular que conecta DIRECTAMENTE a sus dos vecinas del otro eje,
    pasando por ENCIMA de esa celda sin tocarla — el pasillo original bajo el
    puente se conserva intacto. Así el camino puede cruzarse a sí mismo sin
    intersección real, como un paso elevado.
    Returns (cells, connections, bridges, solution_path, rows, cols).
    bridges: dict {mid_cell: axis_bajo_el_puente} ('h' o 'v').
    """
    cells = [(r, c) for r in range(rows) for c in range(cols)]
    cell_set = set(cells)

    def neighbors4(r, c):
        return [(r, c-1), (r, c+1), (r-1, c), (r+1, c)]

    visited = set()
    connections = set()

    def carve(r, c):
        visited.add((r, c))
        dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        random.shuffle(dirs)
        for dr, dc in dirs:
            nr, nc = r+dr, c+dc
            if (nr, nc) in cell_set and (nr, nc) not in visited:
                connections.add(frozenset([(r, c), (nr, nc)]))
                carve(nr, nc)

    carve(0, 0)

    # Puentes: siempre hay una fracción mínima para que el laberinto conserve
    # su identidad de "weave" incluso en difícil (menos puentes = más difícil,
    # pero nunca cero).
    fraction = max(0.12, _BRAID_BY_DIFFICULTY.get(difficulty, 0.05))
    bridges = {}
    candidates = list(cells)
    random.shuffle(candidates)

    def _bridge_spec(r, c):
        """Si la celda (r,c) es RECTA (grado 2 en un mismo eje), devuelve
        (axis, pr1, pr2) del puente perpendicular que puede tender; si no es
        apta (giro, cruce, o fuera de la rejilla), devuelve None."""
        conns_here = [n for n in neighbors4(r, c)
                      if n in cell_set and frozenset([(r, c), n]) in connections]
        if len(conns_here) != 2:
            return None
        (r1, c1), (r2, c2) = conns_here
        if r1 == r2 == r and {c1, c2} == {c-1, c+1}:
            axis, perp = 'h', [(r-1, c), (r+1, c)]
        elif c1 == c2 == c and {r1, r2} == {r-1, r+1}:
            axis, perp = 'v', [(r, c-1), (r, c+1)]
        else:
            return None  # celda con giro: no es apta para un puente
        pr1, pr2 = perp
        if pr1 not in cell_set or pr2 not in cell_set:
            return None
        return axis, pr1, pr2

    def _place_bridge(r, c, axis, pr1, pr2):
        bridges[(r, c)] = axis
        connections.add(frozenset([pr1, pr2]))

    for (r, c) in candidates:
        spec = _bridge_spec(r, c)
        if spec is None:
            continue
        axis, pr1, pr2 = spec
        if pr1 in bridges or pr2 in bridges:
            continue  # no apilar puentes contiguos
        if random.random() > fraction:
            continue
        _place_bridge(r, c, axis, pr1, pr2)

    # Garantiza AL MENOS un puente (identidad "weave" incluso en difícil): si el
    # azar no colocó ninguno, coloca el primer candidato elegible que quede.
    if not bridges:
        for (r, c) in candidates:
            spec = _bridge_spec(r, c)
            if spec is not None:
                _place_bridge(r, c, *spec)
                break

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

