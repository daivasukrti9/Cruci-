import math

ISO_DIRECTIONS = {
    'no': (-1, -1),  # Norte-Oeste (página izquierda, proyecta sombra arriba/izq)
    'so': (-1, +1),  # Sur-Oeste   (página izquierda, proyecta sombra abajo/izq)
    'ne': (+1, -1),  # Norte-Este  (página derecha, proyecta sombra arriba/der)
    'se': (+1, +1),  # Sur-Este    (página derecha, proyecta sombra abajo/der)
}

def apply_isometric_board(svg_2d_content, w, h, depth=20, direction='se', 
                          top_color='#ffffff', left_color='#cccccc', right_color='#999999', 
                          stroke_color='#000000', sw=1.5, rx=0):
    """
    Toma contenido 2D SVG y lo proyecta isométricamente sobre un 'tablero' 3D.
    - svg_2d_content: todo el <g> o contenido 2D del puzzle.
    - w, h: ancho y alto original del tablero 2D.
    - depth: grosor del tablero en el eje Z (profundidad isométrica).
    - direction: 'se', 'sw', 'ne', 'nw' -> controla hacia dónde se extruyen las paredes.
    - colores: las 3 caras del bloque (iluminación).
    - rx: radio para esquinas redondeadas (próxima integración de diseño).
    """
    # Matriz afín isométrica estándar:
    # Scale(1, 0.5) * Rotate(45) o transformaciones similares (shear/rotate).
    # Matriz típica isométrica: matrix(0.866, 0.5, -0.866, 0.5, X, Y)
    # Pero aquí usamos una aproximación 2:1 que encaja perfecto en pixel art / cuadrículas.
    # El usuario / ChatGPT diseñará exactamente la matriz y dimensiones.
    
    # Esta es la ESTRUCTURA LÓGICA BASE. ChatGPT llenará los detalles de estilos.
    
    # 1. Dimensiones y vectores
    sx, sy = ISO_DIRECTIONS.get(direction, (1, 1))
    
    # 2. Construcción de los polígonos del Borde/Caja (Las caras laterales)
    # Dependiendo de Sx y Sy, las caras visibles cambian.
    # (ChatGPT configurará exactamente los paths y los estilos de esquinas redondeadas)
    
    # Ejemplo básico de estructura de caras a devolver:
    faces_svg = f"""
    <!-- Base 3D de la placa -->
    <g class="iso-base" stroke="{stroke_color}" stroke-width="{sw}">
        <!-- Cara A (Lateral 1) -->
        <path d="M..." fill="{left_color}" />
        <!-- Cara B (Lateral 2) -->
        <path d="M..." fill="{right_color}" />
        <!-- Top Face -->
        <path d="M..." fill="{top_color}" />
    </g>
    """
    
    # 3. Transformador del contenido original (el Grid del juego)
    # <g transform="matrix(0.866, 0.5, -0.866, 0.5, offsetX, offsetY)">
    transform_matrix = "matrix(0.866, 0.5, -0.866, 0.5, 0, 0)"
    
    projected_content = f"""
    <g class="iso-projection" transform="{transform_matrix}">
        {svg_2d_content}
    </g>
    """
    
    return f'<g class="iso-puzzle-group">{faces_svg}{projected_content}</g>'

