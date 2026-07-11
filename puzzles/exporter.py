"""
PDF exporter using ReportLab — KDP-ready B&W output.
Supports:
  - KDP Trim sizes: 6x9, 8.5x11, 7x10
  - Bleed / no-bleed margins
  - Embeds SVG puzzles as vector drawings via svglib (fallback: PNG via cairosvg or Pillow)
"""
import os
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, pt
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing


# KDP standard trim sizes (width, height) in inches
KDP_SIZES = {
    '6x9':    (6 * inch, 9 * inch),
    '8.5x11': (8.5 * inch, 11 * inch),
    '7x10':   (7 * inch, 10 * inch),
    '5x8':    (5 * inch, 8 * inch),
}

# Margins (inside_margin is larger to account for spine)
MARGINS = {
    'no_bleed': {'top': 0.75*inch, 'bottom': 0.75*inch, 'outside': 0.5*inch, 'inside': 0.875*inch},
    'bleed':    {'top': 0.875*inch, 'bottom': 0.875*inch, 'outside': 0.625*inch, 'inside': 1.0*inch},
}


def _svg_to_drawing(svg_string):
    """Convert SVG string to ReportLab Drawing using svglib."""
    try:
        from svglib.svglib import svg2rlg
        svg_bytes = io.BytesIO(svg_string.encode('utf-8'))
        drawing = svg2rlg(svg_bytes)
        return drawing
    except Exception:
        return None


def _svg_to_png_bytes(svg_string, scale=2):
    """Rasterize SVG to PNG at scale×72 DPI using Pillow+cairosvg or fallback."""
    try:
        import cairosvg
        return cairosvg.svg2png(bytestring=svg_string.encode(), scale=scale)
    except Exception:
        return None


def _embed_svg_on_canvas(c, svg_string, x, y, width, height):
    """Try to embed SVG as vector, fall back to PNG."""
    if not svg_string or len(svg_string) < 50:
        c.drawString(x, y - 20, "[Error: Empty SVG]")
        return

    drawing = _svg_to_drawing(svg_string)
    if drawing:
        try:
            sx = width / drawing.width if drawing.width else 1
            sy = height / drawing.height if drawing.height else 1
            scale = min(sx, sy)
            drawing.width = drawing.width * scale
            drawing.height = drawing.height * scale
            drawing.transform = (scale, 0, 0, scale, 0, 0)
            renderPDF.draw(drawing, c, x, y - drawing.height)
            return
        except Exception:
            pass

    # PNG fallback (más confiable que SVG vector)
    try:
        png = _svg_to_png_bytes(svg_string, scale=3)
        if png:
            img_io = io.BytesIO(png)
            img = Image(img_io, width=width, height=height)
            img.drawOn(c, x, y - height)
            return
    except Exception:
        pass

    # Fallback texto de error
    c.drawString(x, y - 20, "[Error embedding SVG - please use PNG export]")


def export_puzzle_pdf(puzzles_data, output_path, book_size='6x9', margin_type='no_bleed',
                      book_title='Puzzle Book', author=''):
    """
    Export a list of puzzle pages to a KDP-ready PDF.

    puzzles_data: list of dicts, each with:
      {
        'title': str,
        'instructions': str,
        'puzzle_svg': str,       # SVG string for puzzle
        'solution_svg': str,     # SVG string for solution
        'clues_svg': str | None, # SVG string for clue list (crosswords)
        'type': str,
      }

    output_path: full path to output PDF file
    """
    page_w, page_h = KDP_SIZES.get(book_size, KDP_SIZES['6x9'])
    m = MARGINS[margin_type]

    c = canvas.Canvas(output_path, pagesize=(page_w, page_h))
    c.setTitle(book_title)
    c.setAuthor(author)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('PuzzleTitle', fontName='Helvetica-Bold',
                                  fontSize=14, alignment=TA_CENTER, spaceAfter=6)
    instr_style = ParagraphStyle('Instr', fontName='Helvetica',
                                  fontSize=9, alignment=TA_LEFT, spaceAfter=4)

    content_w = page_w - m['inside'] - m['outside']
    content_h = page_h - m['top'] - m['bottom']

    def draw_header(page_num, title=''):
        c.setFont('Helvetica', 8)
        c.setFillColor(colors.black)
        c.drawCentredString(page_w/2, page_h - m['top']/2, book_title)
        c.drawRightString(page_w - m['outside'], m['bottom']/2, str(page_num))

    page_num = 1

    # Title page
    c.setFont('Helvetica-Bold', 28)
    c.drawCentredString(page_w/2, page_h*0.55, book_title)
    if author:
        c.setFont('Helvetica', 14)
        c.drawCentredString(page_w/2, page_h*0.45, author)
    c.showPage()
    page_num += 1

    puzzle_pages = []
    solution_pages = []

    for idx, pd in enumerate(puzzles_data):
        puzzle_pages.append((idx + 1, pd))

    # ── Puzzle pages ──
    for num, pd in puzzle_pages:
        draw_header(page_num, pd.get('title', ''))
        y = page_h - m['top']
        x = m['inside']

        # Title
        c.setFont('Helvetica-Bold', 13)
        c.drawString(x, y - 16, f"#{num}  {pd.get('title', '')}")
        y -= 28

        # Instructions (wrap)
        instr = pd.get('instructions', '')
        if instr:
            c.setFont('Helvetica', 8)
            text_obj = c.beginText(x, y)
            text_obj.setFont('Helvetica', 8)
            text_obj.setLeading(11)
            for line in instr[:200].split('\n'):
                text_obj.textLine(line)
            c.drawText(text_obj)
            y -= min(60, len(instr.split('\n')) * 12 + 10)

        # Clue list (for crosswords)
        if pd.get('clues_svg'):
            clue_h = content_h * 0.25
            _embed_svg_on_canvas(c, pd['clues_svg'], x, y, content_w, clue_h)
            y -= clue_h + 10

        # Puzzle SVG
        puzzle_svg = pd.get('puzzle_svg', '')
        if puzzle_svg:
            avail_h = y - m['bottom'] - 10
            avail_w = content_w
            _embed_svg_on_canvas(c, puzzle_svg, x, y, avail_w, avail_h)

        c.showPage()
        page_num += 1

    # ── Solutions section divider ──
    c.setFont('Helvetica-Bold', 20)
    c.drawCentredString(page_w/2, page_h/2, 'SOLUCIONES')
    c.showPage()
    page_num += 1

    # ── Solution pages (2 per page when possible) ──
    for num, pd in puzzle_pages:
        solution_svg = pd.get('solution_svg', '')
        if not solution_svg:
            continue
        draw_header(page_num)
        x = m['inside']
        y = page_h - m['top']
        c.setFont('Helvetica-Bold', 10)
        c.drawString(x, y - 12, f"Solución #{num} — {pd.get('title', '')}")
        y -= 24
        sol_h = y - m['bottom'] - 10
        _embed_svg_on_canvas(c, solution_svg, x, y, content_w, sol_h)
        c.showPage()
        page_num += 1

    c.save()
    return output_path


def export_single_svg(svg_string, output_path):
    """Save SVG string to file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_string)
    return output_path


def export_png(svg_string, output_path, dpi=300):
    """Export SVG to high-res PNG."""
    scale = dpi / 72
    png = _svg_to_png_bytes(svg_string, scale=scale)
    if png:
        with open(output_path, 'wb') as f:
            f.write(png)
        return output_path
    # Fallback using Pillow
    try:
        from PIL import Image as PILImage
        import xml.etree.ElementTree as ET
        # Basic fallback: can't rasterize without cairosvg
        return None
    except Exception:
        return None
