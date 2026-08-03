"""
make_info_card.py
Génère une carte SVG façon `neofetch` : barre de titre + lignes clé/valeur
(Now, Prev, Stack, Highlights) qui apparaissent en fondu, en cascade.

STATIC=1 python make_info_card.py -> émet une frame figée (pour Quick Look local)

Usage: python make_info_card.py
Sortie: info-card.svg (ici: kawthar-info-card.svg)
"""
import os

OUTPUT_PATH = "kawthar-info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

WIDTH = 560
LINE_H = 30
PAD_X = 24
TITLEBAR_H = 40

BG = "#0d1117"
TITLEBAR_BG = "#161b22"
BORDER = "#30363d"
KEY_COLOR = "#7ee787"
VAL_COLOR = "#c9d1d9"
ACCENT = "#58a6ff"
MUTED = "#8b949e"

# (clé, valeur) — contenu narratif que la heatmap ne raconte pas
ROWS = [
    ("user", "kawthar@github"),
    ("---", "---"),
    ("Role", "Software & AI/ML Engineering Student"),
    ("School", "ESPRIM · Honoris United Universities"),
    ("Now", "Building RAG platforms & multi-agent AI tools"),
    ("Stack", "Next.js · FastAPI · LangChain · PyTorch"),
    ("Focus", "RAG pipelines, multimodal AI, full-stack SaaS"),
    ("Team", "NeuroNova — 6-person engineering squad"),
    ("Highlights", "StudyMate AI · OncoVision · EduMind AI"),
]

STAGGER = 0.12
FADE_DUR = 0.5


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg() -> str:
    height = TITLEBAR_H + len(ROWS) * LINE_H + 24

    lines_svg = []
    for i, (key, val) in enumerate(ROWS):
        y = TITLEBAR_H + 28 + i * LINE_H
        start = round(0.3 + i * STAGGER, 3)

        if key == "---":
            content = (
                f'<text x="{PAD_X}" y="{y}" font-family="Consolas, monospace" '
                f'font-size="13" fill="{MUTED}">{"-" * 34}</text>'
            )
        else:
            content = (
                f'<text x="{PAD_X}" y="{y}" font-family="Consolas, monospace" font-size="13">'
                f'<tspan fill="{KEY_COLOR}" font-weight="bold">{esc(key)}</tspan>'
                f'<tspan fill="{MUTED}">: </tspan>'
                f'<tspan fill="{VAL_COLOR}">{esc(val)}</tspan>'
                f'</text>'
            )

        if STATIC:
            group = f'  <g opacity="1">{content}</g>'
        else:
            group = f'''  <g opacity="0">
    {content}
    <animate attributeName="opacity" from="0" to="1" begin="{start}s" dur="{FADE_DUR}s" fill="freeze" />
    <animateTransform attributeName="transform" type="translate"
      from="-8 0" to="0 0" begin="{start}s" dur="{FADE_DUR}s" fill="freeze" calcMode="spline"
      keySplines="0.25 0.1 0.25 1" />
  </g>'''
        lines_svg.append(group)

    svg = f'''<svg viewBox="0 0 {WIDTH} {height}" xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="{WIDTH}" height="{height}" rx="8" fill="{BG}" stroke="{BORDER}" stroke-width="1"/>
  <rect x="0" y="0" width="{WIDTH}" height="{TITLEBAR_H}" rx="8" fill="{TITLEBAR_BG}"/>
  <rect x="0" y="{TITLEBAR_H - 8}" width="{WIDTH}" height="8" fill="{TITLEBAR_BG}"/>
  <circle cx="24" cy="{TITLEBAR_H/2}" r="6" fill="#ff5f56"/>
  <circle cx="44" cy="{TITLEBAR_H/2}" r="6" fill="#ffbd2e"/>
  <circle cx="64" cy="{TITLEBAR_H/2}" r="6" fill="#27c93f"/>
  <text x="{WIDTH/2}" y="{TITLEBAR_H/2 + 4}" text-anchor="middle" font-family="Consolas, monospace"
    font-size="12" fill="{MUTED}">kawthar@github: ~</text>
{chr(10).join(lines_svg)}
</svg>
'''
    return svg


if __name__ == "__main__":
    with open(OUTPUT_PATH, "w") as f:
        f.write(build_svg())
    print(f"SVG écrit -> {OUTPUT_PATH}")
