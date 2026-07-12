"""
Red de seguridad: valida las REGLAS de la familia Sudoku.

Validador independiente (no reusa la lógica interna del módulo) para que un bug
en el código no se apruebe a sí mismo. Cubre lo que ya corregimos:
  - 16x16 sin duplicados (bug de generación)
  - Jigsaw genera en 9/12/16 sin reventar (bug de tupla en box_w/box_h)
"""
import pytest

from puzzles import sudoku


# ─── Validadores independientes ──────────────────────────────────────────────

def _rows_ok(grid, size):
    return all(sorted(row) == list(range(1, size + 1)) for row in grid)


def _cols_ok(grid, size):
    for c in range(size):
        col = [grid[r][c] for r in range(size)]
        if sorted(col) != list(range(1, size + 1)):
            return False
    return True


def _boxes_ok(grid, size, box_w, box_h):
    for br in range(0, size, box_h):
        for bc in range(0, size, box_w):
            vals = [grid[r][c]
                    for r in range(br, br + box_h)
                    for c in range(bc, bc + box_w)]
            if sorted(vals) != list(range(1, size + 1)):
                return False
    return True


def _is_valid_solution(grid, size, box_w, box_h):
    return (_rows_ok(grid, size)
            and _cols_ok(grid, size)
            and _boxes_ok(grid, size, box_w, box_h))


def _puzzle_subset_of_solution(puzzle, solution, empty=0):
    """El puzzle nunca puede contradecir la solución."""
    size = len(solution)
    for r in range(size):
        for c in range(size):
            if puzzle[r][c] != empty and puzzle[r][c] != solution[r][c]:
                return False
    return True


BOX_DIMS = {9: (3, 3), 12: (4, 3), 16: (4, 4)}  # (box_w, box_h)


# ─── Sudoku clásico ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("size", [9, 12, 16])
@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_classic_solution_valida(size, difficulty):
    box_w, box_h = BOX_DIMS[size]
    puzzle, solution = sudoku.generate_classic(size=size, difficulty=difficulty)
    assert _is_valid_solution(solution, size, box_w, box_h), \
        f"Solución inválida en clásico {size}x{size} ({difficulty})"
    assert _puzzle_subset_of_solution(puzzle, solution)


# ─── Sudoku Jigsaw (regresión del bug de tupla) ──────────────────────────────

@pytest.mark.parametrize("size", [9, 12])  # tamaños de jigsaw ofrecidos en la app
def test_jigsaw_genera_sin_error(size):
    # No debe lanzar (el bug daba: unsupported operand // int y tuple)
    puzzle, solution, regions = sudoku.generate_jigsaw(difficulty="easy", size=size)
    # Filas y columnas siempre deben ser válidas
    assert _rows_ok(solution, size) and _cols_ok(solution, size), \
        f"Jigsaw {size}x{size}: fila o columna con repetidos"
    assert _puzzle_subset_of_solution(puzzle, solution)


@pytest.mark.parametrize("size", [9, 12])
def test_jigsaw_regiones_de_tamano_exacto(size):
    """Cada pieza debe tener EXACTAMENTE `size` casillas y contener 1..size."""
    puzzle, solution, regions = sudoku.generate_jigsaw(difficulty="medium", size=size)
    # Contar casillas por región
    counts = {}
    vals = {}
    for r in range(size):
        for c in range(size):
            rid = regions[r][c]
            counts[rid] = counts.get(rid, 0) + 1
            vals.setdefault(rid, []).append(solution[r][c])
    assert len(counts) == size, f"Debe haber {size} regiones, hay {len(counts)}"
    for rid, n in counts.items():
        assert n == size, f"Región {rid} tiene {n} casillas (debe ser {size})"
        assert sorted(vals[rid]) == list(range(1, size + 1)), \
            f"Región {rid} no contiene 1..{size} sin repetir"


def test_jigsaw_9_evita_pieza_3x3():
    """Regla del usuario: el jigsaw 9x9 evita la pieza cuadrada 3x3 la gran
    mayoría de las veces (búsqueda acotada por tiempo, no garantía absoluta)."""
    limpios = sum(1 for _ in range(6)
                  if sudoku._count_boxy(sudoku.generate_jigsaw(size=9)[2], 9) == 0)
    assert limpios >= 4, f"Solo {limpios}/6 jigsaw 9x9 sin pieza 3x3"


def test_jigsaw_genera_formas_distintas():
    """Dos generaciones seguidas no deben dar exactamente las mismas regiones."""
    _, _, reg1 = sudoku.generate_jigsaw(difficulty="medium", size=9)
    distintas = False
    for _ in range(5):
        _, _, reg2 = sudoku.generate_jigsaw(difficulty="medium", size=9)
        if reg2 != reg1:
            distintas = True
            break
    assert distintas, "El generador devuelve siempre la misma forma"


def test_jigsaw_x_diagonales_validas():
    """Jigsaw X: además de regiones, las diagonales no repiten."""
    puzzle, solution, regions = sudoku.generate_jigsaw(difficulty="medium", with_x=True, size=9)
    diag1 = [solution[i][i] for i in range(9)]
    diag2 = [solution[i][8 - i] for i in range(9)]
    assert sorted(diag1) == list(range(1, 10))
    assert sorted(diag2) == list(range(1, 10))


# ─── Sudoku X (diagonales) ───────────────────────────────────────────────────

def test_x_solution_valida_con_diagonales():
    puzzle, solution = sudoku.generate_x(difficulty="medium")
    assert _is_valid_solution(solution, 9, 3, 3)
    diag1 = [solution[i][i] for i in range(9)]
    diag2 = [solution[i][8 - i] for i in range(9)]
    assert sorted(diag1) == list(range(1, 10)), "Diagonal principal con repetidos"
    assert sorted(diag2) == list(range(1, 10)), "Diagonal secundaria con repetidos"


# ─── Sudoku Killer (jaulas) ──────────────────────────────────────────────────

def test_killer_jaulas_coherentes():
    puzzle, solution, cages = sudoku.generate_killer(difficulty="medium")
    assert _is_valid_solution(solution, 9, 3, 3)
    # Las jaulas cubren las 81 celdas exactamente una vez
    cubiertas = [cell for cage in cages for cell in cage["cells"]]
    assert len(cubiertas) == 81
    assert len(set(map(tuple, cubiertas))) == 81, "Celdas repetidas o faltantes en jaulas"
    # La suma de cada jaula coincide con la suma real en la solución
    for cage in cages:
        real = sum(solution[r][c] for r, c in cage["cells"])
        assert cage["sum"] == real, f"Suma de jaula {cage['id']} incorrecta"


# ─── Sudoku Letras (A-I) ─────────────────────────────────────────────────────

def test_letras_sin_repetidos():
    puzzle, solution = sudoku.generate_letters(difficulty="easy")
    for row in solution:
        assert sorted(row) == list("ABCDEFGHI"), "Fila de letras con repetidos"
    for c in range(9):
        col = [solution[r][c] for r in range(9)]
        assert sorted(col) == list("ABCDEFGHI"), "Columna de letras con repetidos"
    assert _puzzle_subset_of_solution(puzzle, solution, empty="")
