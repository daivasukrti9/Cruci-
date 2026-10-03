# Plan de correcciones — Cruci (20 puntos)

Fuente: "Correcciones aplicacion Cruci.txt" + referencia `Diseños/Crucigramas Lista.pdf`.

---

## ▶️ PUNTO DE CONTINUACIÓN (leer primero al abrir sesión nueva)

**Última actualización:** 2026-07-20 · Último commit previo: `3ee0398`.

**Nueva fase acordada (2026-07-20) — Formato de libro / colección / producción:**
Respuestas del usuario a la propuesta de etapas para esta fase (no confundir con las
Fases A-F de puzzles, ya cerradas):

1. **Etapa 1 (generación de puzzles)** — funciona perfecto, sin acción.
2. **Etapa 2 (estilos isométricos + paleta)** — agregar al menú 4 variantes de
   proyección isométrica: página izquierda = Oeste-Norte-arriba y Oeste-Sur-abajo;
   página derecha = Este-Norte-arriba y Este-Sur-abajo. Hoy `renderer.py` solo tiene
   un modo `'isometric'` fijo (línea ~19) — hay que parametrizar la dirección de
   proyección y exponer las 4 opciones en `static/app.js`. Paleta de colores por
   colección temática: se define recién al cerrar Etapa 3 (queda en espera).
3. **Etapa 3 (formato de libro KDP)** — guía completa en
   `C:\Users\Maximiliano Marinero\OneDrive\Escritorio\Algoritmo formato libro.txt`:
   tamaño 8.5"×11" base, márgenes espejo por página par/impar, capítulos de 4 páginas
   con densidad progresiva (calentamiento → medio → gran reto → test), tipografía
   monoespaciada en grillas, interior B&N con color solo en portada (portada-por-color
   = colección temática, conecta con la paleta de Etapa 2).
4. **Estructura de trabajo nueva (carpetas)** — separar "generación de puzzles" de
   "maquetación de libro": Carpeta A = juegos aprobados + sus soluciones (material
   curado por el usuario); Carpeta B = páginas finales generadas fusionando material
   de A con el algoritmo de diseño de Etapa 3. Pendiente al retomar: definir el
   formato del artefacto en Carpeta A (¿SVG + JSON de metadata? ¿PDF por puzzle?),
   de eso depende cómo el algoritmo de Etapa 3 los lea y componga. `app.py` hoy solo
   cachea en memoria — no existe todavía un paso de "aprobación" persistente.
5. **Diseño de producción y carpetas conectado a Google Drive** — decidido: **carpeta
   local sincronizada** (Google Drive Desktop), no integración por API. Las carpetas
   A y B viven físicamente dentro de la carpeta local que sincroniza Google Drive
   Desktop en la máquina del usuario; el algoritmo solo lee/escribe rutas locales
   normales, Drive se encarga de sync/backup/compartición por su cuenta — sin
   credenciales OAuth ni dependencias nuevas en el proyecto. Pendiente al retomar:
   definir la ruta exacta de esa carpeta sincronizada.

**Puente Circular arreglado (2026-07-20):** el modo `corner='round'` construía
arcos SVG ('A') a mano con radio r=S/2, casi igual a la mitad del grosor del
tubo — el borde INTERIOR de la curva casi tocaba el centro de curvatura (radio
interior ≈ 1.3px en producción) y el trazado degeneraba en fragmentos rotos
("comas"), no en curvas limpias (el "esferas" que reportó el usuario era en
realidad esto, no bolas). Comprobado con SVG aislado: el mismo trazado recto
de 'sharp' (M borde L centro L borde) con `stroke-linejoin="round"` NATIVO de
SVG da una curva perfecta, con el mismo ancho de tubo que 'sharp' (90%) — sin
necesidad de arcos manuales. Se eliminó el bloque de arcos completo de
`_corridor_paths` (simplificación neta: sharp y round comparten TODA la
geometría, solo cambia `stroke-linejoin`/`shape-rendering`). `crispEdges`
sigue limitado a 'sharp' (arruinaría las curvas nativas de 'round'); se
verificó que 'round' no muestra la costura gris en los cruces de puente sin
necesitarlo. Test actualizado (`test_round_weave_render_corner_round`): ya no
busca comando 'A', verifica `stroke-linejoin="round"` en su lugar.
Verificado: 95 tests + smoke test end-to-end (`maze_round_weave`, 3
tamaños × 4 dificultades) + inspección visual en varias semillas (incluida la
semilla con mucho trenzado que antes mostraba el problema).

**Rediseño de dificultad para TODOS los laberintos + arreglos visuales del Puente (2026-07-20):**

- ✅ **Tabla de dificultad para rect/hex/triangular/triangular-cuadrado/circular** — tenían el
  mismo problema que weave (ver abajo): solo controlaban trenzado, sin objetivo de ruta.
  Medido: rectangular medium>hard invertido (43%/47% casi iguales), hexagonal y circular
  con inversión en la cima, triangular casi plano (19-28% en los 4 niveles), varianza
  enorme (rangos 2-4x) en todos. Aplicado el mismo patrón que weave: cada
  `generate_*_maze` ahora envuelve un `_*_once` interno y genera hasta 16 candidatos,
  quedándose con el más cercano al objetivo de ruta de su dificultad (tablas
  `_RECT/_HEX/_TRI/_TRISQ/_CIRC_ROUTE_TARGET`). Verificado con 20 muestras/nivel:
  rangos SIN solapamiento en los 5 tipos. 5 tests nuevos (`test_*_dificultad_escala_con_ruta`).
- ✅ **Puente: máscara continua para grupos de puentes contiguos** — cuando 2+ puentes son
  vecinos (misma fila/columna, mismo eje), se agrupan (`_weave_bridge_groups`) y se tapan
  con una franja negra sólida en todo el tramo, antes de dibujar cada tubo blanco
  individual. Sin esto, el hueco de pared entre puentes vecinos dejaba asomar el borde
  del pasillo de abajo.
- ✅ **Puente: solución dividida en tramos suelo/elevado** — la ruta roja ahora se dibuja en
  el momento correcto de la pila de capas (`_weave_solution_layers`): los tramos que usan
  el paso de ABAJO se dibujan antes de los puentes (así un puente ajeno que cruce por
  encima los oculta); los tramos que usan el SALTO elevado se dibujan al final (se ven
  limpios sobre el tubo). Grosor subido de 2.6 a 4.6 (`WEAVE_SOLUTION_STROKE`).
- ✅ **Puente: costura gris (antialiasing seam) eliminada** — cuando dos trazos del mismo
  color se tocan en un borde matemático exacto (p.ej. fondo del grupo de puentes con el
  pasillo de abajo), el antialiasing dejaba una línea gris translúcida visible en la
  plantilla. Corregido con `shape-rendering="crispEdges"` (SOLO en `corner='sharp'`, ya
  que el laberinto de puentes es 100% ortogonal; `round` conserva antialiasing por sus
  arcos — pendiente de revisión aparte).
- ✅ **Laberinto de Puente Circular (`corner='round'`)** — arreglado, ver entrada de
  arriba ("Puente Circular arreglado").

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
- ✅ Arreglado el test flaky `test_weave_maze_conectividad_y_puentes[hard]`: el
  generador de puentes ahora **garantiza ≥1 puente** (si el azar no colocó ninguno,
  coloca el primer candidato elegible). Validado: 500 muestras/dificultad, mínimo ≥1.

**Rediseño del Laberinto de Puentes (2026-07-20):**

- ✅ **Render "casing/cinta"**: cada pasillo es un trazo NEGRO grueso (muros) con un
  trazo BLANCO opaco encima (camino). Tubo al 90% de la celda (10% de separación).
  Capas: todo el negro → todo el blanco → puente elevado (negro → blanco).
  `linecap="butt"` + `linejoin="miter"`; el negro de los callejones se alarga solo
  el grosor del muro para cerrarlos. Entrada/salida = aberturas a ras del margen.
  Bugs corregidos: la capa del puente iba de p1 a p2 (2 celdas) y tapaba los
  pasillos de p1/p2 rompiendo conexiones — ahora cubre SOLO la celda saltada;
  `square` dejaba pegotes; los radios sueltos desde el centro dejaban muescas
  (ahora son polilíneas conectadas).
- ✅ **Cruces integrados en el árbol**: el DFS puede SALTAR por encima de un pasillo
  recto hasta una celda sin visitar. Al aterrizar en celda no visitada la arista
  sigue siendo de árbol ⇒ **hard es laberinto PERFECTO (ruta única) CON muchos
  cruces**. Antes los puentes eran aristas extra y cada uno creaba un bucle.
- ✅ **Dificultad por complejidad de recorrido, no solo por tamaño**: cruces suben
  con la dificultad (kids 0.15 → hard 0.85), trenzado baja (kids 0.55 → hard 0), y
  se elige entre 14 candidatos el que más se acerca al objetivo de ruta
  (kids 15% / easy 25% / medium 35% / hard 48% del tablero). Medido con 20 muestras:
  rangos SIN solapamiento entre niveles.
- ⬜ **Pendiente: Laberinto de Puente Circular** — hereda el motor de casing pero aún
  tiene las "esferas"/bolas en extremos y uniones; falta aplicarle el mismo criterio
  con arcos de 90°.

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
2. Servidor: `iniciar.bat` → <http://localhost:1771> · Tests: `python -m pytest` (90 en verde).
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
