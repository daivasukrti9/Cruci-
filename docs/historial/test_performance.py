#!/usr/bin/env python3
"""
KDP Puzzle Generator — Performance & Quality Test Suite
Ejecuta: python313 test_performance.py
"""

import json
import time
import sys
import os
import requests
from datetime import datetime
from statistics import mean, stdev

# Fix encoding en Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

API_BASE = "http://localhost:5000/api"
TIMEOUT = 30  # segundos

# Puzzles de prueba (tipo, params, descripción)
TEST_CASES = [
    # Sudoku
    ('sudoku_classic', {'difficulty': 'medium', 'size': 9}, '9×9 clásico'),
    ('sudoku_16x16', {'difficulty': 'medium', 'size': 16}, '16×16 clásico'),
    ('sudoku_killer', {'difficulty': 'medium', 'size': 9}, 'Asesino 9×9'),
    ('sudoku_x', {'difficulty': 'medium', 'size': 9}, 'X diagonal'),
    ('sudoku_jigsaw', {'difficulty': 'medium', 'size': 9}, 'Jigsaw 9×9'),

    # Aritmética
    ('kenken', {'difficulty': 'medium', 'size': 4}, 'KenKen 4×4'),
    ('kenken', {'difficulty': 'medium', 'size': 6}, 'KenKen 6×6'),
    ('futoshiki', {'difficulty': 'medium', 'size': 5}, 'Futoshiki 5×5'),

    # Lógica
    ('hashi', {'difficulty': 'medium', 'size': [7,7]}, 'Hashi 7×7'),
    ('akari', {'difficulty': 'medium', 'size': [7,7]}, 'Akari 7×7'),
    ('nurikabe', {'difficulty': 'medium', 'size': [6,6]}, 'Nurikabe 6×6'),

    # Crucigramas
    ('crossword', {'difficulty': 'medium', 'size': 13, 'words': 'PUZZLE\nLIBRO\nJUEGO\nAMAZON\nROMPECABEZAS'}, 'Crucigrama 13×13'),
    ('word_search', {'difficulty': 'medium', 'size': 15, 'words': 'PUZZLE\nLIBRO\nAMAZON\nKDP\nJUEGO'}, 'Sopa 15×15'),

    # Laberintos
    ('maze_rect', {'difficulty': 'medium', 'size': [10,10]}, 'Laberinto 10×10'),
    ('maze_hex', {'difficulty': 'medium', 'size': [6,8]}, 'Hexagonal 6×8'),
    ('maze_circular', {'difficulty': 'medium', 'size': 5}, 'Circular 5 anillos'),
]

STYLES = ['flat', 'isometric', 'geometric']

# ─────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log(msg, level='INFO'):
    ts = datetime.now().strftime('%H:%M:%S')
    if level == 'INFO':
        print(f"{Colors.OKCYAN}[{ts}]{Colors.ENDC} {msg}")
    elif level == 'OK':
        print(f"{Colors.OKGREEN}[{ts}] ✓{Colors.ENDC} {msg}")
    elif level == 'WARN':
        print(f"{Colors.WARNING}[{ts}] ⚠{Colors.ENDC} {msg}")
    elif level == 'ERROR':
        print(f"{Colors.FAIL}[{ts}] ✗{Colors.ENDC} {msg}")
    elif level == 'HEADER':
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{msg}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}\n")

def format_time(ms):
    if ms < 1000:
        return f"{ms:.0f}ms"
    return f"{ms/1000:.2f}s"

def format_size(bytes_val):
    for unit in ['B', 'KB', 'MB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f}GB"

def validate_svg(svg_string):
    """Valida que el SVG es XML válido."""
    if not svg_string or len(svg_string) < 50:
        return False, "SVG vacío o muy corto"
    if not svg_string.strip().startswith('<svg'):
        return False, "No comienza con <svg>"
    if '</svg>' not in svg_string:
        return False, "No cierra </svg>"
    try:
        import xml.etree.ElementTree as ET
        ET.fromstring(svg_string)
        return True, "XML válido"
    except Exception as e:
        return False, str(e)

# ─────────────────────────────────────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_api_availability():
    """Verifica que la API responde."""
    log("PRUEBA 1: Disponibilidad de API", 'HEADER')
    try:
        r = requests.get(f"{API_BASE}/catalog", timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            log(f"API disponible ✓ — {len(data['categories'])} categorías", 'OK')
            return True
        else:
            log(f"API retornó {r.status_code}", 'ERROR')
            return False
    except Exception as e:
        log(f"Servidor no responde: {e}", 'ERROR')
        return False

def test_generation_performance():
    """Prueba velocidad de generación de cada tipo."""
    log("PRUEBA 2: Performance de Generación", 'HEADER')

    results = {}
    total_time = 0
    success_count = 0

    for puzzle_id, params, desc in TEST_CASES:
        payload = {
            'puzzle_id': puzzle_id,
            'style': 'flat',
            'difficulty': params.get('difficulty', 'medium'),
            'stroke_width': 1.5,
            'size': params.get('size', 9),
            'words': params.get('words', ''),
            'clues': '',
        }

        try:
            start = time.time()
            r = requests.post(f"{API_BASE}/generate", json=payload, timeout=TIMEOUT)
            elapsed_ms = (time.time() - start) * 1000

            if r.status_code == 200:
                data = r.json()
                if data.get('ok'):
                    svg_size = len(data.get('puzzle_svg', ''))
                    sol_size = len(data.get('solution_svg', ''))

                    is_valid, msg = validate_svg(data.get('puzzle_svg', ''))

                    results[desc] = {
                        'time_ms': elapsed_ms,
                        'svg_size': svg_size,
                        'solution_size': sol_size,
                        'valid': is_valid,
                    }

                    status = "✓" if is_valid else "⚠"
                    log(f"{status} {desc:30s} {format_time(elapsed_ms):10s} "
                        f"({format_size(svg_size)} puzzle, {format_size(sol_size)} solución)", 'OK')

                    total_time += elapsed_ms
                    success_count += 1
                else:
                    log(f"✗ {desc:30s} Error en respuesta: {data.get('error', 'unknown')}", 'WARN')
            else:
                log(f"✗ {desc:30s} HTTP {r.status_code}", 'WARN')

        except requests.Timeout:
            log(f"✗ {desc:30s} Timeout (>{TIMEOUT}s)", 'WARN')
        except Exception as e:
            log(f"✗ {desc:30s} {str(e)[:40]}", 'WARN')

    # Estadísticas
    if results:
        times = [v['time_ms'] for v in results.values()]
        avg_time = mean(times)
        if len(times) > 1:
            std_dev = stdev(times)
            log(f"\n📊 Estadísticas: Promedio {format_time(avg_time)}, "
                f"Desv.Est. {format_time(std_dev)}, Total {format_time(total_time)}", 'INFO')
        log(f"✓ {success_count}/{len(TEST_CASES)} puzzles generados exitosamente\n", 'OK')

    return success_count, len(TEST_CASES), results

def test_multiple_styles():
    """Prueba generación con 3 estilos visuales."""
    log("PRUEBA 3: Rendimiento por Estilo Visual", 'HEADER')

    payload_base = {
        'puzzle_id': 'sudoku_classic',
        'difficulty': 'medium',
        'stroke_width': 1.5,
        'size': 9,
        'words': '',
        'clues': '',
    }

    style_times = {}
    for style in STYLES:
        payload = {**payload_base, 'style': style}
        times = []

        for i in range(3):  # 3 repeticiones
            try:
                start = time.time()
                r = requests.post(f"{API_BASE}/generate", json=payload, timeout=TIMEOUT)
                elapsed_ms = (time.time() - start) * 1000
                if r.status_code == 200 and r.json().get('ok'):
                    times.append(elapsed_ms)
            except Exception:
                pass

        if times:
            avg = mean(times)
            style_times[style] = avg
            log(f"  {style:25s}: {format_time(avg)} (x3 pruebas)", 'OK')

    print()
    return style_times

def test_concurrent_generation():
    """Prueba 5 generaciones simultáneas (sin bloqueos)."""
    log("PRUEBA 4: Manejo de Concurrencia (simulado)", 'HEADER')

    import threading

    results = {'success': 0, 'failed': 0, 'times': []}
    lock = threading.Lock()

    def worker(puzzle_id):
        payload = {
            'puzzle_id': puzzle_id,
            'style': 'flat',
            'difficulty': 'medium',
            'stroke_width': 1.5,
            'size': 9,
            'words': '',
            'clues': '',
        }
        try:
            start = time.time()
            r = requests.post(f"{API_BASE}/generate", json=payload, timeout=TIMEOUT)
            elapsed_ms = (time.time() - start) * 1000
            with lock:
                if r.status_code == 200 and r.json().get('ok'):
                    results['success'] += 1
                    results['times'].append(elapsed_ms)
                else:
                    results['failed'] += 1
        except Exception:
            with lock:
                results['failed'] += 1

    threads = []
    puzzle_ids = ['sudoku_classic', 'kenken', 'crossword', 'maze_rect', 'hashi']

    log("  Lanzando 5 solicitudes simultáneas...", 'INFO')
    start_all = time.time()
    for pid in puzzle_ids:
        t = threading.Thread(target=worker, args=(pid,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    total_time_ms = (time.time() - start_all) * 1000

    log(f"  ✓ {results['success']}/5 éxito, {results['failed']}/5 fallo", 'OK')
    if results['times']:
        log(f"  Tiempo promedio por request: {format_time(mean(results['times']))}", 'INFO')
    log(f"  Tiempo total (paralelo): {format_time(total_time_ms)}\n", 'INFO')

    return results['success'], results['failed']

def test_export_pdf():
    """Prueba exportación a PDF."""
    log("PRUEBA 5: Exportación PDF (Libro KDP)", 'HEADER')

    # Generar un puzzle primero
    payload = {
        'puzzle_id': 'sudoku_classic',
        'style': 'flat',
        'difficulty': 'medium',
        'stroke_width': 1.5,
        'size': 9,
        'words': '',
        'clues': '',
    }

    try:
        log("  Generando puzzle...", 'INFO')
        r = requests.post(f"{API_BASE}/generate", json=payload, timeout=TIMEOUT)
        if r.status_code != 200 or not r.json().get('ok'):
            log("  No se pudo generar puzzle base", 'WARN')
            return False

        gen_data = r.json()

        export_payload = {
            'format': 'pdf',
            'which': 'both',
            'puzzle_svg': gen_data.get('puzzle_svg', ''),
            'solution_svg': gen_data.get('solution_svg', ''),
            'title': 'Test Puzzle',
            'book_size': '6x9',
            'margin_type': 'no_bleed',
        }

        log("  Exportando a PDF...", 'INFO')
        start = time.time()
        r = requests.post(f"{API_BASE}/export", json=export_payload, timeout=TIMEOUT)
        elapsed_ms = (time.time() - start) * 1000

        if r.status_code == 200:
            pdf_size = len(r.content)
            log(f"  ✓ PDF generado en {format_time(elapsed_ms)} ({format_size(pdf_size)})", 'OK')
            return True
        else:
            log(f"  ✗ Error HTTP {r.status_code}", 'WARN')
            return False

    except Exception as e:
        log(f"  ✗ {str(e)}", 'WARN')
        return False

def test_catalog_loading():
    """Prueba carga y validación del catálogo."""
    log("PRUEBA 6: Integridad del Catálogo", 'HEADER')

    try:
        r = requests.get(f"{API_BASE}/catalog", timeout=TIMEOUT)
        if r.status_code != 200:
            log(f"  ✗ HTTP {r.status_code}", 'WARN')
            return False

        cat = r.json()
        total_puzzles = sum(len(c['puzzles']) for c in cat.get('categories', []))
        total_styles = len(cat.get('visual_styles', []))
        total_sizes = len(cat.get('book_sizes', []))

        log(f"  ✓ {len(cat['categories'])} categorías", 'OK')
        log(f"  ✓ {total_puzzles} tipos de puzzle", 'OK')
        log(f"  ✓ {total_styles} estilos visuales", 'OK')
        log(f"  ✓ {total_sizes} tamaños KDP\n", 'OK')

        return True
    except Exception as e:
        log(f"  ✗ {str(e)}", 'WARN')
        return False

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    log("KDP Puzzle Generator — Test Suite", 'HEADER')
    log(f"Servidor: {API_BASE}", 'INFO')
    log(f"Timestamp: {datetime.now().isoformat()}\n", 'INFO')

    # Pruebas
    if not test_api_availability():
        log("\n❌ El servidor no responde. Inicia la app primero:", 'FAIL')
        log("   python313 app.py\n", 'INFO')
        sys.exit(1)

    test_catalog_loading()

    success, total, perf_results = test_generation_performance()

    style_times = test_multiple_styles()

    concurrent_ok, concurrent_fail = test_concurrent_generation()

    pdf_ok = test_export_pdf()

    # Resumen final
    log("RESUMEN EJECUTIVO", 'HEADER')

    print(f"{Colors.OKGREEN}✓ API disponible{Colors.ENDC}")
    print(f"{Colors.OKGREEN}✓ {success}/{total} puzzles generados correctamente ({100*success//total}%){Colors.ENDC}")
    print(f"{Colors.OKGREEN}✓ {concurrent_ok}/5 solicitudes concurrentes exitosas{Colors.ENDC}")
    print(f"{'✓' if pdf_ok else '⚠'} Exportación PDF {'funcional' if pdf_ok else 'requiere ajuste'}")

    # Rendimiento
    if perf_results:
        times = [v['time_ms'] for v in perf_results.values()]
        print(f"\n⏱️  Performance:")
        print(f"   Mínimo: {format_time(min(times))}")
        print(f"   Máximo: {format_time(max(times))}")
        print(f"   Promedio: {format_time(mean(times))}")

    # Estilos
    if style_times:
        print(f"\n🎨 Estilos más rápidos:")
        for style, t in sorted(style_times.items(), key=lambda x: x[1]):
            print(f"   {style}: {format_time(t)}")

    print(f"\n✅ Test completado: {datetime.now().isoformat()}\n")

if __name__ == '__main__':
    main()
