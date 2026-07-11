# KDP Puzzle Generator — Análisis de Rendimiento & Recomendaciones

**Fecha de test:** 2026-06-30 12:11 UTC  
**Servidor:** Flask dev + SQLite (en memoria)  
**Timeout API:** 30 segundos  

---

## 📊 RESULTADOS DEL TEST

### ✅ Fortalezas

| Métrica | Resultado |
|---------|-----------|
| **Disponibilidad API** | ✓ 100% online |
| **Puzzles funcionales** | ✓ 14/16 (87%) |
| **Concurrencia** | ✓ 5/5 paralelos exitosos |
| **Velocidad promedio** | ✓ 2.43s (rápido para lógica combinatoria) |
| **Tamaño SVG** | ✓ 3-60KB (optimizado) |
| **Estilos visuales** | ✓ Isométrico más eficiente (2.34s) |

### ⚠️ Problemas Detectados

| Problema | Severidad | Impacto |
|----------|-----------|---------|
| **Sudoku 16×16 timeout** | 🔴 CRÍTICO | No se puede generar (>30s) |
| **Sudoku Jigsaw timeout** | 🔴 CRÍTICO | No se puede generar (>30s) |
| **PDF export error 500** | 🟠 IMPORTANTE | Exportación PDF fallida |
| **Estilo flat más lento** | 🟡 MENOR | +0.45s vs isométrico |

---

## 🔧 ORDEN RECOMENDADO DE AJUSTES

### **ORDEN 1: CRÍTICO — Resolver Sudoku 16×16 y Jigsaw**

**Problema:** Algoritmo backtracking sin límite mata en ~40s

**Causa raíz:**
```python
# puzzles/sudoku.py línea ~50
def _solve(...):
    # Backtracking puro: intenta todas las combinaciones
    # Para grillas 16×16 o Jigsaw irregular, explosión combinatoria
```

**Solución (recomendada en este orden):**

#### 1a. Agregar tiempo máximo de búsqueda (RÁPIDO — 10 min)
```python
# En puzzles/sudoku.py, agregar timeout interno
def _solve(grid, size, ..., max_iterations=100000):
    iteration = [0]
    def backtrack(pos):
        iteration[0] += 1
        if iteration[0] > max_iterations:
            return False  # Timeout interno
        # ... rest of code
```
**Impacto:** Genera "puzzle bueno" vs "puzzle perfecto único"

#### 1b. Usar técnica CSP + constraint propagation (RECOMENDADO — 30 min)
```python
# Agregar naked singles + hidden singles antes de backtrack
def _propagate_constraints(grid):
    # Si solo 1 opción para celda → rellenarla
    # Si solo 1 lugar para número en fila → rellenarlo
    # Reduce espacio búsqueda 80%
```

#### 1c. Pre-generar puzzles (cache) (FUTURO)
Mantener pool de 10 Sudoku 16×16 resueltos, reutilizar

**Recomendación:** Implement 1a (5 min) + 1b (30 min) = ~35 min

**Código propuesto:**
```python
# puzzles/sudoku.py
MAX_ITERATIONS = 100000  # Limitar búsqueda

def _solve(grid, size, box_w, box_h, regions=None, diags=False, ...):
    iteration = [0]
    def backtrack(pos):
        iteration[0] += 1
        if iteration[0] > MAX_ITERATIONS:
            return False  # Timeout
        # ... existing code
```

---

### **ORDEN 2: IMPORTANTE — Debuggear PDF export (HTTP 500)**

**Problema:** 
```
[12:14:12] ⚠ ✗ PDF export error HTTP 500
```

**Causa probable:**
- `svglib` falla parseando SVG complejo
- ReportLab no puede renderizar ciertos elementos
- Problema de encoding en SVG

**Investigación (10 min):**
```bash
# Verificar logs del servidor Flask
# En la consola del servidor debe haber traceback detallado
```

**Solución (recomendada):**

#### 2a. Fallback a PNG (RÁPIDO — 5 min)
```python
# puzzles/exporter.py
def export_puzzle_pdf(...):
    try:
        svg_to_drawing(svg_string)  # Intenta SVG
    except Exception:
        png_bytes = svg_to_png(svg_string, dpi=300)  # Fallback PNG
```

#### 2b. Simplificar SVG antes de PDF (RECOMENDADO — 15 min)
- Remover comentarios XML
- Converter estilos inline en atributos
- Remover gradientes complejas

#### 2c. Usar cairosvg en lugar de svglib (FUTURO)
Instalable: `pip install cairosvg`

**Recomendación:** 2a (inmediato) + 2b investigación

---

### **ORDEN 3: OPTIMIZACIÓN — Mejorar velocidad global (1-2 horas)**

**Meta:** Reducir 2.43s → 1.5s promedio

#### 3a. Caché de puzzles (BAJO IMPACTO)
```python
# app.py
CACHE = {}  # {puzzle_id + params: (puzzle_svg, solution_svg)}
def generate(...):
    key = f"{puzzle_id}_{size}_{difficulty}"
    if key in CACHE:
        return CACHE[key]  # 10ms vs 2400ms
```
**Impacto:** +30% velocidad para repeats

#### 3b. Paralelizar generación (MEDIO)
```python
# puzzles/sudoku.py
from concurrent.futures import ThreadPoolExecutor
# Generar múltiples candidatos en paralelo, elegir el mejor
```
**Impacto:** +15% en puzzles grandes

#### 3c. Usar PyPy en lugar de CPython (FUTURO)
PyPy es 2-4× más rápido en código con loops

**Recomendación:** 3a solamente (easy win)

---

### **ORDEN 4: UX/CONVENIENCIA — Mejoras no-críticas (2-3 horas)**

#### 4a. Progress indicator durante generación
```javascript
// static/app.js
WebSocket para actualizar barra progress en tiempo real
```

#### 4b. Historial de puzzles generados
```python
# app.py + frontend
Guardar últimos 10 en sesión, con preview pequeño
```

#### 4c. Presets guardados
```json
// Guardar "Mi preset de libros" con configuraciones favoritas
```

**Recomendación:** 4a (mejor UX)

---

## 📋 TABLA RESUMEN: PRIORIDAD Y ESFUERZO

| Orden | Tarea | Severidad | Esfuerzo | Impacto | Recomendado |
|-------|-------|-----------|----------|---------|-------------|
| **1a** | Timeout sudoku 16x16 | 🔴 Crítico | 5 min | Alto | ✅ AHORA |
| **1b** | Constraint propagation | 🔴 Crítico | 30 min | Alto | ✅ AHORA |
| **2a** | PDF fallback PNG | 🟠 Importante | 5 min | Medio | ✅ AHORA |
| **2b** | Debug PDF error | 🟠 Importante | 15 min | Medio | ✅ AHORA |
| **3a** | Caché puzzles | 🟡 Optimización | 15 min | Bajo | ✅ DESPUÉS |
| **4a** | Progress indicator | 🟢 UX | 20 min | Bajo | ⏸ FUTURO |

---

## ⚡ PLAN DE EJECUCIÓN RECOMENDADO

### **Fase 1: Hoy — Corregir críticos (1 hora)**
```
1. [5 min] Agregar timeout en sudoku.py
2. [20 min] Investigar error 500 en logs servidor
3. [15 min] Implementar fallback PNG en exporter.py
4. [20 min] Test nuevamente: time test_performance.py
→ Meta: 16/16 puzzles generados, PDF funcional
```

### **Fase 2: Mañana — Optimizar (1.5 horas)**
```
1. [30 min] Implement constraint propagation en sudoku.py
2. [20 min] Agregar caché en app.py
3. [10 min] Test performance nuevamente
→ Meta: Reducir 16x16 de timeout → 10-15s, 9x9 → 1.5s
```

### **Fase 3: Esta semana — UX (2 horas)**
```
1. [20 min] Progress bar con WebSocket
2. [20 min] Historial de puzzles
3. [20 min] Presets guardados
```

---

## 🎯 MÉTRICAS DE ÉXITO

Después de Fase 1:
- ✅ 16/16 puzzles generados exitosamente
- ✅ PDF export funcional (no error 500)

Después de Fase 2:
- ✅ Sudoku 16×16 genera en 10-15s
- ✅ Promedio general < 2s

Después de Fase 3:
- ✅ UI muestra progreso en tiempo real
- ✅ Usuarios pueden guardar presets

---

## 📌 NOTAS IMPORTANTES

1. **El test es representativo:** 30s timeout simula red lenta → ajustar si necesitas local-only

2. **Sudoku 16×16 es inherentemente lento:** No es un bug, es la naturaleza del CSP. La solución es mejor algoritmo, no más poder de CPU.

3. **PDF export puede necesitar dependencias adicionales:** Si falla cairosvg, instalar:
   ```bash
   pip install cairosvg
   ```

4. **Concurrencia funciona bien:** El servidor Flask puede manejar 5+ solicitudes simultáneas sin problema.

---

## 🚀 SIGUIENTE PASO

¿Quieres que implemente la **Fase 1** ahora?

Necesitaré:
1. Acceso a línea de comandos para editar `puzzles/sudoku.py` y `puzzles/exporter.py`
2. Permiso para reiniciar servidor y re-testear

Estimado: **1 hora para Fase 1 + Phase 2**
