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
- ⚠️ **Jigsaw X (~40%) y 12×12 (~15%)**: PARCIAL. Generar piezas irregulares "gordas",
  válidas y sin rectángulos es muy difícil aquí (X además debe cumplir diagonales;
  12×12 tiene piezas de 12 celdas). Métodos probados sin éxito total: tallado greedy
  (hace cajas), deformación por intercambios, crecimiento simultáneo, camino
  hamiltoniano/backbite (da serpientes irresolubles). Pendiente: enfoque por
  **plantillas curadas** (biblioteca de layouts válidos + simetrías) o aceptar
  best-effort. Nunca se cuelga (presupuesto 2.5s).

## FASE B — Familia Sudoku ✅ (commit 5b94866)
- ✅ **2** Asesino: jaulas con contorno punteado inset + suma; visibles en puzzle y
  solución. Solución sin sombreado. Plantilla trasladada a la solución.
- ✅ **2b (X)** Sudoku X: se sombrean solo las diagonales (sin líneas X trazadas);
  solución resalta las respuestas.
- ✅ **4/5** Jigsaw, Jigsaw X, letras y 12×12: regiones irregulares de EXACTAMENTE
  `size` casillas (tallado arcoíris sobre solución válida); solución sobre la misma
  plantilla con regiones. Cuadrícula interna fina + regiones/borde gruesos.

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
