import random
import math


def generate_rectangular_maze(rows, cols):
    """
    Classic rectangular maze using recursive backtracking.
    Returns (maze, solution_path) where maze is a dict of walls between cells.
    Cell (r,c). Walls stored as frozenset pairs.
    Returns a simpler representation: 2D grid where 1=wall, 0=passage.
    Grid dimensions: (2*rows+1) x (2*cols+1)
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


def generate_hexagonal_maze(rows, cols):
    """
    Hexagonal maze. Uses offset coordinates.
    Returns (cells, walls, solution_path)
    cells: list of (r, c) hex coordinates
    walls: set of frozenset({cell1, cell2}) — wall present between these cells
    """
    # For hex grid with offset rows
    def hex_neighbors(r, c):
        if r % 2 == 0:
            return [(r-1,c-1),(r-1,c),(r,c-1),(r,c+1),(r+1,c-1),(r+1,c)]
        else:
            return [(r-1,c),(r-1,c+1),(r,c-1),(r,c+1),(r+1,c),(r+1,c+1)]

    cells = [(r, c) for r in range(rows) for c in range(cols)]
    cell_set = set(cells)
    # All walls initially (connections NOT yet carved)
    visited = set()
    walls = set()
    connections = set()

    def carve_hex(r, c):
        visited.add((r, c))
        neighbors = [n for n in hex_neighbors(r, c) if n in cell_set]
        random.shuffle(neighbors)
        for nr, nc in neighbors:
            if (nr, nc) not in visited:
                connections.add(frozenset([(r,c),(nr,nc)]))
                carve_hex(nr, nc)

    carve_hex(0, 0)

    # Walls = all possible connections minus carved ones
    for cell in cells:
        r, c = cell
        for nr, nc in hex_neighbors(r, c):
            if (nr, nc) in cell_set:
                pair = frozenset([(r,c),(nr,nc)])
                if pair not in connections:
                    walls.add(pair)

    # BFS for solution
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
        r, c = cell
        for nr, nc in hex_neighbors(r, c):
            if (nr, nc) in cell_set and (nr, nc) not in seen:
                pair = frozenset([(r,c),(nr,nc)])
                if pair not in walls:
                    seen.add((nr,nc))
                    queue.append(((nr,nc), path+[(nr,nc)]))

    return cells, list(connections), walls, solution_path


def generate_triangular_maze(size):
    """
    Triangular maze on triangular grid.
    Returns cells with triangular adjacency.
    """
    # Triangle grid: each row has increasing triangles
    # For simplicity, use a rectangular grid with diagonal walls
    rows, cols = size, size * 2 - 1
    grid = [[1]*(2*cols+1) for _ in range(2*rows+1)]
    for r in range(rows):
        for c in range(cols):
            grid[2*r+1][2*c+1] = 0
    visited = [[False]*cols for _ in range(rows)]

    def tri_neighbors(r, c):
        nbrs = []
        if c > 0: nbrs.append((r, c-1))
        if c < cols-1: nbrs.append((r, c+1))
        if r > 0 and c % 2 == 1: nbrs.append((r-1, c-1))
        if r < rows-1 and c % 2 == 0: nbrs.append((r+1, c+1))
        return nbrs

    def carve(r, c):
        visited[r][c] = True
        directions = tri_neighbors(r, c)
        random.shuffle(directions)
        for nr, nc in directions:
            if 0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc]:
                wr, wc = 2*r+1+(nr-r), 2*c+1+(nc-c)
                if 0 <= wr < 2*rows+1 and 0 <= wc < 2*cols+1:
                    grid[wr][wc] = 0
                carve(nr, nc)

    carve(0, 0)
    grid[1][0] = 0
    if cols > 0:
        grid[2*rows-1][2*cols] = 0

    return grid, []


def generate_circular_maze(rings, sectors_per_ring=8):
    """
    Circular maze with concentric rings.
    Returns (connections, walls) as sets of cell pairs.
    Each cell is (ring, sector).
    ring 0 = center, ring n = outermost.
    """
    def get_cells(r, s_count):
        return [(r, s) for s in range(s_count)]

    sector_counts = [max(1, sectors_per_ring * (r+1)) for r in range(rings)]
    # Simplify: keep constant sectors per ring for clarity
    sector_counts = [sectors_per_ring] * rings
    all_cells = [(r, s) for r in range(rings) for s in range(sector_counts[r])]
    cell_set = set(all_cells)

    def neighbors(r, s):
        nbrs = []
        sc = sector_counts[r]
        # Clockwise / counter-clockwise
        nbrs.append((r, (s-1) % sc))
        nbrs.append((r, (s+1) % sc))
        # Inner ring
        if r > 0:
            inner_sc = sector_counts[r-1]
            inner_s = int(s * inner_sc / sc)
            nbrs.append((r-1, inner_s % inner_sc))
        # Outer ring
        if r < rings - 1:
            outer_sc = sector_counts[r+1]
            outer_s = int(s * outer_sc / sc)
            nbrs.append((r+1, outer_s % outer_sc))
        return [n for n in nbrs if n in cell_set]

    visited = set()
    connections = set()

    def carve(cell):
        visited.add(cell)
        nbrs = neighbors(*cell)
        random.shuffle(nbrs)
        for nbr in nbrs:
            if nbr not in visited:
                connections.add(frozenset([cell, nbr]))
                carve(nbr)

    carve((0, 0))

    walls = set()
    for cell in all_cells:
        for nbr in neighbors(*cell):
            pair = frozenset([cell, nbr])
            if pair not in connections:
                walls.add(pair)

    # Solution path BFS
    from collections import deque
    start = (0, 0)
    end = (rings-1, 0)
    queue = deque([(start, [start])])
    seen = {start}
    solution_path = []
    while queue:
        cell, path = queue.popleft()
        if cell == end:
            solution_path = path
            break
        for nbr in neighbors(*cell):
            if nbr not in seen and frozenset([cell, nbr]) in connections:
                seen.add(nbr)
                queue.append((nbr, path+[nbr]))

    return all_cells, sector_counts, list(connections), walls, solution_path
