import random
import string


def generate_word_search(words, grid_size=15, difficulty='medium'):
    """
    Word Search puzzle. Places words in grid in 8 directions.
    Returns (puzzle_grid, solution_grid, placed_words, word_positions)
    """
    words = [w.upper().strip() for w in words if w.strip()]
    words.sort(key=len, reverse=True)
    grid = [['.' for _ in range(grid_size)] for _ in range(grid_size)]
    solution = [['.' for _ in range(grid_size)] for _ in range(grid_size)]
    directions = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
    if difficulty == 'easy':
        directions = [(0,1),(1,0),(1,1)]  # fewer directions
    placed_words = []
    word_positions = {}

    for word in words:
        if len(word) > grid_size:
            continue
        placed = False
        attempts = 0
        while not placed and attempts < 200:
            attempts += 1
            dr, dc = random.choice(directions)
            # Random start that fits the word
            if dr == 0:
                r = random.randint(0, grid_size - 1)
                if dc == 1:
                    c = random.randint(0, grid_size - len(word))
                else:
                    c = random.randint(len(word) - 1, grid_size - 1)
            elif dc == 0:
                c = random.randint(0, grid_size - 1)
                if dr == 1:
                    r = random.randint(0, grid_size - len(word))
                else:
                    r = random.randint(len(word) - 1, grid_size - 1)
            else:
                if dr == 1:
                    r = random.randint(0, grid_size - len(word))
                else:
                    r = random.randint(len(word) - 1, grid_size - 1)
                if dc == 1:
                    c = random.randint(0, grid_size - len(word))
                else:
                    c = random.randint(len(word) - 1, grid_size - 1)

            # Check if fits
            ok = True
            for i, ch in enumerate(word):
                nr, nc = r + i*dr, c + i*dc
                if not (0 <= nr < grid_size and 0 <= nc < grid_size):
                    ok = False
                    break
                if grid[nr][nc] not in ('.', ch):
                    ok = False
                    break
            if ok:
                cells = []
                for i, ch in enumerate(word):
                    nr, nc = r + i*dr, c + i*dc
                    grid[nr][nc] = ch
                    solution[nr][nc] = ch
                    cells.append((nr, nc))
                placed_words.append(word)
                word_positions[word] = {'cells': cells, 'direction': (dr, dc)}
                placed = True

    # Fill remaining with random letters
    letters = string.ascii_uppercase
    for r in range(grid_size):
        for c in range(grid_size):
            if grid[r][c] == '.':
                grid[r][c] = random.choice(letters)
                solution[r][c] = grid[r][c].lower()  # lowercase = filler in solution

    return grid, solution, placed_words, word_positions


def generate_crossword(words, clues=None, grid_size=21):
    """
    Traditional crossword puzzle. Words cross at shared letters.
    Returns (puzzle_grid, solution_grid, across_entries, down_entries)
    """
    words_clues = {}
    if clues and len(clues) == len(words):
        for w, c in zip(words, clues):
            words_clues[w.upper().strip()] = c
    else:
        for w in words:
            words_clues[w.upper().strip()] = f"Pista para {w.upper().strip()}"

    words = list(words_clues.keys())
    words = [w for w in words if 2 <= len(w) <= grid_size - 2]
    words.sort(key=len, reverse=True)

    if not words:
        return None, None, [], []

    # Grid: None=wall, ''=open cell
    grid = [[None] * grid_size for _ in range(grid_size)]
    placed = []  # list of {'word', 'row', 'col', 'direction', 'number'}

    def can_place(word, r, c, direction):
        dr, dc = (0, 1) if direction == 'across' else (1, 0)
        # Check boundaries
        end_r = r + dr * (len(word) - 1)
        end_c = c + dc * (len(word) - 1)
        if not (0 <= end_r < grid_size and 0 <= end_c < grid_size):
            return False
        # Check before and after
        br, bc = r - dr, c - dc
        if 0 <= br < grid_size and 0 <= bc < grid_size and grid[br][bc] is not None:
            return False
        ar, ac = r + dr * len(word), c + dc * len(word)
        if 0 <= ar < grid_size and 0 <= ac < grid_size and grid[ar][ac] is not None:
            return False
        # Check each cell
        for i, ch in enumerate(word):
            nr, nc = r + i*dr, c + i*dc
            existing = grid[nr][nc]
            if existing is None:
                # Check perpendicular neighbors don't create new adjacencies
                if direction == 'across':
                    if (nr > 0 and grid[nr-1][nc] is not None) or (nr < grid_size-1 and grid[nr+1][nc] is not None):
                        # OK if crossing an existing word
                        if existing is None:
                            return False
                else:
                    if (nc > 0 and grid[nr][nc-1] is not None) or (nc < grid_size-1 and grid[nr][nc+1] is not None):
                        if existing is None:
                            return False
            elif existing != ch:
                return False
        return True

    def place_word(word, r, c, direction, number):
        dr, dc = (0, 1) if direction == 'across' else (1, 0)
        for i, ch in enumerate(word):
            grid[r + i*dr][c + i*dc] = ch
        placed.append({'word': word, 'row': r, 'col': c, 'direction': direction, 'number': number, 'clue': words_clues.get(word, '')})

    # Place first word in center
    first = words[0]
    start_r = grid_size // 2
    start_c = (grid_size - len(first)) // 2
    place_word(first, start_r, start_c, 'across', 1)
    number = 2

    for word in words[1:]:
        best = None
        best_score = -1
        for p in placed:
            pr, pc = p['row'], p['col']
            pd = p['direction']
            pword = p['word']
            # Try to cross with this word
            for i, pw_ch in enumerate(pword):
                for j, w_ch in enumerate(word):
                    if pw_ch == w_ch:
                        if pd == 'across':
                            # New word goes down, crossing at column pc+i
                            new_r = pr - j
                            new_c = pc + i
                            direction = 'down'
                        else:
                            # New word goes across, crossing at row pr+i
                            new_r = pr + i
                            new_c = pc - j
                            direction = 'across'
                        if can_place(word, new_r, new_c, direction):
                            score = len(word)  # prefer longer words crossing
                            if score > best_score:
                                best_score = score
                                best = (word, new_r, new_c, direction)
        if best:
            place_word(best[0], best[1], best[2], best[3], number)
            number += 1

    if not placed:
        return None, None, [], []

    # Build puzzle grid (None=black, letter=letter)
    puzzle_grid = [[None] * grid_size for _ in range(grid_size)]
    solution_grid = [[None] * grid_size for _ in range(grid_size)]
    for r in range(grid_size):
        for c in range(grid_size):
            if grid[r][c] is not None:
                solution_grid[r][c] = grid[r][c]
                puzzle_grid[r][c] = ''  # empty white cell

    # Assign numbers
    cell_numbers = {}
    num = 1
    for r in range(grid_size):
        for c in range(grid_size):
            if puzzle_grid[r][c] is None:
                continue
            starts_across = (c == 0 or puzzle_grid[r][c-1] is None) and (c + 1 < grid_size and puzzle_grid[r][c+1] is not None)
            starts_down = (r == 0 or puzzle_grid[r-1][c] is None) and (r + 1 < grid_size and puzzle_grid[r+1][c] is not None)
            if starts_across or starts_down:
                cell_numbers[(r, c)] = num
                num += 1

    across_entries = []
    down_entries = []
    for entry in placed:
        cell_num = cell_numbers.get((entry['row'], entry['col']), None)
        if cell_num:
            e = {'number': cell_num, 'word': entry['word'], 'clue': entry['clue'],
                 'row': entry['row'], 'col': entry['col']}
            if entry['direction'] == 'across':
                across_entries.append(e)
            else:
                down_entries.append(e)

    across_entries.sort(key=lambda x: x['number'])
    down_entries.sort(key=lambda x: x['number'])

    return puzzle_grid, solution_grid, across_entries, down_entries, cell_numbers
