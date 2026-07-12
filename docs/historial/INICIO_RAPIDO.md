# KDP Puzzle Generator — Guía de Inicio Rápido

## 1️⃣ COMANDOS PARA INICIALIZAR LA APLICACIÓN

### Opción A: Click directo (recomendado)
Navega a: `C:\Users\Maximiliano Marinero\Downloads\Apps\Cruci\`

**Doble clic en:** `iniciar.bat`

Esto:
- Inicia el servidor Flask automáticamente
- Abre el navegador en http://localhost:5000
- Mantiene una ventana de consola con logs

---

### Opción B: Línea de comandos manual

#### PowerShell:
```powershell
cd "C:\Users\Maximiliano Marinero\Downloads\Apps\Cruci"
$py = "C:\Users\Maximiliano Marinero\AppData\Local\Programs\Python\Python313\python.exe"
& $py app.py
```

#### CMD:
```cmd
cd C:\Users\Maximiliano Marinero\Downloads\Apps\Cruci
"C:\Users\Maximiliano Marinero\AppData\Local\Programs\Python\Python313\python.exe" app.py
```

Luego abre en navegador: **http://localhost:5000**

---

### Opción C: Usar Python directamente (si está en PATH)
```powershell
cd C:\Users\Maximiliano Marinero\Downloads\Apps\Cruci
python313 app.py
```

---

### ⚠️ Python correcto
**Siempre usar Python 3.13:**
```
C:\Users\Maximiliano Marinero\AppData\Local\Programs\Python\Python313\python.exe
```

❌ No usar el `python` del PATH — no tiene las dependencias instaladas.

---

## Verificar dependencias (una sola vez)

```powershell
$py = "C:\Users\Maximiliano Marinero\AppData\Local\Programs\Python\Python313\python.exe"
& $py -m pip list | Select-String -Pattern "flask|reportlab|svgwrite|svglib|Pillow"
```

Debe mostrar:
```
flask           3.1.3
reportlab       4.5.1
svgwrite        1.4.3
svglib          2.0.1
Pillow          ...
```

---

## Parar el servidor

Presiona **Ctrl+C** en la ventana de consola del servidor, o ciérralade golpe.

---

## Troubleshooting

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError: No module named 'flask'` | Usa Python313 explícitamente |
| Página en blanco | Espera 3-5 segundos y recarga (F5) |
| "No es posible conectar" | Verifica que la ventana de servidor está abierta |
| Puerto 5000 en uso | Cambia en `app.py` línea ~150: `app.run(debug=True, port=5001)` |
