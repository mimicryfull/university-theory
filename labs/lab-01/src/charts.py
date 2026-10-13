"""SVG-графіки PMF/PDF та CDF без зовнішніх бібліотек."""

import html
import json
import math
from pathlib import Path

COLORS = ("#2563eb", "#d97706")


def text(x, y, label, anchor="start", size=21, fill="#172033"):
    return f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" font-size="{size}" fill="{fill}">{html.escape(str(label))}</text>'


def line(x1, y1, x2, y2, color="#cbd5e1", width=1):
    return f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{width}"/>'


def save(path, pieces, height=730):
    header = f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{height}" viewBox="0 0 1100 {height}"><rect width="100%" height="100%" fill="white"/><g font-family="Literata, DejaVu Sans, serif">'
    path.write_text(header + "\n" + "\n".join(pieces) + "</g></svg>", encoding="utf-8")


def axes(start, stop, ymax, top, title):
    left, width, height = 95, 940, 210
    xx = lambda x: left + width * (x - start) / (stop - start)
    yy = lambda y: top + height * (1 - y / ymax)
    pieces = [text(left, top - 20, title, size=22)]
    for i in range(5):
        y = ymax * i / 4
        pieces.extend([line(left, yy(y), left + width, yy(y)), text(left - 13, yy(y) + 7, f"{y:.3g}", "end", 20)])
    for i in range(7):
        x = start + (stop - start) * i / 6
        pieces.extend([line(xx(x), top, xx(x), top + height, "#eef2f6"), text(xx(x), top + height + 30, f"{x:.3g}", "middle", 20)])
    pieces.append(text(left + width, top + height + 57, "x", "end", 21))
    return pieces, xx, yy


def generate_charts(results, folder):
    folder = Path(folder)
    for distribution in results["distributions"]:
        rows = distribution["rows"]
        discrete = distribution["kind"] == "discrete"
        start = rows[0]["x"] - 0.5 if discrete else rows[0]["x"]
        stop = rows[-1]["x"] + 0.5 if discrete else rows[-1]["x"]
        ymax = max(row["value"] for row in rows) * 1.14
        params = "; ".join(f"{key}={value:g}" for key, value in distribution["parameters"].items())
        pieces = [text(550, 35, distribution["label"], "middle", 28), text(550, 68, params, "middle", 22)]
        panel, xx, yy = axes(start, stop, ymax, 115, "Імовірність P(X=k)" if discrete else "Густина ймовірності f(x)")
        pieces.extend(panel)
        if discrete:
            width = min(80, (xx(1) - xx(0)) * 0.6)
            for row in rows:
                x, value = xx(row["x"]), row["value"]
                pieces.append(f'<rect x="{x-width/2:.2f}" y="{yy(value):.2f}" width="{width:.2f}" height="{yy(0)-yy(value):.2f}" fill="{COLORS[0]}"/>')
                pieces.append(text(x, yy(value) - 9, f"{value:.4f}", "middle", 19))
        else:
            points = " ".join(f'{xx(row["x"]):.2f},{yy(row["value"]):.2f}' for row in rows)
            pieces.append(f'<polyline points="{points}" fill="none" stroke="{COLORS[0]}" stroke-width="3"/>')
        panel, xx, yy = axes(start, stop, 1, 465, "Функція розподілу F(x)=P(X≤x)")
        pieces.extend(panel)
        if discrete:
            previous, previous_x = 0, start
            for row in rows:
                x, cdf = row["x"], row["cdf"]
                pieces.append(line(xx(previous_x), yy(previous), xx(x), yy(previous), COLORS[1], 3))
                pieces.append(f'<circle cx="{xx(x):.2f}" cy="{yy(previous):.2f}" r="4" fill="white" stroke="{COLORS[1]}" stroke-width="2"/>')
                pieces.append(f'<circle cx="{xx(x):.2f}" cy="{yy(cdf):.2f}" r="4" fill="{COLORS[1]}"/>')
                previous, previous_x = cdf, x
            pieces.append(line(xx(previous_x), yy(previous), xx(stop), yy(previous), COLORS[1], 3))
        else:
            points = " ".join(f'{xx(row["x"]):.2f},{yy(row["cdf"]):.2f}' for row in rows)
            pieces.append(f'<polyline points="{points}" fill="none" stroke="{COLORS[1]}" stroke-width="3"/>')
        save(folder / (distribution["key"] + ".svg"), pieces, 745)
    rows = results["tails"]
    pieces = [text(550, 35, "Хвости: стандартна нормальна та Стьюдента", "middle", 27),
              text(550, 70, "Спільні центр 0 та одиниця масштабу; різні форми хвостів", "middle", 22)]
    left, top, width, height = 100, 110, 920, 330
    xx = lambda x: left + width * x / 6
    yy = lambda p: top + height * (-math.log10(max(p, 1e-10))) / 10
    for power in range(0, 11, 2):
        y = top + height * power / 10
        pieces.extend([line(left, y, left + width, y), text(left - 15, y + 7, f"10⁻{power}" if power else "1", "end", 21)])
    for x in range(7):
        pieces.extend([line(xx(x), top, xx(x), top + height, "#eef2f6"), text(xx(x), top + height + 35, x, "middle", 22)])
    for index, key in enumerate(("normal_survival", "student_survival")):
        points = " ".join(f'{xx(row["x"]):.2f},{yy(row[key]):.2f}' for row in rows)
        pieces.append(f'<polyline points="{points}" fill="none" stroke="{COLORS[index]}" stroke-width="4"/>')
    pieces.extend([text(100, 95, "P(X>x), логарифмічна вісь", size=22), text(1015, 502, "x", "end"),
                   text(100, 535, "Синя: N(0,1)", size=23, fill=COLORS[0]),
                   text(440, 535, f'Помаранчева: Стьюдента ν={results["config"]["student"]["df"]}', size=23, fill=COLORS[1])])
    save(folder / "tail-comparison.svg", pieces, 575)


def make_dashboard(results, destination):
    parts = ['<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
             '<title>Лабораторна 1 — розподіли</title><style>body{max-width:1000px;margin:32px auto;padding:0 24px;font:18px/1.6 Literata,serif;color:#172033}img{width:100%}figure{margin:24px 0}figcaption{text-align:center}table{border-collapse:collapse;width:100%}td,th{border:1px solid #cbd5e1;padding:10px;text-align:left}</style>',
             f'<h1>Розподіли випадкових величин</h1><p>Біжик Юрій Володимирович · ФЕІ-34с · N={results["student_number"]}</p>',
             '<p>Теоретичні PMF/PDF і CDF; випадкові вибірки не генеруються.</p>']
    for i, distribution in enumerate(results["distributions"], 1):
        label = html.escape(distribution["label"])
        parts.append(f'<figure><img src="figures/{distribution["key"]}.svg" alt="{label}"><figcaption>Рисунок {i} — {label}: PMF/PDF та CDF</figcaption></figure>')
    parts.append('<figure><img src="figures/tail-comparison.svg" alt="Порівняння хвостів"><figcaption>Рисунок 8 — Порівняння правих хвостів</figcaption></figure>')
    parts.append('<p>Розподіл Пуассона зображений лише до заданого kmax без перенормування. У Парето α=1 сподівання нескінченне, у Стьюдента ν=1 воно не існує.</p></html>')
    destination.write_text("\n".join(parts), encoding="utf-8")


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    generate_charts(json.loads((root / "data/results.json").read_text(encoding="utf-8")), root / "figures")
