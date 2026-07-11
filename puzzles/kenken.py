import random
import copy
import math


def _latin_square(n):
    """Generate a random n×n Latin square (values 1..n, no repeats in rows/cols)."""
    grid = [[((r + c) % n) + 1 for c in range(n)] for r in range(n)]
    # Shuffle rows and columns
    rows = list(range(n))
    random.shuffle(rows)
    cols = list(range(n))
    random.shuffle(cols)
    perm = list(range(1, n+1))
    random.shuffle(perm)
    grid = [[grid[r][c] for c in cols] for r in rows]
    # Permute values
    grid = [[perm[v-1] for v in row] for row in grid]
    return grid


def generate_kenken(size=4, difficulty='medium'):
    """
    KenKen / Calcudoku puzzle.
    Returns (puzzle_hints, solution, cages) where:
      puzzle_hints: size×size grid of 0s (empty cells)
      solution: size×size grid with answers
      cages: list of {'cells': [(r,c),...], 'target': int, 'op': '+'/'-'/'*'/'/', 'id': int}
    """
    solution = _latin_square(size)
    cells_assigned = [[False]*size for _ in range(size)]
    cages = []
    cid = 0

    all_cells = [(r, c) for r in range(size) for c in range(size)]
    random.shuffle(all_cells)

    for start in all_cells:
        r0, c0 = start
        if cells_assigned[r0][c0]:
            continue
        cage_size = random.randint(1, min(4, size))
        cage_cells = [(r0, c0)]
        cells_assigned[r0][c0] = True

        for _ in range(cage_size - 1):
            candidates = []
            for r, c in cage_cells:
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < size and 0 <= nc < size and not cells_assigned[nr][nc]:
                        candidates.append((nr, nc))
            if not candidates:
                break
            next_cell = random.choice(candidates)
            cells_assigned[next_cell[0]][next_cell[1]] = True
            cage_cells.append(next_cell)

        values = [solution[r][c] for r, c in cage_cells]

        if len(cage_cells) == 1:
            op, target = '=', values[0]
        elif len(cage_cells) == 2:
            a, b = values[0], values[1]
            # Try division first (prefer cleaner ops)
            ops_choices = ['+', '-', '*']
            if size <= 6 and (a % b == 0 or b % a == 0):
                ops_choices.append('/')
            op = random.choice(ops_choices)
            if op == '+':
                target = a + b
            elif op == '-':
                target = abs(a - b)
            elif op == '*':
                target = a * b
            else:
                target = max(a,b) // min(a,b)
        else:
            # Multi-cell: only + or *
            op = random.choice(['+', '*'])
            if op == '+':
                target = sum(values)
            else:
                target = 1
                for v in values:
                    target *= v

        cages.append({'id': cid, 'cells': cage_cells, 'target': target, 'op': op})
        cid += 1

    puzzle = [[0]*size for _ in range(size)]
    return puzzle, solution, cages


def generate_futoshiki(size=5, difficulty='medium'):
    """
    Futoshiki puzzle.
    Returns (puzzle_grid, solution, inequalities)
    where inequalities is list of {'r1','c1','r2','c2','op': '<'|'>'}
    """
    solution = _latin_square(size)
    puzzle = [[0]*size for _ in range(size)]

    # Reveal some cells based on difficulty
    clue_count = {'easy': size*size//2, 'medium': size*size//4, 'hard': size*size//6}.get(difficulty, size*size//4)
    cells = [(r,c) for r in range(size) for c in range(size)]
    random.shuffle(cells)
    for r, c in cells[:clue_count]:
        puzzle[r][c] = solution[r][c]

    # Generate inequalities between adjacent cells
    inequalities = []
    num_ineq = {'easy': size, 'medium': size*2, 'hard': size*3}.get(difficulty, size*2)
    pairs = []
    for r in range(size):
        for c in range(size):
            if c + 1 < size:
                pairs.append(((r,c),(r,c+1)))
            if r + 1 < size:
                pairs.append(((r,c),(r+1,c)))
    random.shuffle(pairs)
    for (r1,c1),(r2,c2) in pairs[:num_ineq]:
        v1, v2 = solution[r1][c1], solution[r2][c2]
        op = '<' if v1 < v2 else '>'
        inequalities.append({'r1':r1,'c1':c1,'r2':r2,'c2':c2,'op':op})

    return puzzle, solution, inequalities
