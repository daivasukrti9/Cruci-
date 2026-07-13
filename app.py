"""
KDP Puzzle Book Generator — Flask Backend
Run: python app.py
Open: http://localhost:5000
"""
import os, json, uuid, copy, traceback
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)
app.config['EXPORTS_DIR'] = os.path.join(os.path.dirname(__file__), 'exports')
app.config['PATTERNS_DIR'] = os.path.join(os.path.dirname(__file__), 'puzzles_patterns')
os.makedirs(app.config['EXPORTS_DIR'], exist_ok=True)

# ─── Catalog ─────────────────────────────────────────────────────────────────

def load_catalog():
    path = os.path.join(app.config['PATTERNS_DIR'], 'catalog.json')
    with open(path, encoding='utf-8') as f:
        return json.load(f)


@app.route('/')
def index():
    catalog = load_catalog()
    return render_template('index.html', catalog=catalog)


@app.route('/api/catalog')
def api_catalog():
    return jsonify(load_catalog())


# ─── Generate ────────────────────────────────────────────────────────────────

@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.json
    puzzle_id  = data.get('puzzle_id', 'sudoku_classic')
    style      = data.get('style', 'flat')
    difficulty = data.get('difficulty', 'medium')
    stroke_w   = float(data.get('stroke_width', 1.5))
    size_param = data.get('size', 9)
    words      = [w.strip() for w in data.get('words', '').split('\n') if w.strip()]
    clues      = [c.strip() for c in data.get('clues', '').split('\n') if c.strip()]

    try:
        result = _generate(puzzle_id, style, difficulty, stroke_w, size_param, words, clues)
        return jsonify({'ok': True, **result})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500


def _generate(puzzle_id, style, difficulty, stroke_w, size_param, words, clues):
    # Sin caché: cada generación produce un puzzle NUEVO (variedad infinita).
    # La generación ya es rápida y la exportación usa el SVG que el front ya tiene.
    return _generate_impl(puzzle_id, style, difficulty, stroke_w, size_param, words, clues)


def _generate_impl(puzzle_id, style, difficulty, stroke_w, size_param, words, clues):
    from puzzles import renderer as R

    # ── SUDOKU CLASSIC ──
    if puzzle_id == 'sudoku_classic':
        from puzzles.sudoku import generate_classic
        size = int(size_param) if isinstance(size_param, (int, str)) else 9
        puzzle, solution = generate_classic(size, difficulty)
        puzzle_svg   = R.render_sudoku(puzzle, solution, size, style, stroke_w, show_solution=False)
        solution_svg = R.render_sudoku(puzzle, solution, size, style, stroke_w, show_solution=True)
        return {'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg,
                'title': f'Sudoku Clásico {size}×{size}',
                'instructions': _instr('sudoku_classic', size)}

    # ── SUDOKU 16x16 ──
    elif puzzle_id == 'sudoku_16x16':
        from puzzles.sudoku import generate_classic
        puzzle, solution = generate_classic(16, difficulty)
        puzzle_svg   = R.render_sudoku(puzzle, solution, 16, style, stroke_w, show_solution=False)
        solution_svg = R.render_sudoku(puzzle, solution, 16, style, stroke_w, show_solution=True)
        return {'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg,
                'title': 'Sudoku 16×16',
                'instructions': _instr('sudoku_16x16')}

    # ── SUDOKU KILLER ──
    elif puzzle_id == 'sudoku_killer':
        from puzzles.sudoku import generate_killer
        puzzle, solution, cages = generate_killer(difficulty)
        puzzle_svg   = R.render_sudoku(puzzle, solution, 9, style, stroke_w, False, cages=cages)
        solution_svg = R.render_sudoku(puzzle, solution, 9, style, stroke_w, True, cages=cages)
        return {'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg,
                'title': 'Sudoku Asesino',
                'instructions': _instr('sudoku_killer')}

    # ── SUDOKU X ──
    elif puzzle_id == 'sudoku_x':
        from puzzles.sudoku import generate_x
        puzzle, solution = generate_x(difficulty)
        puzzle_svg   = R.render_sudoku(puzzle, solution, 9, style, stroke_w, False, diagonals=True)
        solution_svg = R.render_sudoku(puzzle, solution, 9, style, stroke_w, True, diagonals=True)
        return {'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg,
                'title': 'Sudoku X',
                'instructions': _instr('sudoku_x')}

    # ── SUDOKU LETTERS ──
    elif puzzle_id == 'sudoku_letters':
        from puzzles.sudoku import generate_letters
        puzzle, solution = generate_letters(difficulty)
        puzzle_svg   = R.render_sudoku(puzzle, solution, 9, style, stroke_w, False, is_letters=True)
        solution_svg = R.render_sudoku(puzzle, solution, 9, style, stroke_w, True, is_letters=True)
        return {'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg,
                'title': 'Sudoku de Letras',
                'instructions': _instr('sudoku_letters')}

    # ── SUDOKU JIGSAW ──
    elif puzzle_id in ('sudoku_jigsaw', 'sudoku_jigsaw_x', 'sudoku_jigsaw_letters', 'sudoku_12x12'):
        from puzzles.sudoku import generate_jigsaw
        with_x     = puzzle_id == 'sudoku_jigsaw_x'
        letters    = puzzle_id == 'sudoku_jigsaw_letters'
        sz         = 12 if puzzle_id == 'sudoku_12x12' else 9
        result_t   = generate_jigsaw(difficulty, with_x=with_x, letters=letters, size=sz)
        puzzle, solution, regions = result_t
        puzzle_svg   = R.render_sudoku(puzzle, solution, sz, style, stroke_w, False,
                                        regions=regions, diagonals=with_x)
        solution_svg = R.render_sudoku(puzzle, solution, sz, style, stroke_w, True,
                                        regions=regions, diagonals=with_x)
        names = {'sudoku_jigsaw':'Sudoku Rompecabezas','sudoku_jigsaw_x':'Sudoku Jigsaw X',
                 'sudoku_jigsaw_letters':'Sudoku Rompecabezas con Letras','sudoku_12x12':f'Sudoku Jigsaw {sz}×{sz}'}
        return {'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg,
                'title': names[puzzle_id],
                'instructions': _instr('sudoku_jigsaw', sz)}

    # ── KENKEN ──
    elif puzzle_id == 'kenken':
        from puzzles.kenken import generate_kenken
        size = int(size_param) if isinstance(size_param, (int, str)) else 4
        size = max(3, min(8, size))
        puzzle, solution, cages = generate_kenken(size, difficulty)
        puzzle_svg   = R.render_kenken(puzzle, solution, cages, size, style, stroke_w, False)
        solution_svg = R.render_kenken(puzzle, solution, cages, size, style, stroke_w, True)
        return {'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg,
                'title': f'KenKen {size}×{size}',
                'instructions': _instr('kenken', size)}

    # ── FUTOSHIKI ──
    elif puzzle_id == 'futoshiki':
        from puzzles.kenken import generate_futoshiki
        size = int(size_param) if isinstance(size_param, (int, str)) else 5
        size = max(4, min(7, size))
        puzzle, solution, inequalities = generate_futoshiki(size, difficulty)
        puzzle_svg   = R.render_futoshiki(puzzle, solution, inequalities, style, stroke_w, False)
        solution_svg = R.render_futoshiki(puzzle, solution, inequalities, style, stroke_w, True)
        return {'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg,
                'title': f'Futoshiki {size}×{size}',
                'instructions': _instr('futoshiki', size)}

    # ── HITORI ──
    elif puzzle_id == 'hitori':
        from puzzles.logic_puzzles import generate_hitori
        if isinstance(size_param, (list, tuple)):
            rows, cols = int(size_param[0]), int(size_param[1])
        else:
            rows = cols = int(size_param)
        puzzle, solution = generate_hitori(rows, cols)
        puzzle_svg   = R.render_hitori(puzzle, solution, style, stroke_w, False)
        solution_svg = R.render_hitori(puzzle, solution, style, stroke_w, True)
        return {'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg,
                'title': f'Hitori {rows}×{cols}',
                'instructions': _instr('hitori')}

    # ── HASHI ──
    elif puzzle_id == 'hashi':
        from puzzles.logic_puzzles import generate_hashi
        sz = size_param if isinstance(size_param, (list, tuple)) else [20, 14]
        rows, cols = int(sz[0]), int(sz[1])
        islands, bridges = generate_hashi(rows, cols, difficulty)
        puzzle_svg   = R.render_hashi(islands, bridges, rows, cols, style, stroke_w, False)
        solution_svg = R.render_hashi(islands, bridges, rows, cols, style, stroke_w, True)
        return {'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg,
                'title': f'Hashi (Puentes) {rows}×{cols}',
                'instructions': _instr('hashi')}

    # ── MASYU ──
    elif puzzle_id == 'masyu':
        from puzzles.logic_puzzles import generate_masyu
        sz = size_param if isinstance(size_param, (list, tuple)) else [20, 14]
        rows, cols = int(sz[0]), int(sz[1])
        puzzle, solution_path, pearls = generate_masyu(rows, cols, difficulty)
        puzzle_svg   = R.render_masyu(puzzle, solution_path, pearls, style, stroke_w, False)
        solution_svg = R.render_masyu(puzzle, solution_path, pearls, style, stroke_w, True)
        return {'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg,
                'title': f'Masyu (Perla) {rows}×{cols}',
                'instructions': _instr('masyu')}

    # ── AKARI ──
    elif puzzle_id == 'akari':
        from puzzles.logic_puzzles import generate_akari
        sz = size_param if isinstance(size_param, list) else [7, 7]
        rows, cols = int(sz[0]), int(sz[1])
        puzzle, solution = generate_akari(rows, cols)
        puzzle_svg   = R.render_akari(puzzle, solution, style, stroke_w, False)
        solution_svg = R.render_akari(puzzle, solution, style, stroke_w, True)
        return {'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg,
                'title': f'Akari (Iluminación) {rows}×{cols}',
                'instructions': _instr('akari')}

    # ── NURIKABE ──
    elif puzzle_id == 'nurikabe':
        from puzzles.logic_puzzles import generate_nurikabe
        sz = size_param if isinstance(size_param, (list, tuple)) else [15, 10]
        rows, cols = int(sz[0]), int(sz[1])
        puzzle, solution = generate_nurikabe(rows, cols, difficulty)
        puzzle_svg   = R.render_nurikabe(puzzle, solution, style, stroke_w, False)
        solution_svg = R.render_nurikabe(puzzle, solution, style, stroke_w, True)
        return {'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg,
                'title': f'Nurikabe {rows}×{cols}',
                'instructions': _instr('nurikabe')}

    # ── CROSSWORD ──
    elif puzzle_id == 'crossword':
        from puzzles.crossword import generate_crossword
        grid_size = int(size_param) if isinstance(size_param, (int, str)) else 15
        if not words:
            words = ['CRUCIGRAMA','PUZZLE','LIBRO','JUEGO','AMAZON','ROMPECABEZAS','LETRAS','FÁCIL']
        result = generate_crossword(words, clues if clues else None, grid_size)
        if result[0] is None:
            return {'puzzle_svg': '<svg/>', 'solution_svg': '<svg/>',
                    'title': 'Crucigrama', 'instructions': '', 'error': 'No se pudo generar'}
        puzzle_g, solution_g, across, down, cell_nums = result
        puzzle_svg   = R.render_crossword(puzzle_g, solution_g, across, down, cell_nums, style, stroke_w, False)
        solution_svg = R.render_crossword(puzzle_g, solution_g, across, down, cell_nums, style, stroke_w, True)
        clues_svg    = R.render_clue_sheet(across, down, 'CRUCIGRAMA', style)
        return {'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg, 'clues_svg': clues_svg,
                'title': 'Crucigrama Clásico',
                'across': [{'n':e['number'],'clue':e['clue'],'word':e['word']} for e in across],
                'down':   [{'n':e['number'],'clue':e['clue'],'word':e['word']} for e in down],
                'instructions': _instr('crossword')}

    # ── WORD SEARCH ──
    elif puzzle_id == 'word_search':
        from puzzles.crossword import generate_word_search
        grid_size = int(size_param) if isinstance(size_param, (int, str)) else 15
        if not words:
            words = ['PUZZLE','LIBRO','JUEGO','AMAZON','LETRAS','MENTE','LÓGICA','ARTE']
        g, sol, placed, positions = generate_word_search(words, grid_size, difficulty)
        puzzle_svg   = R.render_word_search(g, sol, placed, positions, style, stroke_w, False)
        solution_svg = R.render_word_search(g, sol, placed, positions, style, stroke_w, True)
        return {'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg,
                'title': f'Sopa de Letras {grid_size}×{grid_size}',
                'placed_words': placed,
                'instructions': _instr('word_search')}

    # ── MAZES ──
    elif puzzle_id == 'maze_rect':
        from puzzles.maze import generate_rectangular_maze
        sz = size_param if isinstance(size_param, list) else [15, 15]
        rows, cols = int(sz[0]), int(sz[1])
        grid, sol_path = generate_rectangular_maze(rows, cols)
        cell_px = max(8, min(20, 300 // max(rows, cols)))
        puzzle_svg   = R.render_maze_rect(grid, sol_path, style, stroke_w, False, cell_px)
        solution_svg = R.render_maze_rect(grid, sol_path, style, stroke_w, True, cell_px)
        return {'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg,
                'title': f'Laberinto Rectangular {rows}×{cols}',
                'instructions': _instr('maze_rect')}

    elif puzzle_id == 'maze_hex':
        from puzzles.maze import generate_hexagonal_maze
        sz = size_param if isinstance(size_param, list) else [8, 10]
        rows, cols = int(sz[0]), int(sz[1])
        cells, conns, walls, sol_path = generate_hexagonal_maze(rows, cols)
        puzzle_svg   = R.render_maze_hex(cells, conns, walls, sol_path, rows, cols, style, stroke_w, False)
        solution_svg = R.render_maze_hex(cells, conns, walls, sol_path, rows, cols, style, stroke_w, True)
        return {'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg,
                'title': f'Laberinto Hexagonal {rows}×{cols}',
                'instructions': _instr('maze_hex')}

    elif puzzle_id == 'maze_circular':
        from puzzles.maze import generate_circular_maze
        rings = int(size_param) if isinstance(size_param, (int, str)) else 5
        rings = max(3, min(8, rings))
        cells, sc, conns, walls, sol_path = generate_circular_maze(rings)
        puzzle_svg   = R.render_maze_circular(cells, sc, conns, walls, sol_path, style, stroke_w, False)
        solution_svg = R.render_maze_circular(cells, sc, conns, walls, sol_path, style, stroke_w, True)
        return {'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg,
                'title': f'Laberinto Circular ({rings} anillos)',
                'instructions': _instr('maze_circular')}

    elif puzzle_id == 'maze_triangle':
        from puzzles.maze import generate_triangular_maze
        size = int(size_param) if isinstance(size_param, (int, str)) else 10
        grid, sol_path = generate_triangular_maze(size)
        puzzle_svg   = R.render_maze_rect(grid, sol_path, style, stroke_w, False, 14)
        solution_svg = R.render_maze_rect(grid, sol_path, style, stroke_w, True, 14)
        return {'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg,
                'title': f'Laberinto Triangular',
                'instructions': _instr('maze_triangle')}

    else:
        return {'puzzle_svg': '', 'solution_svg': '',
                'title': puzzle_id, 'instructions': '', 'error': 'Tipo no implementado aún'}


# ─── Export ──────────────────────────────────────────────────────────────────

@app.route('/api/export', methods=['POST'])
def api_export():
    data = request.json
    fmt        = data.get('format', 'svg')      # svg | pdf | png
    which      = data.get('which', 'puzzle')     # puzzle | solution | both
    puzzle_svg = data.get('puzzle_svg', '')
    solution_svg = data.get('solution_svg', '')
    book_size  = data.get('book_size', '6x9')
    margin_type = data.get('margin_type', 'no_bleed')
    title      = data.get('title', 'Puzzle')
    stroke_w   = float(data.get('stroke_width', 1.5))

    uid = uuid.uuid4().hex[:8]
    exports_dir = app.config['EXPORTS_DIR']

    try:
        if fmt == 'svg':
            svg = puzzle_svg if which == 'puzzle' else solution_svg
            path = os.path.join(exports_dir, f'{uid}_{which}.svg')
            from puzzles.exporter import export_single_svg
            export_single_svg(svg, path)
            return send_file(path, as_attachment=True,
                             download_name=f'{title}_{which}.svg',
                             mimetype='image/svg+xml')

        elif fmt == 'png':
            svg = puzzle_svg if which == 'puzzle' else solution_svg
            path = os.path.join(exports_dir, f'{uid}_{which}.png')
            from puzzles.exporter import export_png
            result = export_png(svg, path, dpi=300)
            if result:
                return send_file(path, as_attachment=True,
                                 download_name=f'{title}_{which}.png',
                                 mimetype='image/png')
            return jsonify({'ok': False, 'error': 'PNG export requires cairosvg'}), 500

        elif fmt == 'pdf':
            puzzles_list = []
            if which in ('puzzle', 'both'):
                puzzles_list = [{'title': title, 'instructions': data.get('instructions',''),
                                 'puzzle_svg': puzzle_svg, 'solution_svg': solution_svg,
                                 'clues_svg': data.get('clues_svg', '')}]
            path = os.path.join(exports_dir, f'{uid}_book.pdf')
            from puzzles.exporter import export_puzzle_pdf
            export_puzzle_pdf(puzzles_list, path, book_size=book_size,
                              margin_type=margin_type, book_title=title)
            return send_file(path, as_attachment=True,
                             download_name=f'{title}.pdf',
                             mimetype='application/pdf')

    except Exception as e:
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500

    return jsonify({'ok': False, 'error': 'Formato no soportado'}), 400


# ─── Batch Generate ──────────────────────────────────────────────────────────

@app.route('/api/batch_pdf', methods=['POST'])
def api_batch_pdf():
    """Generate a complete book PDF with multiple puzzles."""
    data = request.json
    puzzles_config = data.get('puzzles', [])
    book_title  = data.get('book_title', 'Mi Libro de Puzzles')
    author      = data.get('author', '')
    book_size   = data.get('book_size', '6x9')
    margin_type = data.get('margin_type', 'no_bleed')

    all_puzzles = []
    for cfg in puzzles_config:
        try:
            result = _generate(
                cfg.get('puzzle_id', 'sudoku_classic'),
                cfg.get('style', 'flat'),
                cfg.get('difficulty', 'medium'),
                float(cfg.get('stroke_width', 1.5)),
                cfg.get('size', 9),
                [w.strip() for w in cfg.get('words', '').split('\n') if w.strip()],
                [c.strip() for c in cfg.get('clues', '').split('\n') if c.strip()],
            )
            result['instructions'] = cfg.get('instructions', result.get('instructions', ''))
            all_puzzles.append(result)
        except Exception as e:
            all_puzzles.append({'title': cfg.get('puzzle_id','?'), 'error': str(e),
                                'puzzle_svg': '', 'solution_svg': ''})

    uid = uuid.uuid4().hex[:8]
    path = os.path.join(app.config['EXPORTS_DIR'], f'{uid}_book.pdf')
    from puzzles.exporter import export_puzzle_pdf
    export_puzzle_pdf(all_puzzles, path, book_size=book_size,
                      margin_type=margin_type, book_title=book_title, author=author)
    return send_file(path, as_attachment=True,
                     download_name=f'{book_title}.pdf',
                     mimetype='application/pdf')


# ─── Save pattern ─────────────────────────────────────────────────────────────

@app.route('/api/patterns/save', methods=['POST'])
def api_save_pattern():
    """Save a custom visual sub-pattern."""
    data = request.json
    pid = data.get('id') or f"custom_{uuid.uuid4().hex[:6]}"
    path = os.path.join(app.config['PATTERNS_DIR'], f'{pid}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'ok': True, 'id': pid, 'path': path})


@app.route('/api/patterns')
def api_patterns():
    patterns_dir = app.config['PATTERNS_DIR']
    patterns = []
    for fn in os.listdir(patterns_dir):
        if fn.endswith('.json') and fn != 'catalog.json':
            with open(os.path.join(patterns_dir, fn), encoding='utf-8') as f:
                try:
                    patterns.append(json.load(f))
                except Exception:
                    pass
    return jsonify(patterns)


# ─── Instructions text ────────────────────────────────────────────────────────

def _instr(pid, size=9):
    texts = {
        'sudoku_classic': f'Completa la cuadrícula {size}×{size} colocando los números del 1 al {size} de modo que no se repitan en ninguna fila, columna ni caja.',
        'sudoku_16x16': 'Completa la cuadrícula 16×16 usando los números del 1 al 16 sin repetir en filas, columnas ni cajas 4×4.',
        'sudoku_killer': 'Las líneas de puntos forman "jaulas". Los números dentro de cada jaula deben sumar exactamente el valor indicado. Sigue las reglas del Sudoku clásico.',
        'sudoku_x': 'Sigue las reglas del Sudoku clásico. Adicionalmente, las dos diagonales principales también deben contener los dígitos del 1 al 9 sin repetición.',
        'sudoku_letters': 'Completa la cuadrícula 9×9 usando las letras de la A a la I. Ninguna letra puede repetirse en filas, columnas ni cajas 3×3.',
        'sudoku_jigsaw': f'Las regiones irregulares reemplazan las cajas clásicas. Cada región debe contener los números del 1 al {size} sin repetición, igual que filas y columnas.',
        'kenken': f'Rellena la cuadrícula {size}×{size} con números del 1 al {size}. Los bloques con operaciones deben dar el resultado indicado usando +, -, ×, ÷.',
        'futoshiki': f'Rellena la cuadrícula usando números del 1 al {size}. Respeta los signos > y < entre celdas adyacentes. No repitas en filas ni columnas.',
        'hitori': 'Tacha (pinta de negro) celdas para eliminar duplicados en cada fila y columna. Las celdas negras no pueden estar adyacentes y las blancas deben estar conectadas.',
        'hashi': 'Conecta todas las islas (círculos) con puentes (líneas rectas). El número en cada isla indica cuántos puentes deben conectarla. Máximo 2 puentes entre dos islas.',
        'masyu': 'Dibuja un bucle cerrado que pase por todas las perlas. Perla negra = giro obligatorio. Perla blanca = recto en ella, giro antes o después.',
        'akari': 'Coloca bombillas en celdas blancas para iluminar toda la cuadrícula. Las bombillas no pueden iluminarse entre sí. Los números en celdas negras indican cuántas bombillas deben tocarlas.',
        'nurikabe': 'Pinta celdas de negro formando un único "río" continuo. Las islas blancas tienen el tamaño indicado por su número. El río no puede tener bloques de 2×2.',
        'crossword': 'Completa el crucigrama usando las pistas horizontal y vertical. Cada cuadro blanco contiene una letra.',
        'word_search': 'Encuentra todas las palabras ocultas en la sopa de letras. Las palabras pueden ir en cualquier dirección: horizontal, vertical o diagonal.',
        'maze_rect': 'Encuentra el camino desde la entrada hasta la salida del laberinto sin atravesar las paredes.',
        'maze_hex': 'Navega por el laberinto hexagonal. Cada celda puede tener hasta 6 salidas posibles.',
        'maze_circular': 'Encuentra el camino desde el centro hasta el anillo exterior del laberinto circular.',
        'maze_triangle': 'Resuelve el laberinto de celdas triangulares encontrando el camino de entrada a salida.',
        'futoshiki': f'Rellena la cuadrícula {size}×{size} sin repetir. Respeta los signos de mayor/menor entre celdas adyacentes.',
    }
    return texts.get(pid, 'Resuelve el puzzle siguiendo las reglas indicadas.')


if __name__ == '__main__':
    print("=" * 55)
    print("  KDP Puzzle Book Generator")
    print("  http://localhost:5000")
    print("=" * 55)
    app.run(debug=True, port=5000)
