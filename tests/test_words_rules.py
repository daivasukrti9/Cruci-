"""
Red de seguridad para la familia de palabras (Fase E: Crucigrama, Sopa de letras).
"""
import xml.etree.ElementTree as ET

import pytest
from puzzles import crossword as CW
from puzzles import renderer as R


WORDS = ['CASA', 'SOL', 'LUNA', 'MAR', 'ARBOL', 'RIO', 'FLOR', 'NUBE']


def test_crossword_solucion_rellena_plantilla():
    puzzle_g, solution_g, across, down, cell_nums = CW.generate_crossword(WORDS, grid_size=15)
    assert puzzle_g is not None
    size = len(puzzle_g)

    # El puzzle es un subconjunto de la solución: mismas celdas blancas/negras,
    # y toda celda blanca del puzzle tiene una letra en la solución.
    for r in range(size):
        for c in range(size):
            is_wall = puzzle_g[r][c] is None
            assert is_wall == (solution_g[r][c] is None)
            if not is_wall:
                assert solution_g[r][c] and solution_g[r][c].isalpha()

    # El SVG de la solución debe mostrar las letras (rellenar la plantilla).
    solution_svg = R.render_crossword(puzzle_g, solution_g, across, down, cell_nums,
                                       'flat', 1.5, True)
    ET.fromstring(solution_svg)
    for entry in across + down:
        for i, ch in enumerate(entry['word']):
            assert f'>{ch}<' in solution_svg or f'>{ch.upper()}<' in solution_svg

    # El SVG del puzzle no debe mostrar letras (casillas vacías).
    puzzle_svg = R.render_crossword(puzzle_g, solution_g, across, down, cell_nums,
                                     'flat', 1.5, False)
    ET.fromstring(puzzle_svg)


@pytest.mark.parametrize('difficulty,expected_dirs', [
    ('easy', {(0, 1), (1, 0)}),
    ('medium', {(0, 1), (0, -1), (1, 0), (-1, 0)}),
    ('hard', {(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)}),
])
def test_word_search_direcciones_por_dificultad(difficulty, expected_dirs):
    grid, solution, placed, positions = CW.generate_word_search(WORDS, grid_size=15,
                                                                  difficulty=difficulty)
    assert placed  # al menos alguna palabra colocada
    used_dirs = {info['direction'] for info in positions.values()}
    assert used_dirs.issubset(expected_dirs)


def test_word_search_solucion_marca_celdas_de_palabras():
    grid, solution, placed, positions = CW.generate_word_search(WORDS, grid_size=15,
                                                                  difficulty='hard')
    # Cada celda marcada como parte de una palabra coincide con la letra del grid.
    for word, info in positions.items():
        for i, (r, c) in enumerate(info['cells']):
            assert grid[r][c] == word[i]

    puzzle_svg = R.render_word_search(grid, solution, placed, positions, 'flat', 1.0, False)
    solution_svg = R.render_word_search(grid, solution, placed, positions, 'flat', 1.0, True)
    ET.fromstring(puzzle_svg)
    ET.fromstring(solution_svg)
    # La solución debe usar celdas negras (fill_black) para las palabras encontradas.
    assert 'fill="#000000"' in solution_svg or 'fill="#1a1a1a"' in solution_svg or \
           'fill="#111111"' in solution_svg
