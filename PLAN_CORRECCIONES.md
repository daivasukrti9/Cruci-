# Plan de correcciones — Cruci (20 puntos)

Fuente: "Correcciones aplicacion Cruci.txt" + referencia `Diseños/Crucigramas Lista.pdf`.

**Decisiones acordadas (2026-07-11):**
- Estilos visuales: quitar solo **Geométrico**; conservar Plano + Isométrico.
- Nivel **Kids / muy fácil**: solo en laberintos.
- Laberintos (Fase F): al final, tras el resto.

Leyenda estado: ⬜ pendiente · 🟦 en progreso · ✅ hecho

---

## FASE A — Global (menú + formato de soluciones)
- ⬜ **1b** Quitar estilo "Geométrico/Origami" del menú.
- ⬜ **1c** Quitar "Grosor de línea (pt)"; grosor estándar único.
- ⬜ **1a+3** Soluciones sobre la MISMA plantilla del juego: sombrear solo las
  casillas dadas (pistas), respuestas faltantes en negrita. (Corrige el sombreado
  actual que marca todas las celdas.)

## FASE B — Familia Sudoku
- ⬜ **2** Asesino: líneas de jaula claras (punteadas + suma en esquina). Solución
  SIN sombreado, doble cuadrícula (borde 9×9 + límites de jaula).
- ⬜ **4** Jigsaw y Jigsaw X: definir bien cuadrícula 9 vs regiones; reflejar en solución.
- ⬜ **5** Jigsaw letras y Jigsaw 12×12: corregir plantilla + instrucciones + solución.

## FASE C — Lógica / aritmética
- ⬜ **6** KenKen: jaula de cálculo con línea gris interior (más fina que borde negro).
- ⬜ **7** Futoshiki: pistas numéricas en gris; trasladar a solución.
- ⬜ **8** Hitori: revisar lógica (bug), instrucciones del PDF, solución negro=eliminadas.
  Tamaños 10×10 y 20×14.
- ⬜ **12** Nurikabe: plantilla 15×10, corregir lógica (números adyacentes), más
  casillas en difícil, solución pinta muro de negro.

## FASE D — Redes / bucles
- ⬜ **9** Hashi: cuadrícula gris; solución traza puentes (líneas dobles). Tamaños 20×14, 18×25.
- ⬜ **10** Masyu: tamaños 20×14, 18×25; más perlas en difícil; solución traza el bucle.
- ⬜ **11** Akari: tamaños 12×12, 20×20; más casillas en difícil; solución sobre plantilla.

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
