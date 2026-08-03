"""
make_ascii_svg.py
Convertit l'image préparée (niveaux de gris) en un portrait ASCII SVG
qui "s'imprime" ligne par ligne via SMIL (GitHub le rend, pas de JS requis).

Design :
- Monochrome (une seule couleur) -> évite l'effet "static" arc-en-ciel
- Rampe de densité claire -> foncé, l'espace en tête vide le fond
- Chaque ligne se révèle via un clip horizontal qui se décale de gauche à
  droite, avec un petit "curseur" bloc qui suit le front d'écriture,
  et les lignes sont décalées (stagger) du haut vers le bas.
- Joue une fois puis se fige (pas de boucle).

Usage: python make_ascii_svg.py
Sortie: avi-ascii.svg (ici: kawthar-ascii.svg)
"""
import numpy as np
from PIL import Image

INPUT_PATH = "prepped/source-prepped.png"
OUTPUT_PATH = "kawthar-ascii.svg"

# Densité claire (sparse) -> foncée (dense). L'espace en tête vide le fond blanc.
RAMP = " .`:-=+*cs#%@"

COLS = 100
ROWS = 53
FONT_SIZE = 8
CHAR_W = FONT_SIZE * 0.6
CHAR_H = FONT_SIZE * 1.0
FILL_COLOR = "#8ecbff"  # gris-bleu clair monochrome (thème terminal)

STAGGER = 0.035  # décalage (s) entre le début de chaque ligne
WIPE_DUR = 0.55  # durée du "tapage" d'une ligne


def image_to_ascii_rows(path: str, cols: int, rows: int) -> list[str]:
    img = Image.open(path).convert("L")
    img = img.resize((cols, rows))
    arr = np.array(img)

    ascii_rows = []
    ramp_len = len(RAMP)
    for r in range(rows):
        line_chars = []
        for c in range(cols):
            brightness = arr[r, c] / 255.0  # 0 = noir, 1 = blanc
            idx = int((1 - brightness) * (ramp_len - 1))
            line_chars.append(RAMP[idx])
        ascii_rows.append("".join(line_chars))
    return ascii_rows


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(rows: list[str]) -> str:
    width = COLS * CHAR_W
    height = ROWS * CHAR_H + 20

    svg_rows = []
    for i, row_text in enumerate(rows):
        y = i * CHAR_H + FONT_SIZE
        start = round(i * STAGGER, 3)
        end = round(start + WIPE_DUR, 3)
        row_width = len(row_text) * CHAR_W
        safe_text = escape_xml(row_text)

        # clipPath qui grandit de 0 -> largeur totale de la ligne (wipe gauche->droite)
        svg_rows.append(f'''
    <clipPath id="clip{i}">
      <rect x="0" y="{y - FONT_SIZE}" width="0" height="{CHAR_H}">
        <animate attributeName="width" from="0" to="{row_width:.1f}"
          begin="{start}s" dur="{WIPE_DUR}s" fill="freeze" calcMode="spline"
          keySplines="0.25 0.1 0.25 1" />
      </rect>
    </clipPath>''')

    text_elements = []
    cursor_elements = []
    for i, row_text in enumerate(rows):
        y = i * CHAR_H + FONT_SIZE
        start = round(i * STAGGER, 3)
        end = round(start + WIPE_DUR, 3)
        row_width = len(row_text) * CHAR_W
        safe_text = escape_xml(row_text)

        text_elements.append(
            f'    <text x="0" y="{y}" font-family="Consolas, \'Courier New\', monospace" '
            f'font-size="{FONT_SIZE}" fill="{FILL_COLOR}" xml:space="preserve" '
            f'clip-path="url(#clip{i})">{safe_text}</text>'
        )

        # petit curseur bloc qui suit le front d'écriture puis disparaît
        cursor_elements.append(f'''
    <rect x="0" y="{y - FONT_SIZE + 1}" width="{CHAR_W:.1f}" height="{CHAR_H - 2}" fill="{FILL_COLOR}" opacity="0">
      <animate attributeName="x" from="0" to="{row_width:.1f}" begin="{start}s" dur="{WIPE_DUR}s" fill="freeze" />
      <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.01;0.9;1"
        begin="{start}s" dur="{WIPE_DUR}s" fill="freeze" />
    </rect>''')

    svg = f'''<svg viewBox="0 0 {width:.0f} {height:.0f}" xmlns="http://www.w3.org/2000/svg"
     font-family="Consolas, 'Courier New', monospace">
  <defs>{"".join(svg_rows)}
  </defs>
  <rect x="0" y="0" width="{width:.0f}" height="{height:.0f}" fill="none" />
{chr(10).join(text_elements)}
{chr(10).join(cursor_elements)}
</svg>
'''
    return svg


if __name__ == "__main__":
    rows = image_to_ascii_rows(INPUT_PATH, COLS, ROWS)
    svg_content = build_svg(rows)
    with open(OUTPUT_PATH, "w") as f:
        f.write(svg_content)
    print(f"SVG écrit -> {OUTPUT_PATH} ({COLS}x{ROWS} caractères)")
