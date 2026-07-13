import random
import copy
from collections import deque


# ─── HASHI (Bridges) ────────────────────────────────────────────────────────

_HASHI_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def generate_hashi(rows=14, cols=10, difficulty='medium'):
    """
    Genera un Hashi VÁLIDO: se construye una red de islas CONECTADA (un solo grafo)
    con puentes rectos que NO se cruzan, creciendo desde una isla semilla. Cada isla
    lleva su número = total de puentes que salen de ella.
    Returns (islands, bridges): islands=[{id,row,col,count}], bridges=[{from,to,count}].
    """
    island_at = {}          # (r,c) -> id
    islands = []            # {id,row,col,count}
    bridges = {}            # frozenset(id1,id2) -> count (1 o 2)
    seg = set()             # celdas ocupadas por algún puente (evita cruces/solapes)

    def add_island(r, c):
        iid = len(islands)
        islands.append({'id': iid, 'row': r, 'col': c, 'count': 0})
        island_at[(r, c)] = iid
        return iid

    def between(r1, c1, r2, c2):
        if r1 == r2:
            s = 1 if c2 > c1 else -1
            return [(r1, c) for c in range(c1 + s, c2, s)]
        s = 1 if r2 > r1 else -1
        return [(r, c1) for r in range(r1 + s, r2, s)]

    def adjacent_to_island(r, c):
        return any((r + dr, c + dc) in island_at for dr, dc in _HASHI_DIRS)

    def path_clear(r1, c1, r2, c2):
        return all((r, c) not in island_at and (r, c) not in seg
                   for (r, c) in between(r1, c1, r2, c2))

    def place_bridge(a, b, cnt):
        bridges[frozenset([a['id'], b['id']])] = cnt
        for (r, c) in between(a['row'], a['col'], b['row'], b['col']):
            seg.add((r, c))
        a['count'] += cnt
        b['count'] += cnt

    # Parámetros por dificultad (según la guía de densidad):
    density     = {'easy': 0.13, 'medium': 0.11, 'hard': 0.09}.get(difficulty, 0.11)
    max_reach   = {'easy': 4,    'medium': 6,    'hard': 9}.get(difficulty, 6)   # largo máx. de puente
    p_double    = {'easy': 0.60, 'medium': 0.40, 'hard': 0.25}.get(difficulty, 0.40)
    target = max(4, int(rows * cols * density))

    add_island(random.randrange(rows), random.randrange(cols))
    guard = 0
    while len(islands) < target and guard < target * 80:
        guard += 1
        E = random.choice(islands)
        if E['count'] >= 8:
            continue
        dr, dc = random.choice(_HASHI_DIRS)
        r, c = E['row'] + dr, E['col'] + dc
        dist = 1
        cands = []
        while 0 <= r < rows and 0 <= c < cols and dist <= max_reach:
            if (r, c) in island_at or (r, c) in seg:
                break
            if dist >= 2 and not adjacent_to_island(r, c):
                cands.append((r, c))
            r += dr; c += dc; dist += 1
        if not cands:
            continue
        L = cands[0] if difficulty == 'easy' else random.choice(cands)
        if not path_clear(E['row'], E['col'], L[0], L[1]):
            continue
        cnt = 2 if random.random() < p_double else 1
        cnt = min(cnt, 8 - E['count'])
        if cnt < 1:
            continue
        lid = add_island(L[0], L[1])
        place_bridge(E, islands[lid], cnt)

    # Aristas extra entre islas ya visibles (sin cruzar) para enriquecer las pistas.
    extra_target = int(len(islands) * 0.30)
    added = tries = 0
    while added < extra_target and tries < len(islands) * 40:
        tries += 1
        A = random.choice(islands)
        dr, dc = random.choice(_HASHI_DIRS)
        r, c = A['row'] + dr, A['col'] + dc
        dist = 1
        found = None
        while 0 <= r < rows and 0 <= c < cols and dist <= max_reach:
            if (r, c) in island_at:
                found = island_at[(r, c)]
                break
            if (r, c) in seg:
                break
            r += dr; c += dc; dist += 1
        if found is None:
            continue
        B = islands[found]
        pair = frozenset([A['id'], B['id']])
        if pair in bridges:
            continue
        if not path_clear(A['row'], A['col'], B['row'], B['col']):
            continue
        cnt = 2 if random.random() < p_double else 1
        cnt = min(cnt, 8 - A['count'], 8 - B['count'])
        if cnt < 1:
            continue
        place_bridge(A, B, cnt)
        added += 1

    if len(islands) < 2:
        return generate_hashi(rows, cols, difficulty)   # reintento raro

    bridge_list = [{'from': min(p), 'to': max(p), 'count': cnt}
                   for p, cnt in bridges.items()]
    return islands, bridge_list


# ─── NURIKABE ────────────────────────────────────────────────────────────────

_NB_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _nurikabe_ocean_ok(iid, rows, cols):
    """El océano (celdas con iid == -1) debe ser UNA región conectada y SIN bloques
    2×2 (piscinas)."""
    ocean = [(r, c) for r in range(rows) for c in range(cols) if iid[r][c] == -1]
    if len(ocean) < 2:
        return False
    # Sin piscinas 2×2
    for r in range(rows - 1):
        for c in range(cols - 1):
            if (iid[r][c] == -1 and iid[r + 1][c] == -1
                    and iid[r][c + 1] == -1 and iid[r + 1][c + 1] == -1):
                return False
    # Conectado
    seen = {ocean[0]}
    stack = [ocean[0]]
    while stack:
        r, c = stack.pop()
        for dr, dc in _NB_DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and iid[nr][nc] == -1 and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))
    return len(seen) == len(ocean)


def _creates_pool(ocean, r, c, rows, cols):
    """True si marcar (r,c) como océano completa un bloque 2×2 de océano."""
    for tr in (r - 1, r):
        for tc in (c - 1, c):
            if 0 <= tr and tr + 1 < rows and 0 <= tc and tc + 1 < cols:
                if (ocean[tr][tc] and ocean[tr + 1][tc]
                        and ocean[tr][tc + 1] and ocean[tr + 1][tc + 1]):
                    return True
    return False


def _white_components(ocean, rows, cols):
    """Componentes conexas de celdas blancas (islas)."""
    seen = [[False] * cols for _ in range(rows)]
    comps = []
    for r in range(rows):
        for c in range(cols):
            if not ocean[r][c] and not seen[r][c]:
                comp = [(r, c)]
                seen[r][c] = True
                st = [(r, c)]
                while st:
                    rr, cc = st.pop()
                    for dr, dc in _NB_DIRS:
                        nr, nc = rr + dr, cc + dc
                        if (0 <= nr < rows and 0 <= nc < cols
                                and not ocean[nr][nc] and not seen[nr][nc]):
                            seen[nr][nc] = True
                            comp.append((nr, nc))
                            st.append((nr, nc))
                comps.append(comp)
    return comps


def _ocean_connected(white, rows, cols):
    """El océano (celdas NO blancas) es una sola región conectada."""
    ocean = [(r, c) for r in range(rows) for c in range(cols) if not white[r][c]]
    if not ocean:
        return False
    seen = {ocean[0]}
    st = [ocean[0]]
    while st:
        r, c = st.pop()
        for dr, dc in _NB_DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not white[nr][nc] and (nr, nc) not in seen:
                seen.add((nr, nc))
                st.append((nr, nc))
    return len(seen) == len(ocean)


def _white_islands(white, rows, cols):
    """Componentes conexas de celdas blancas (cada una = una isla)."""
    seen = [[False] * cols for _ in range(rows)]
    comps = []
    for r in range(rows):
        for c in range(cols):
            if white[r][c] and not seen[r][c]:
                comp = [(r, c)]
                seen[r][c] = True
                st = [(r, c)]
                while st:
                    rr, cc = st.pop()
                    for dr, dc in _NB_DIRS:
                        nr, nc = rr + dr, cc + dc
                        if (0 <= nr < rows and 0 <= nc < cols
                                and white[nr][nc] and not seen[nr][nc]):
                            seen[nr][nc] = True
                            comp.append((nr, nc))
                            st.append((nr, nc))
                comps.append(comp)
    return comps


def _try_nurikabe(rows, cols, white_ratio, max_isize):
    """Siembra una blanca en cada malla (r par, c par): garantiza que TODO bloque 2×2
    tiene al menos una blanca ⇒ el océano nunca forma piscinas 2×2. Luego hace crecer
    las blancas (sin desconectar el océano). Las componentes blancas son las islas."""
    white = [[False] * cols for _ in range(rows)]
    frontier = set()
    for r in range(0, rows, 2):
        for c in range(0, cols, 2):
            white[r][c] = True
    white_count = sum(row.count(True) for row in white)
    # Frontera = celdas de océano adyacentes a alguna blanca (se mantiene incremental)
    for r in range(rows):
        for c in range(cols):
            if white[r][c]:
                for dr, dc in _NB_DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and not white[nr][nc]:
                        frontier.add((nr, nc))
    target = int(rows * cols * white_ratio)

    while white_count < target and frontier:
        r, c = random.choice(tuple(frontier))
        frontier.discard((r, c))
        white[r][c] = True
        if not _ocean_connected(white, rows, cols):
            white[r][c] = False        # habría partido el océano: descartar esta celda
            continue
        white_count += 1
        for dr, dc in _NB_DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not white[nr][nc]:
                frontier.add((nr, nc))

    islands = _white_islands(white, rows, cols)
    if len(islands) < 3 or any(len(i) > max_isize for i in islands):
        return None

    solution = [[0] * cols for _ in range(rows)]   # 0 = negro (océano)
    puzzle = [[None] * cols for _ in range(rows)]
    for isl in islands:
        for (r, c) in isl:
            solution[r][c] = -1
        cr, cc = random.choice(isl)                # celda-pista al azar
        solution[cr][cc] = len(isl)
        puzzle[cr][cc] = len(isl)
    return puzzle, solution


def generate_nurikabe(rows=15, cols=10, difficulty='medium'):
    """
    Nurikabe válido: islas blancas (cada una con su número = tamaño) separadas entre
    sí por un único "muro"/océano negro conectado y SIN bloques 2×2.
    Returns (puzzle, solution): puzzle solo muestra las pistas; en solution
    0=negro (océano), n=celda-pista, -1=blanca de isla.
    """
    # "difícil" = islas más grandes (máximo por isla mayor); la densidad se mantiene
    # moderada para que el océano siga conectado y la generación sea rápida.
    white_ratio = {'easy': 0.40, 'medium': 0.44, 'hard': 0.47}.get(difficulty, 0.44)
    max_isize = {'easy': 5, 'medium': 7, 'hard': 10}.get(difficulty, 7)
    for _ in range(150):
        res = _try_nurikabe(rows, cols, white_ratio, max_isize)
        if res is not None:
            return res
    # Relajar progresivamente hasta garantizar un tablero válido.
    for ratio, mx in [(0.42, 12), (0.40, 14), (0.38, 16)]:
        for _ in range(80):
            res = _try_nurikabe(rows, cols, ratio, mx)
            if res is not None:
                return res
    return [[None] * cols for _ in range(rows)], [[0] * cols for _ in range(rows)]


# ─── HITORI ──────────────────────────────────────────────────────────────────

def _hitori_white_connected(black, rows, cols):
    """True si todas las celdas blancas forman una sola región conectada."""
    whites = [(r, c) for r in range(rows) for c in range(cols) if not black[r][c]]
    if not whites:
        return False
    seen = {whites[0]}
    stack = [whites[0]]
    while stack:
        r, c = stack.pop()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not black[nr][nc] and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))
    return len(seen) == len(whites)


def _choose_hitori_blacks(rows, cols, ratio=0.20):
    """Elige celdas a tachar cumpliendo las reglas de Hitori:
    - ninguna dos negras ortogonalmente adyacentes,
    - las blancas quedan todas conectadas."""
    black = [[False] * cols for _ in range(rows)]
    target = int(rows * cols * ratio)
    cells = [(r, c) for r in range(rows) for c in range(cols)]
    random.shuffle(cells)
    count = 0
    for r, c in cells:
        if count >= target:
            break
        # No puede ser adyacente a otra negra
        if any(0 <= r + dr < rows and 0 <= c + dc < cols and black[r + dr][c + dc]
               for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]):
            continue
        black[r][c] = True
        if not _hitori_white_connected(black, rows, cols):
            black[r][c] = False   # rompería la conectividad de las blancas
            continue
        count += 1
    return black


def generate_hitori(rows=10, cols=None):
    """
    Hitori válido. Reglas: tachar (negro) celdas para que ninguna fila/columna tenga
    números repetidos entre las blancas; las negras no pueden tocarse ortogonalmente;
    las blancas deben quedar conectadas.

    Estrategia: se parte de una base SIN repeticiones (blancas válidas), se eligen
    las celdas negras (no adyacentes + blancas conectadas) y se cambia el valor de
    cada negra por un duplicado de una blanca de su fila o columna (así el jugador
    deduce que debe tacharla).

    Returns (puzzle, solution) con solution[r][c] = -1 en las negras, valor en blancas.
    """
    if cols is None:
        cols = rows
    M = max(rows, cols)
    perm = list(range(1, M + 1))
    random.shuffle(perm)
    # Base tipo latino: perm[(r+c) % M] => sin repetidos en ninguna fila ni columna
    base = [[perm[(r + c) % M] for c in range(cols)] for r in range(rows)]

    black = _choose_hitori_blacks(rows, cols)

    puzzle = [row[:] for row in base]
    for r in range(rows):
        for c in range(cols):
            if not black[r][c]:
                continue
            # Duplicar el valor de una blanca de la misma fila o columna
            cands = [base[r][cc] for cc in range(cols) if cc != c and not black[r][cc]]
            cands += [base[rr][c] for rr in range(rows) if rr != r and not black[rr][c]]
            if cands:
                puzzle[r][c] = random.choice(cands)

    solution = [[-1 if black[r][c] else base[r][c] for c in range(cols)]
                for r in range(rows)]
    return puzzle, solution


# ─── AKARI (Light Up) ────────────────────────────────────────────────────────

def generate_akari(rows=7, cols=7, num_blacks=8):
    """
    Akari / Light Up puzzle.
    Returns (puzzle, solution) where:
      puzzle: grid of None (white) or int 0-4 (black with count) or -1 (black, no count)
      solution: same grid with lightbulb positions marked as 'L'
    """
    grid = [[None]*cols for _ in range(rows)]
    solution = [[None]*cols for _ in range(rows)]

    # Place black cells randomly
    black_cells = set()
    all_cells = [(r,c) for r in range(rows) for c in range(cols)]
    random.shuffle(all_cells)
    for r, c in all_cells[:num_blacks]:
        black_cells.add((r,c))
        grid[r][c] = -1  # black, count TBD
        solution[r][c] = -1

    # Place lightbulbs on white cells (greedy: try to illuminate all)
    white_cells = [(r,c) for r in range(rows) for c in range(cols) if (r,c) not in black_cells]
    illuminated = set()
    bulbs = set()

    def illuminate(r, c):
        cells = {(r,c)}
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            nr, nc = r+dr, c+dc
            while 0 <= nr < rows and 0 <= nc < cols and (nr,nc) not in black_cells:
                cells.add((nr,nc))
                nr += dr
                nc += dc
        return cells

    random.shuffle(white_cells)
    for r, c in white_cells:
        if (r,c) not in illuminated:
            lit = illuminate(r, c)
            if not any(b in lit for b in bulbs if b != (r,c)):
                bulbs.add((r,c))
                illuminated |= lit

    # Assign counts to black cells
    for r, c in black_cells:
        count = sum(1 for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]
                    if (r+dr, c+dc) in bulbs)
        if random.random() < 0.6:  # show number on ~60% of blacks
            grid[r][c] = count
            solution[r][c] = count
        # else -1 (no clue)

    # Mark bulbs in solution
    for r, c in bulbs:
        solution[r][c] = 'L'

    return grid, solution


# ─── MASYU (Pearl) ───────────────────────────────────────────────────────────

def generate_masyu(rows=7, cols=7):
    """
    Masyu pearl puzzle.
    Returns (puzzle, solution_path, pearls)
    puzzle: grid showing only pearl positions ('B'=black, 'W'=white, None=empty)
    solution_path: list of (r,c) forming the loop
    """
    # Generate a random Hamiltonian-like loop on a subset of the grid
    # Simplified: random walk loop
    path = _random_loop(rows, cols)
    if not path:
        return [[None]*cols for _ in range(rows)], [], []

    path_set = set(path)
    turns = []
    for i in range(len(path)):
        prev = path[(i-1) % len(path)]
        curr = path[i]
        nxt = path[(i+1) % len(path)]
        d1 = (curr[0]-prev[0], curr[1]-prev[1])
        d2 = (nxt[0]-curr[0], nxt[1]-curr[1])
        if d1 != d2:
            turns.append(curr)

    # Assign pearls
    pearls = {}
    straights = [p for p in path if p not in set(turns)]
    for p in random.sample(turns, min(len(turns), max(2, len(turns)//2))):
        pearls[p] = 'B'  # black = must turn here
    for p in random.sample(straights, min(len(straights), max(2, len(straights)//3))):
        pearls[p] = 'W'  # white = must go straight

    puzzle = [[None]*cols for _ in range(rows)]
    for (r, c), ptype in pearls.items():
        puzzle[r][c] = ptype

    return puzzle, path, pearls


def _random_loop(rows, cols):
    """Generate a random closed loop on the grid."""
    # Start with a simple rectangular loop in the center
    r1, c1 = rows//4, cols//4
    r2, c2 = 3*rows//4, 3*cols//4
    path = []
    for c in range(c1, c2+1):
        path.append((r1, c))
    for r in range(r1+1, r2+1):
        path.append((r, c2))
    for c in range(c2-1, c1-1, -1):
        path.append((r2, c))
    for r in range(r2-1, r1, -1):
        path.append((r, c1))
    return path
