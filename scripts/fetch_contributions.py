"""
fetch_contributions.py
Récupère le calendrier de contributions GitHub public (HTML), sans token
ni API GraphQL : https://github.com/users/<username>/contributions

Parse les cellules de jours avec BeautifulSoup et calcule des stats
dérivées (streak courant, plus longue streak, meilleur jour, totaux
mensuels), écrites dans data/contributions.json.

Usage: python fetch_contributions.py [username]
"""
import sys
import json
import datetime
import requests
from bs4 import BeautifulSoup

USERNAME = sys.argv[1] if len(sys.argv) > 1 else "kawtharjguirim"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUTPUT_PATH = "data/contributions.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ProfileReadmeBot/1.0)"
}


def fetch_official_total(soup: BeautifulSoup) -> int | None:
    """GitHub affiche 'N contributions in the last year' dans un <h2>.
    C'est la source de vérité pour le total (le markup des cellules n'expose
    plus de data-count individuel depuis la refonte de la grille)."""
    h2 = soup.find("h2", id="js-contribution-activity-description")
    if not h2:
        return None
    digits = "".join(ch for ch in h2.get_text() if ch.isdigit())
    return int(digits) if digits else None


def fetch_days(username: str) -> tuple[list[dict], int | None]:
    resp = requests.get(f"https://github.com/users/{username}/contributions", headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    official_total = fetch_official_total(soup)

    days = []
    # GitHub rend chaque jour comme <td class="ContributionCalendar-day" ...> ou <rect> selon la version du markup.
    cells = soup.select("td.ContributionCalendar-day, table.ContributionCalendar-grid td")
    if not cells:
        cells = soup.select("rect.ContributionCalendar-day")

    for cell in cells:
        date_str = cell.get("data-date")
        level = cell.get("data-level")
        count_attr = cell.get("data-count")

        if date_str is None:
            continue

        try:
            level_int = int(level) if level is not None else 0
        except ValueError:
            level_int = 0

        try:
            count_int = int(count_attr) if count_attr is not None else None
        except ValueError:
            count_int = None

        days.append({"date": date_str, "level": level_int, "count": count_int})

    return days, official_total


def compute_stats(days: list[dict], official_total: int | None) -> dict:
    days_sorted = sorted(days, key=lambda d: d["date"])

    counted = sum(d["count"] for d in days_sorted if d["count"] is not None)
    total = official_total if official_total is not None else counted

    # streaks (en se basant sur count > 0, ou level > 0 si count manquant)
    def active(d):
        if d["count"] is not None:
            return d["count"] > 0
        return d["level"] > 0

    longest = current = 0
    running = 0
    today = datetime.date.today().isoformat()
    for d in days_sorted:
        if active(d):
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    # streak courant = depuis la fin en remontant
    for d in reversed(days_sorted):
        if d["date"] > today:
            continue
        if active(d):
            current += 1
        else:
            break

    best_day = max(days_sorted, key=lambda d: d["count"] or 0, default=None)

    monthly = {}
    for d in days_sorted:
        month_key = d["date"][:7]
        monthly[month_key] = monthly.get(month_key, 0) + (d["count"] or 0)

    return {
        "total_last_year": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best_day,
        "monthly_totals": monthly,
    }


if __name__ == "__main__":
    print(f"Récupération des contributions pour {USERNAME}...")
    days, official_total = fetch_days(USERNAME)

    if not days:
        print("Aucune donnée trouvée. Le markup GitHub a peut-être changé, ou le profil est privé.")
        sys.exit(1)

    stats = compute_stats(days, official_total)

    payload = {
        "username": USERNAME,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "days": days,
        "stats": stats,
    }

    import os
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"{len(days)} jours récupérés -> {OUTPUT_PATH}")
    print(f"Total: {stats['total_last_year']} · Streak actuel: {stats['current_streak']} · Record: {stats['longest_streak']}")
