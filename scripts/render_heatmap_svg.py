"""
render_heatmap_svg.py
Rend data/contributions.json en calendrier classique 53 semaines x 7 jours
de cases arrondies, avec une rampe verte façon GitHub.

Révélation : chaque case glisse depuis le haut avec un léger fondu, en
diagonale (semaine + jour), joue une fois puis se fige. Légende
Less -> More + pied de page avec le total de contributions.

Usage: python render_heatmap_svg.py
Sortie: contrib-heatmap.svg (ici: kawthar-contrib-heatmap.svg)
"""
import json
import datetime

INPUT_PATH = "data/contributions.json"
OUTPUT_PATH = "kawthar-contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
#           none      lvl1       lvl2       lvl3       lvl4       (extra top-end, non utilisé par GitHub mais gardé en réserve)

CELL = 11
GAP = 3
STEP = CELL + GAP
LEFT_PAD = 28
TOP_PAD = 20
LEGEND_H = 26
FOOTER_H = 22

STAGGER = 0.006  # par (semaine+jour), donne l'effet diagonale
DUR = 0.35

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def level_color(level: int) -> str:
    level = max(0, min(level, 4))
    return PALETTE[level]


def build_weeks(days: list[dict]) -> list[list[dict | None]]:
    """Regroupe les jours en semaines colonnes (dimanche -> samedi), comme le calendrier GitHub."""
    parsed = []
    for d in days:
        dt = datetime.date.fromisoformat(d["date"])
        parsed.append({**d, "dt": dt})
    parsed.sort(key=lambda d: d["dt"])

    if not parsed:
        return []

    first = parsed[0]["dt"]
    # reculer jusqu'au dimanche précédent (ou égal) pour aligner la première colonne
    offset = (first.weekday() + 1) % 7  # lundi=0 ... dimanche=6 -> on veut dimanche=0
    weeks: list[list[dict | None]] = []
    current_week: list[dict | None] = [None] * offset

    for d in parsed:
        current_week.append(d)
        if len(current_week) == 7:
            weeks.append(current_week)
            current_week = []

    if current_week:
        while len(current_week) < 7:
            current_week.append(None)
        weeks.append(current_week)

    return weeks


def build_svg(payload: dict) -> str:
    days = payload["days"]
    stats = payload["stats"]
    weeks = build_weeks(days)
    n_weeks = len(weeks)

    width = LEFT_PAD + n_weeks * STEP + 10
    height = TOP_PAD + 7 * STEP + LEGEND_H + FOOTER_H

    cells_svg = []
    month_labels = []
    last_month = None

    for wi, week in enumerate(weeks):
        x = LEFT_PAD + wi * STEP
        for di, day in enumerate(week):
            y = TOP_PAD + di * STEP
            if day is None:
                continue

            month = day["dt"].month
            if month != last_month:
                month_labels.append((x, MONTH_ABBR[month - 1]))
                last_month = month

            level = day["level"]
            color = level_color(level)
            delay = round((wi + di) * STAGGER, 3)

            cells_svg.append(f'''
  <rect x="{x}" y="{y - 6}" width="{CELL}" height="{CELL}" rx="2" fill="{color}" opacity="0">
    <animate attributeName="y" from="{y - 6}" to="{y}" begin="{delay}s" dur="{DUR}s" fill="freeze"
      calcMode="spline" keySplines="0.25 0.1 0.25 1" />
    <animate attributeName="opacity" from="0" to="1" begin="{delay}s" dur="{DUR}s" fill="freeze" />
  </rect>''')

    month_labels_svg = "".join(
        f'<text x="{x}" y="{TOP_PAD - 6}" font-family="Consolas, monospace" font-size="10" fill="#8b949e">{label}</text>'
        for x, label in month_labels
    )

    legend_y = TOP_PAD + 7 * STEP + 18
    legend_x_start = width - 190
    legend_swatches = "".join(
        f'<rect x="{legend_x_start + 34 + i * (CELL + 3)}" y="{legend_y - 9}" width="{CELL}" height="{CELL}" rx="2" fill="{level_color(i)}" />'
        for i in range(5)
    )

    total = stats.get("total_last_year", 0)
    streak = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)
    footer_text = f"{total} contributions in the last year · current streak {streak} · longest streak {longest}"

    svg = f'''<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg"
     font-family="Consolas, 'Courier New', monospace">
  <rect x="0" y="0" width="{width}" height="{height}" fill="none" />
  {month_labels_svg}
{"".join(cells_svg)}
  <text x="{legend_x_start}" y="{legend_y}" font-size="10" fill="#8b949e">Less</text>
  {legend_swatches}
  <text x="{legend_x_start + 34 + 5 * (CELL + 3) + 4}" y="{legend_y}" font-size="10" fill="#8b949e">More</text>
  <text x="{LEFT_PAD}" y="{height - 6}" font-size="11" fill="#c9d1d9">{footer_text}</text>
</svg>
'''
    return svg


if __name__ == "__main__":
    with open(INPUT_PATH) as f:
        payload = json.load(f)

    svg_content = build_svg(payload)
    with open(OUTPUT_PATH, "w") as f:
        f.write(svg_content)

    print(f"SVG écrit -> {OUTPUT_PATH}")
