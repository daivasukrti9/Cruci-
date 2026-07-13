"""
Red de seguridad para la familia de lógica (Bloque C en adelante).
Validadores independientes de las reglas de cada juego.
"""
import pytest
from puzzles import logic_puzzles as L


# ─── HITORI ──────────────────────────────────────────────────────────────────

def _hitori_checks(puzzle, solution):
    rows = len(solution)
    cols = len(solution[0])
    black = [[solution[r][c] == -1 for c in range(cols)] for r in range(rows)]

    # 1) Ninguna dos negras ortogonalmente adyacentes
    for r in range(rows):
        for c in range(cols):
            if black[r][c]:
                for dr, dc in [(1, 0), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if nr < rows and nc < cols and black[nr][nc]:
                        return f"negras adyacentes en ({r},{c})-({nr},{nc})"

    # 2) Blancas conectadas (una sola región)
    whites = [(r, c) for r in range(rows) for c in range(cols) if not black[r][c]]
    seen = {whites[0]}
    stack = [whites[0]]
    while stack:
        r, c = stack.pop()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not black[nr][nc] and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))
    if len(seen) != len(whites):
        return "blancas desconectadas"

    # 3) Sin números repetidos entre blancas en filas ni columnas
    for r in range(rows):
        vals = [puzzle[r][c] for c in range(cols) if not black[r][c]]
        if len(vals) != len(set(vals)):
            return f"duplicado blanco en fila {r}"
    for c in range(cols):
        vals = [puzzle[r][c] for r in range(rows) if not black[r][c]]
        if len(vals) != len(set(vals)):
            return f"duplicado blanco en columna {c}"

    # 4) Cada negra es un duplicado real de una blanca de su fila o columna
    for r in range(rows):
        for c in range(cols):
            if black[r][c]:
                v = puzzle[r][c]
                in_row = any(puzzle[r][cc] == v and not black[r][cc] for cc in range(cols))
                in_col = any(puzzle[rr][c] == v and not black[rr][c] for rr in range(rows))
                if not (in_row or in_col):
                    return f"negra ({r},{c}) no duplica ninguna blanca"
    return None


@pytest.mark.parametrize("rows,cols", [(10, 10), (20, 14)])
def test_hitori_valido(rows, cols):
    puzzle, solution = L.generate_hitori(rows, cols)
    err = _hitori_checks(puzzle, solution)
    assert err is None, f"Hitori {rows}×{cols} inválido: {err}"


# ─── NURIKABE ────────────────────────────────────────────────────────────────

def _nurikabe_checks(solution):
    rows = len(solution)
    cols = len(solution[0])
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    ocean = [(r, c) for r in range(rows) for c in range(cols) if solution[r][c] == 0]

    # 1) Océano sin bloques 2×2
    for r in range(rows - 1):
        for c in range(cols - 1):
            if all(solution[r + a][c + b] == 0 for a in (0, 1) for b in (0, 1)):
                return "océano con bloque 2×2"

    # 2) Océano conectado (una sola región)
    if ocean:
        seen = {ocean[0]}
        st = [ocean[0]]
        while st:
            r, c = st.pop()
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and solution[nr][nc] == 0 and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    st.append((nr, nc))
        if len(seen) != len(ocean):
            return "océano desconectado"

    # 3) Cada isla (componente blanca) tiene EXACTAMENTE una pista = su tamaño
    seen = [[False] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if solution[r][c] != 0 and not seen[r][c]:
                comp = [(r, c)]
                seen[r][c] = True
                st = [(r, c)]
                while st:
                    rr, cc = st.pop()
                    for dr, dc in dirs:
                        nr, nc = rr + dr, cc + dc
                        if (0 <= nr < rows and 0 <= nc < cols
                                and solution[nr][nc] != 0 and not seen[nr][nc]):
                            seen[nr][nc] = True
                            comp.append((nr, nc))
                            st.append((nr, nc))
                clues = [solution[rr][cc] for rr, cc in comp if solution[rr][cc] > 0]
                if len(clues) != 1:
                    return f"isla con {len(clues)} pistas"
                if clues[0] != len(comp):
                    return f"pista {clues[0]} != tamaño {len(comp)}"
    return None


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_nurikabe_valido(difficulty):
    puzzle, solution = L.generate_nurikabe(15, 10, difficulty)
    err = _nurikabe_checks(solution)
    assert err is None, f"Nurikabe {difficulty} inválido: {err}"
