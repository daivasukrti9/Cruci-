# Esquema de juegos pendientes — plan por bloques

Guía para trabajar los juegos restantes de forma ordenada. Por cada bloque:
**qué se pide**, **cómo lo abordaré** y **qué necesito de ti** (para adjuntar y
avanzar sin idas y vueltas).

> **Ya resuelto:** Fase A (menú + formato de soluciones) y Fase B (familia Sudoku
> completa: Asesino, X, Jigsaw/12×12/letras/X con piezas 100% irregulares).
> Las **instrucciones de cada juego las editas tú**, así que no te las pido aquí.

---

## Cómo alimentar mi proceso (requerimientos transversales)

Para cualquier juego, esto es lo que más acelera y mejora el resultado. Si me lo
adjuntas junto al bloque, lo clavo a la primera:

1. **Imagen de referencia del RESULTADO deseado** (puzzle + solución). Idealmente
   marcada con lo que quieres (flechas/notas). Ya tengo el PDF "Crucigramas Lista",
   pero un ejemplo tuyo del look exacto ayuda mucho.
2. **Screenshot del error/estado actual** cuando reportes un bug (Hitori, Nurikabe).
   Con ver el fallo concreto, voy directo.
3. **Definición de dificultad**: qué cambia entre fácil / medio / difícil (nº de
   pistas, tamaño, ramificaciones, densidad…).
4. **Tamaños confirmados** (la mayoría ya están en tus correcciones; los recuerdo
   en cada bloque para que confirmes o ajustes).
5. **Preferencias visuales concretas**: tono de gris, grosor de línea, símbolos
   (círculos, bombillas, puentes), color sí/no.

Leyenda dificultad de implementación: 🟢 ajuste visual · 🟡 lógica + visual · 🔴 rediseño/nuevo

---

## BLOQUE C — Lógica y aritmética
*(orden sugerido: primero, es el siguiente después de Sudoku)*

| # | Juego | Qué se pide | Nivel |
|---|-------|-------------|-------|
| 6 | **KenKen / Calcudoku** | Rediseñar la selección del cálculo: jaula con **línea gris interior** (más fina que el borde negro de las celdas). Trasladar plantilla a la solución. | 🟢 |
| 7 | **Futoshiki** | Pintar de **gris** las pistas numéricas de la plantilla. Trasladar a la solución. | 🟢 |
| 8 | **Hitori** | Revisar **lógica (posible bug)** + solución = casillas eliminadas en **negro**. Tamaños nuevos **10×10 y 20×14**. | 🟡 |
| 12 | **Nurikabe** | Plantilla **15×10**. Corregir **lógica** (si dos números quedan pegados no se pueden formar islas). Más casillas en difícil. Solución: pintar de negro el muro que rodea las islas. | 🟡 |

**Cómo lo abordaré:** KenKen y Futoshiki son cambios de render (unifico plantilla↔solución
como en Sudoku). Hitori y Nurikabe requieren revisar el generador y añadir tests de reglas.

**Qué necesito de ti para el Bloque C:**
- [ ] **Hitori**: screenshot del error que viste + confirmar tamaños 10×10 y 20×14.
- [ ] **Nurikabe**: screenshot de "números pegados sin islas" + confirmar 15×10.
- [ ] KenKen/Futoshiki: confirmar tono de gris (¿mismo `#d9d9d9` que Sudoku?).
- [ ] Regla de dificultad para Hitori y Nurikabe (qué sube en "difícil").

---

## BLOQUE D — Redes y bucles

| # | Juego | Qué se pide | Nivel |
|---|-------|-------------|-------|
| 9 | **Hashi (Puentes)** | Cuadrícula en **gris**. Solución: trazar los puentes con **líneas dobles** sobre la cuadrícula. Tamaños **20×14 y 18×25**. | 🟡 |
| 10 | **Masyu (Perla)** | Tamaños **20×14 y 18×25**. **Más perlas** (difícil se genera muy fácil). Solución: trazar el bucle sobre la plantilla. | 🟡 |
| 11 | **Akari (Iluminación)** | Tamaños **12×12 y 20×20**. **Más casillas** en difícil. Solución: trazar (bombillas + rayos) sobre la plantilla. | 🟡 |

**Cómo lo abordaré:** trazado de la solución sobre la misma plantilla (como pediste
en todo). Ajustar densidad/dificultad de los generadores y añadir tamaños grandes.

**Qué necesito de ti para el Bloque D:**
- [ ] Confirmar tamaños grandes (20×14, 18×25, 20×20) — **ojo KDP**: en 6×9" quedan
      celdas muy chicas; ¿estos van para tamaño de libro grande (8.5×11")?
- [ ] Masyu/Akari: qué tan "difícil" quieres el difícil (densidad de perlas/casillas).
- [ ] Referencia visual de cómo quieres el **puente doble** (Hashi) y el **bucle** (Masyu).

---

## BLOQUE E — Palabras

| # | Juego | Qué se pide | Nivel |
|---|-------|-------------|-------|
| 13 | **Crucigrama Clásico** | Solución: **rellenar las casillas** con las palabras correctas sobre la plantilla. | 🟢 |
| 14 | **Sopa de Letras** | Solución sobre plantilla: **casillas negras + letras blancas** en las respuestas. Redefinir dificultad: **fácil** = horizontal/vertical · **medio** = H/V en ambos sentidos · **difícil** = + diagonales en ambos sentidos. | 🟡 |

**Cómo lo abordaré:** cambiar la solución de "lista de respuestas" a "trazado sobre
la plantilla". En sopa de letras, reimplementar la colocación según los 3 niveles.

**Qué necesito de ti para el Bloque E:**
- [ ] Confirmar la definición de dificultad de la sopa (arriba) — es clara, solo valida.
- [ ] ¿La sopa usa tus palabras (input) o listas temáticas por defecto?
- [ ] Crucigrama: ¿mantener el formato actual de la grilla o algún ajuste visual?

---

## BLOQUE F — Laberintos *(el más grande: rediseños + 2 juegos nuevos)*

| # | Juego | Qué se pide | Nivel |
|---|-------|-------------|-------|
| 15 | **Laberinto Rectangular** | Cambiar de "casillas" a **paredes/líneas** (DFS recursive backtracker). Solución: **línea gruesa** del recorrido. Niveles: **kids + fácil + medio + difícil** (más ramificaciones). | 🔴 |
| 16 | **Laberinto Hexagonal** | Rediseño con **hexágonos** (coords axiales q,r; 6 vecinos; Kruskal). Solución trazada. Niveles kids→difícil. | 🔴 |
| 17 | **Laberinto Circular** | Rediseño **polar** (anillos concéntricos, subdivisión de sectores; Prim). Solución trazada. | 🔴 |
| 18 | **Laberinto Triangular** | Rediseño (paridad fila+col; 3 vecinos; Aldous-Broder/Wilson). Solución trazada. | 🔴 |
| 19 | **Laberinto de Puentes (Weave)** | **NUEVO**. Caminos que pasan por encima/debajo (falso 3D). | 🔴 |
| 20 | **Puente Circular (Round Weave)** | **NUEVO**. Polar + puentes. El más complejo. | 🔴 |

**Cómo lo abordaré:** reescribir `maze.py` con una malla basada en grafos (celdas +
paredes), un solo motor de generación (DFS/Kruskal/Prim según malla) y un solo
solucionador de camino. Cada geometría = una malla + su función de vecinos. Los
"puentes" añaden estado over/under. Es un bloque grande; sugiero hacerlo por
sub-tandas: (F1) rectangular, (F2) hex/triangular, (F3) circular, (F4) weave/round.

**Qué necesito de ti para el Bloque F:**
- [ ] **Referencia visual** del estilo de laberinto que quieres (líneas finas tipo
      libro, grosor, con/sin entrada-salida marcadas). Las imágenes del PDF sirven,
      pero confírmame el look.
- [ ] Definición de los **4 niveles** (kids/fácil/medio/difícil): ¿es solo tamaño,
      o también densidad de ramificaciones/callejones?
- [ ] Tamaños por geometría (rect, hex, circular, triangular) y para los nuevos weave.
- [ ] ¿Los 6 tipos van al mismo tiempo o priorizamos algunos? (sugiero empezar por
      rectangular, que valida el motor nuevo, y de ahí derivar los demás).

---

## Orden recomendado y ritmo

1. **Bloque C** (rápido, alto impacto visual) →
2. **Bloque D** →
3. **Bloque E** →
4. **Bloque F** (por sub-tandas, es un proyecto en sí).

**Formato ideal para trabajar cada bloque:** me adjuntas el bloque con su checklist
de arriba resuelto (imágenes + confirmaciones), yo trabajo juego por juego con su
test de reglas, te muestro imágenes puzzle+solución, confirmas, y commiteo.

---

## Estado de la red de seguridad (para tu tranquilidad)
- **Git**: todo en `master`, con historial por fases. Rollback siempre disponible.
- **Tests**: `python -m pytest` (19 en verde). Cada juego que toquemos suma su test.
- **Servidor**: `iniciar.bat` → http://localhost:5000
