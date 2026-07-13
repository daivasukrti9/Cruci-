import random
import copy
from collections import deque


# ─── HASHI (Bridges) ────────────────────────────────────────────────────────

def generate_hashi(rows=7, cols=7, num_islands=None):
    """
    Generate a Hashi puzzle.
    Returns (islands, bridges) where:
      islands: list of {'id','row','col','count'}
      bridges: list of {'from','to','count'} (solution)
    The puzzle shows only islands with their counts; player draws bridges.
    """
    if num_islands is None:
        num_islands = max(4, (rows * cols) // 5)

    # Place islands on grid ensuring no two are adjacent
    island_positions = set()
    attempts = 0
    while len(island_positions) < num_islands and attempts < 10000:
        attempts += 1
        r, c = random.randint(0, rows-1), random.randint(0, cols-1)
        if all(abs(r-ir) > 1 or abs(c-ic) > 1 for ir, ic in island_positions):
            island_positions.add((r, c))

    islands = [{'id': i, 'row': r, 'col': c, 'count': 0}
               for i, (r, c) in enumerate(sorted(island_positions))]

    pos_to_island = {(isl['row'], isl['col']): isl['id'] for isl in islands}

    def find_neighbors(isl_id):
        isl = islands[isl_id]
        nbrs = []
        # Horizontal: scan right
        c = isl['col'] + 1
        while c < cols:
            if (isl['row'], c) in pos_to_island:
                nbrs.append(pos_to_island[(isl['row'], c)])
                break
            c += 1
        # Horizontal: scan left
        c = isl['col'] - 1
        while c >= 0:
            if (isl['row'], c) in pos_to_island:
                nbrs.append(pos_to_island[(isl['row'], c)])
                break
            c -= 1
        # Vertical: scan down
        r = isl['row'] + 1
        while r < rows:
            if (r, isl['col']) in pos_to_island:
                nbrs.append(pos_to_island[(r, isl['col'])])
                break
            r += 1
        # Vertical: scan up
        r = isl['row'] - 1
        while r >= 0:
            if (r, isl['col']) in pos_to_island:
                nbrs.append(pos_to_island[(r, isl['col'])])
                break
            r -= 1
        return list(set(nbrs))

    # Generate random bridges
    bridges = []
    bridge_set = {}  # frozenset({id1,id2}) -> count

    for isl_id in range(len(islands)):
        nbrs = find_neighbors(isl_id)
        for nbr_id in nbrs:
            pair = frozenset([isl_id, nbr_id])
            if pair not in bridge_set and random.random() < 0.5:
                cnt = random.randint(1, 2)
                bridge_set[pair] = cnt
                bridges.append({'from': min(isl_id,nbr_id), 'to': max(isl_id,nbr_id), 'count': cnt})

    # Update island counts
    for b in bridges:
        islands[b['from']]['count'] += b['count']
        islands[b['to']]['count'] += b['count']

    # Remove islands with 0 bridges
    connected_ids = set()
    for b in bridges:
        connected_ids.add(b['from'])
        connected_ids.add(b['to'])

    islands = [isl for isl in islands if isl['id'] in connected_ids]
    # Ensure count >= 1
    for isl in islands:
        isl['count'] = max(1, min(8, isl['count']))

    return islands, bridges


# ─── NURIKABE ────────────────────────────────────────────────────────────────

def generate_nurikabe(rows=7, cols=7, num_islands=4):
    """
    Nurikabe: partition grid into white islands and a black river.
    Returns (puzzle, solution) where values are 0=black, positive=island_size (clue cells), -1=white (non-clue)
    """
    grid = [[0]*cols for _ in range(rows)]  # 0 = black
    islands = []
    used = set()

    for _ in range(num_islands):
        # Pick random start not in used
        candidates = [(r,c) for r in range(rows) for c in range(cols) if (r,c) not in used]
        if not candidates:
            break
        start = random.choice(candidates)
        size = random.randint(1, 4)
        island_cells = [start]
        used.add(start)
        for _ in range(size - 1):
            border = []
            for r, c in island_cells:
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < rows and 0 <= nc < cols and (nr,nc) not in used:
                        border.append((nr,nc))
            if not border:
                break
            nc_cell = random.choice(border)
            island_cells.append(nc_cell)
            used.add(nc_cell)
        islands.append({'cells': island_cells, 'size': len(island_cells)})

    # Build solution
    solution = [[0]*cols for _ in range(rows)]  # 0=black by default
    for isl in islands:
        for r, c in isl['cells']:
            solution[r][c] = -1  # white (part of island)
        # Mark clue cell (first cell) with size
        r0, c0 = isl['cells'][0]
        solution[r0][c0] = isl['size']

    # Build puzzle (only clue cells visible, rest empty for player)
    puzzle = [[None]*cols for _ in range(rows)]
    for isl in islands:
        r0, c0 = isl['cells'][0]
        puzzle[r0][c0] = isl['size']

    return puzzle, solution


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
