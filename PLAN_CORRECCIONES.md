# Plan de correcciones — Cruci (20 puntos)

Fuente: "Correcciones aplicacion Cruci.txt" + referencia `Diseños/Crucigramas Lista.pdf`.

**Decisiones acordadas (2026-07-11):**
- Estilos visuales: quitar solo **Geométrico**; conservar Plano + Isométrico.
- Nivel **Kids / muy fácil**: solo en laberintos.
- Laberintos (Fase F): al final, tras el resto.

Leyenda estado: ⬜ pendiente · 🟦 en progreso · ✅ hecho

---

## FASE A — Global (menú + formato de soluciones) ✅
- ✅ **1b** Quitar estilo "Geométrico/Origami" del menú. (commit b4717b7)
- ✅ **1c** Quitar "Grosor de línea (pt)"; grosor estándar único. (commit b4717b7)
- ✅ **1a+3** Soluciones sobre la MISMA plantilla: sombrear solo pistas, respuestas
  en negrita. Aplicado a familia Sudoku (clásico/16/X/letras). (commit 3c3353f)
  Nota: las soluciones de KenKen/Futoshiki/palabras/laberintos se ajustan en sus
  fases (6,7,13,14,15+) con sus casos especiales.

## Feedback post-Fase B ✅ (commit 0a74d4e, d764716)
- ✅ **Variedad infinita**: quitado el caché; cada "Generar" da un puzzle nuevo.
- ✅ **Jigsaw sin rectángulos (9×9 y letras)**: se rechaza TODO rectángulo (cuadrados
  y barras). jigsaw 9×9 = 100% sin rectángulo, letras = 95%. (commit d764716)
- ✅ **Jigsaw sin rectángulos en TODAS las variantes (100%)** (commit a2ccaf2).
  Solución: **plantillas curadas + simetrías** (como los libros comerciales).
  `tools/harvest_jigsaw_templates.py` cosechó offline 12 mallas SIN rectángulos por
  tipo (jigsaw_9, jigsaw_x_9, jigsaw_12) con su solución guardada →
  `puzzles_patterns/jigsaw_templates.json`. En runtime: plantilla + simetría diédrica
  (96 formas/tipo) → 9×9, X, letras y 12×12 = 100% irregular, válido, instantáneo.
  Descartados (documentado): tallado greedy, border swapping (material del usuario;
  sirve en 9×9 pero no escala a 12×12), backbite (serpientes irresolubles).

## FASE B — Familia Sudoku ✅ (commit 5b94866)
- ✅ **2** Asesino: jaulas con contorno punteado inset + suma; visibles en puzzle y
  solución. Solución sin sombreado. Plantilla trasladada a la solución.
- ✅ **2b (X)** Sudoku X: se sombrean solo las diagonales (sin líneas X trazadas);
  solución resalta las respuestas.
- ✅ **4/5** Jigsaw, Jigsaw X, letras y 12×12: regiones irregulares de EXACTAMENTE
  `size` casillas (tallado arcoíris sobre solución válida); solución sobre la misma
  plantilla con regiones. Cuadrícula interna fina + regiones/borde gruesos.

## FASE C — Lógica / aritmética ✅ (commits a108da5, 159ecd7, de1d058)
- ✅ **6** KenKen: jaulas con línea gris fina inset (más delgada que el borde negro);
  operaciones con símbolos propios (× ÷); solución sobre la misma plantilla.
- ✅ **7** Futoshiki: pistas dadas en gris, respuestas en negro/negrita; misma plantilla.
  (De paso: arreglado bug que rompía el SVG por los signos < > sin escapar.)
- ✅ **8** Hitori: generador válido (dup. fila+columna, negras no adyacentes, blancas
  conectadas); tamaños 10×10 y 20×14; solución = celdas negras. (commit a108da5)
- ✅ **12** Nurikabe: generador válido (malla que cubre cada 2×2 ⇒ sin piscinas;
  océano conectado; islas separadas); 15×10; solución = muro negro. (commit 159ecd7)
  Nota: el nº de islas sale alto (~18-24); ajustable si se quiere menos denso.

## FASE D — Redes / bucles ✅ (commits 0bd3ee1, 68576ea, 19e67eb)
- ✅ **9** Hashi: generador válido (grafo conexo, puentes sin cruces); cuadrícula gris,
  islas en cuadros redondeados, solución con puentes dobles. Tamaños 20×14, 18×25.
- ✅ **10** Masyu: generador válido (bucle orgánico vía backbite + perlas correctas);
  más perlas en difícil; solución traza el bucle. Tamaños 20×14, 18×25.
- ✅ **11** Akari: generador válido (iluminación total, sin conflictos); solución con
  bombillas + celdas iluminadas sombreadas. Tamaños 12×12, 20×20.
- Nota KDP: formato/tamaños finales al cierre (el usuario ajusta luego).

## FASE E — Palabras
- ⬜ **13** Crucigrama: solución rellena casillas con las palabras.
- ⬜ **14** Sopa de letras: solución sobre plantilla (casillas negras + letras blancas);
  dificultad fácil=H/V, medio=H/V ambos sentidos, difícil=+diagonales ambos sentidos.

## FASE F — Laberintos (al final)
- ⬜ **15** Rectangular: paredes/líneas (DFS backtracker, matriz de paredes); solución
  línea gruesa; nivel kids+fácil+medio+difícil.
- ⬜ **16** Hexagonal: rediseño (coords axiales q,r; 6 vecinos; Kruskal).
- ⬜ **17** Circular: rediseño polar (subdivisión de anillos; Prim).
- ⬜ **18** Triangular: rediseño (paridad fila+col; 3 vecinos; Aldous-Broder/Wilson).
- ⬜ **19** 🆕 Laberinto de Puentes (weave): DFS con saltos.
- ⬜ **20** 🆕 Laberinto de Puente Circular (round weave): polar + weave.
