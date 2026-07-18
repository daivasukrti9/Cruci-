# Plan de correcciones — Cruci (20 puntos)

Fuente: "Correcciones aplicacion Cruci.txt" + referencia `Diseños/Crucigramas Lista.pdf`.

---

## ▶️ PUNTO DE CONTINUACIÓN (leer primero al abrir sesión nueva)

**Última actualización:** 2026-07-18 · Último commit previo: `6a2d2d7`.

**Ronda de correcciones adicionales (reporte del usuario, 2026-07-18) — HECHAS:**
- ✅ **#1 KenKen** — tamaños 9×9 y 12×12 (catálogo + clamp `app.py`).
- ✅ **#2 Futoshiki** — tamaños 8/9/10/12; signos `>` `<` sin negrita; solución solo
  con los números faltantes en negrita (esto último ya estaba correcto).
- ✅ **#3 Hashi/Masyu/Akari** — más densidad de islas/perlas/muros (tablero más lleno,
  menos vacío) conservando el gradiente easy>medium>hard. Hard: Hashi ~11%, Masyu ~12%,
  Akari ~14% de celdas (antes 7-10%).
- ✅ **#4 Laberintos rutas más largas/menos predecibles** — hex, triangular,
  triangular-cuadrado y circular pasan de Kruskal/Prim/Aldous-Broder a **DFS
  (recursive backtracker)**: corredores largos y sinuosos, no diagonal directa.
  Validado por dificultad (ratio de celdas recorridas sube claramente en cada tipo).
- ✅ **#5 Triangular** — ancho de camino reducido (base 30→22), en línea con los demás.
- ✅ **#6 Solución triangular/triangular-cuadrado** — la línea roja sigue el corredor
  por los puntos medios de las aristas ("puertas"), sin picos (antes iba por centroides).
- ✅ **#7 Puentes y Puente Circular** — confirmados funcionando. NOTA: `maze_round_weave`
  es el MISMO weave ortogonal cuadrado que `maze_weave` con esquinas curvas
  (`corner='round'`), no el laberinto polar del plan #20 original.
- ⚠️ Pendiente: test flaky `test_weave_maze_conectividad_y_puentes[hard]` (el generador
  de puentes usa probabilidad y a veces da 0 puentes en hard) — a arreglar aparte.

**Estado global:**
- ✅ **Fase A, B, C** — hechas.
- ✅ **Fase D (Hashi, Masyu, Akari)** — generadores válidos, tamaños puestos,
  diseño estilo KenKen, y **dificultad diferenciada** (rangos amplios, Masyu corregido).
- ✅ **Sudoku Asesino** — adopta diseño KenKen.
- ✅ **Fase E — Palabras:**
  - #13 Crucigrama: la solución ahora rellena la MISMA plantilla con las letras en
    negrita (antes mostraba solo una tabla de texto con la lista de respuestas).
  - #14 Sopa de Letras: la solución muestra la MISMA plantilla con las celdas de las
    palabras encontradas en negro y la letra en blanco; el resto de celdas queda igual
    que en el puzzle. Dificultad: fácil = H/V (un sentido); media = H/V ambos sentidos;
    difícil = + diagonales ambos sentidos. (`puzzles/crossword.py`, `puzzles/renderer.py`)
  - Test de reglas: `tests/test_words_rules.py` (5 tests).
- ✅ **Fase F — Laberintos:**
  - #15 Rectangular: se mantiene DFS backtracker; ahora con **trenzado (braid)**
    por dificultad (kids=0.6, easy=0.3, medium=0.05, hard=0.0 callejones abiertos
    en bucle) y la solución traza una **línea gruesa** sobre la misma plantilla
    (antes mostraba una tabla de texto con pasos — código muerto, nunca se dibujaba).
  - #16 Hexagonal: **rediseño completo** a coordenadas **axiales (q,r)** + algoritmo
    de **Kruskal** (antes usaba offset row/col + DFS). Se corrigió además un bug real:
    el render dibujaba los 6 lados de CADA hexágono siempre, sin importar si había
    paso — el laberinto no se podía resolver visualmente. Ahora solo se dibujan las
    paredes reales.
  - #17 Circular: **rediseño** con **subdivisión real de anillos** (el nº de sectores
    se duplica hacia afuera, "Theta maze") + algoritmo de **Prim**. El código anterior
    calculaba la subdivisión pero la descartaba (`# Simplify: keep constant`) y
    dibujaba las 4 paredes de cada sector siempre (mismo bug de "no se ve el laberinto"
    que en el hexagonal). Ahora sí subdivide y solo dibuja paredes reales.
  - #18 Triangular: **rediseño total** — la versión anterior NO generaba triángulos
    reales (usaba una cuadrícula rectangular con paredes en diagonal). Ahora hay una
    cuadrícula triangular auténtica (orientación ▲/▽ por paridad fila+col, 3 vecinos)
    generada con **Aldous-Broder** (paseo aleatorio uniforme).
  - #19 🆕 Laberinto de Puentes (weave): DFS + "saltos" — celdas rectas (sin giro)
    pueden tender un puente perpendicular que salta la celda por encima/debajo.
    Puzzle nuevo: `maze_weave`, tamaños 12×12/15×15/20×20.
  - #20 🆕 Laberinto de Puente Circular: mismo laberinto polar de #17 (Prim +
    subdivisión) con saltos radiales sobre pasillos circunferenciales rectos
    (solo en fronteras de anillo sin subdivisión, para un salto 1 a 1). Puzzle
    nuevo: `maze_round_weave`, tamaños 4–8 anillos.
  - Nivel **Kids** añadido al selector de dificultad, mostrado SOLO para los 6
    laberintos (`MAZE_PUZZLES` en `static/app.js`).
  - Test de reglas: `tests/test_maze_rules.py` (38 tests: conectividad, reducción
    de callejones por dificultad, invariantes de puentes, SVG válido con/sin
    línea de solución para los 6 tipos).
  - Verificado end-to-end contra el servidor real (`/api/generate`) para los 6 tipos
    y las 4 dificultades. Suite completa: **90 tests en verde**.

**Lo que falta (en orden):**
1. **Formato/tamaño KDP final** — aplazado a lo último por decisión del usuario
   (KDP ya validado y soportado en `exporter.py`: 6x9/8.5x11/7x10, bleed, márgenes espejo, 300 DPI).
2. **(Opcional, recomendado) Solver + unicidad + rating de dificultad** para juegos lógicos
   (Hashi/Masyu/Akari). Hoy la dificultad se controla por *proxies* (nº de pistas); los niveles
   difíciles muy escasos pueden no tener solución única. La solución impresa siempre es válida.

**Cómo arrancar la sesión nueva:**
1. Leer este bloque + `CLAUDE.md` (reglas) + `git log --oneline -6`.
2. Servidor: `iniciar.bat` → http://localhost:5000 · Tests: `python -m pytest` (90 en verde).
3. El usuario lidera la revisión: esperar su reporte/material de referencia antes de empezar una fase.

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

## FASE E — Palabras ✅
- ✅ **13** Crucigrama: solución rellena casillas con las palabras (misma plantilla,
  letras en negrita).
- ✅ **14** Sopa de letras: solución sobre plantilla (casillas negras + letras blancas);
  dificultad fácil=H/V, medio=H/V ambos sentidos, difícil=+diagonales ambos sentidos.

## FASE F — Laberintos ✅
- ✅ **15** Rectangular: paredes/líneas (DFS backtracker, matriz de paredes); solución
  línea gruesa; nivel kids+fácil+medio+difícil (trenzado/braid).
- ✅ **16** Hexagonal: rediseño (coords axiales q,r; 6 vecinos; Kruskal).
- ✅ **17** Circular: rediseño polar (subdivisión real de anillos; Prim).
- ✅ **18** Triangular: rediseño (paridad fila+col; 3 vecinos; Aldous-Broder).
- ✅ **19** 🆕 Laberinto de Puentes (weave): DFS con saltos (`maze_weave`).
- ✅ **20** 🆕 Laberinto de Puente Circular (round weave): polar + weave (`maze_round_weave`).
