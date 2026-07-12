"""
Cosecha (offline, una sola vez) mallas de Jigsaw SIN rectángulos, para usarlas
como plantillas en runtime. Guarda en puzzles_patterns/jigsaw_templates.json.

- size 12 (sudoku_12x12): regiones irregulares de 12 casillas, sin rectángulos.
- 9×9 X (sudoku_jigsaw_x): regiones irregulares de 9 casillas, sin rectángulos y
  que ADMITAN una solución con diagonales (para que el Jigsaw X sea válido).

Uso: python tools/harvest_jigsaw_templates.py [N_por_tipo]
"""
import os, sys, json, time, random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from puzzles.sudoku import (_solve, _carve_rainbow_regions, _count_boxy,
                            _validate_jigsaw, _fill_jigsaw)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'puzzles_patterns', 'jigsaw_templates.json')


def harvest(size, n, with_x=False, time_limit=600):
    """Devuelve lista de {regions, solution} sin rectángulos. La solución se guarda
    para no tener que re-resolver en runtime (rápido y siempre válido)."""
    box_w, box_h = (4, 3) if size == 12 else (3, 3)
    found = []
    seen = set()
    t0 = time.time()
    attempts = 0
    while len(found) < n and time.time() - t0 < time_limit:
        attempts += 1
        sol = [[0] * size for _ in range(size)]
        _solve(sol, size, box_w, box_h)
        cand = _carve_rainbow_regions(sol, size)
        if cand is None or _count_boxy(cand, size) != 0:
            continue
        if with_x:
            # X: la solución debe cumplir diagonales; sol (plana) no sirve.
            solution = _fill_jigsaw(size, cand, diags=True, max_iter=20000)
            if solution is None:
                continue
        else:
            solution = sol           # sol ya es válida para estas regiones (rainbow)
        key = tuple(map(tuple, cand))
        if key in seen:
            continue
        seen.add(key)
        found.append({"regions": cand, "solution": solution})
        print(f"  [{'X' if with_x else '12'}] {len(found)}/{n} "
              f"(intento {attempts}, {time.time()-t0:.0f}s)", flush=True)
    return found


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    data = {}
    print("Cosechando 9x9 Jigsaw X ...", flush=True)
    data['jigsaw_x_9'] = harvest(9, n, with_x=True, time_limit=300)
    print("Cosechando 12x12 ...", flush=True)
    data['jigsaw_12'] = harvest(12, n, with_x=False, time_limit=900)

    # Verificación final
    for key, entries in data.items():
        size = 12 if '12' in key else 9
        for e in entries:
            assert _count_boxy(e['regions'], size) == 0
            assert _validate_jigsaw(e['solution'], size, e['regions'])
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    print(f"\nGuardado en {OUT}")
    print({k: len(v) for k, v in data.items()})


if __name__ == '__main__':
    main()
