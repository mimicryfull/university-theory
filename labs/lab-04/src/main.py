"""Лабораторна 4: вибірка 3000 чисел, частоти та шість середніх величин."""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import random
import statistics
from collections import Counter
from pathlib import Path
from charts import generate_charts

LAB_ROOT = Path(__file__).resolve().parent.parent


def calculate_means(sample: list[int]) -> dict:
    """Середні для додатної числової вибірки; моди зберігаються всі."""
    if not sample or any(x <= 0 for x in sample):
        raise ValueError("Вибірка має бути непорожньою і строго додатною.")
    count = len(sample)
    ordered = sorted(sample)
    frequencies = Counter(sample)
    highest = max(frequencies.values())
    modes = sorted(x for x, frequency in frequencies.items()
                   if frequency == highest)
    arithmetic = math.fsum(sample) / count
    quadratic = math.sqrt(math.fsum(x * x for x in sample) / count)
    geometric = math.exp(math.fsum(math.log(x) for x in sample) / count)
    harmonic = count / math.fsum(1 / x for x in sample)
    median = statistics.median(ordered)
    middle = count // 2
    if count % 2:
        left_median = right_median = ordered[middle]
    else:
        left_median, right_median = ordered[middle - 1:middle + 1]
    variance = math.fsum((x - arithmetic) ** 2 for x in sample) / count
    return {
        "arithmetic": arithmetic,
        "modes": modes,
        "mode_frequency": highest,
        "median": median,
        "left_median": left_median,
        "right_median": right_median,
        "quadratic": quadratic,
        "geometric": geometric,
        "harmonic": harmonic,
        "variance": variance,
    }


def make_histogram(frequencies: list[dict], destination: Path) -> None:
    """Векторний графік: x — значення, y — абсолютна частота."""
    width, height = 1000, 560
    left, top, right, bottom = 86, 55, 35, 80
    chart_width = width - left - right
    chart_height = height - top - bottom
    highest = max(row["count"] for row in frequencies)
    ceiling = max(100, math.ceil(highest * 1.12 / 100) * 100)
    step = chart_width / len(frequencies)
    pieces = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<g font-family="Literata, serif" font-size="18" fill="#18181b">',
        '<text x="500" y="28" text-anchor="middle">'
        'Частотний розподіл вибірки, n = 3000</text>',
    ]
    for index in range(6):
        value = ceiling * index / 5
        y = top + chart_height * (1 - index / 5)
        pieces.append(
            f'<line x1="{left}" y1="{y}" x2="{width-right}" '
            f'y2="{y}" stroke="#d4d4d8"/>'
            f'<text x="{left-12}" y="{y+6}" text-anchor="end">'
            f'{value:g}</text>'
        )
    for index, row in enumerate(frequencies):
        x = left + step * index + step * 0.15
        bar_height = chart_height * row["count"] / ceiling
        y = top + chart_height - bar_height
        label_x = left + step * (index + 0.5)
        pieces.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{step*.7:.2f}" '
            f'height="{bar_height:.2f}" fill="#2563eb"/>'
            f'<text x="{label_x:.2f}" y="{y-10:.2f}" '
            f'text-anchor="middle">{row["count"]}</text>'
            f'<text x="{label_x:.2f}" y="{top+chart_height+29}" '
            f'text-anchor="middle">{row["value"]}</text>'
        )
    pieces += [
        f'<path d="M{left},{top} V{top+chart_height} '
        f'H{width-right}" fill="none" stroke="#18181b"/>',
        f'<text x="{left+chart_width/2}" y="{height-18}" '
        'text-anchor="middle">Значення випадкової величини x</text>',
        '<text x="24" y="280" transform="rotate(-90 24 280)" '
        'text-anchor="middle">Абсолютна частота</text>',
        '</g></svg>',
    ]
    destination.write_text("\n".join(pieces), encoding="utf-8")


def write_csv(path: Path, header: list[str], rows) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def make_dashboard(results: dict, destination: Path) -> None:
    """Самодостатній HTML для перегляду вибірки, без сервера чи бібліотек."""
    means = results["means"]
    labels = [
        ("Середнє арифметичне", means["arithmetic"]),
        ("Медіана", means["median"]),
        ("Середнє квадратичне", means["quadratic"]),
        ("Середнє геометричне", means["geometric"]),
        ("Середнє гармонічне", means["harmonic"]),
    ]
    rows = "".join(f"<tr><td>{label}</td><td>{value:.8f}</td></tr>"
                   for label, value in labels)
    mode = ", ".join(map(str, means["modes"]))
    original = html.escape(", ".join(map(str, results["sample"])))
    ordered = html.escape(", ".join(map(str, results["sorted_sample"])))
    destination.write_text(f'''<!doctype html>
<html lang="uk"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Лабораторна 4 — середні величини</title>
<style>
body{{font:18px/1.6 Literata,serif;margin:32px auto;padding:0 24px;max-width:1000px;color:#18181b}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:10px;text-align:left}}
img{{width:100%}}summary{{cursor:pointer;font-weight:bold}}p.sample{{font:14px/1.7 MonoLisaCode,monospace;overflow-wrap:anywhere}}
figure{{margin:12pt 0}}figure img{{display:block}}figcaption{{margin-top:6pt;font-size:12pt;text-align:center}}
</style>
<h1>Методи обчислення середніх величин</h1>
<p>Біжик Юрій Володимирович · ФЕІ-34с · N = {results["student_number"]}</p>
<p>n = {results["size"]}, діапазон 1..{results["maximum"]}, seed = {results["seed"]}.</p>
<figure><img src="figures/histogram.svg" alt="Графік абсолютних частот"><figcaption>Рисунок 1 — Частотний розподіл згенерованої вибірки</figcaption></figure>
<figure><img src="figures/empirical-cdf.svg" alt="Емпірична функція розподілу"><figcaption>Рисунок 2 — Емпірична функція розподілу</figcaption></figure>
<figure><img src="figures/means-comparison.svg" alt="Порівняння середніх із медіаною"><figcaption>Рисунок 3 — Порівняння середніх величин із медіаною</figcaption></figure>
<figure><img src="figures/sample-boxplot.svg" alt="Квартилі, медіана та розмах вибірки"><figcaption>Рисунок 4 — Квартилі, медіана та розмах вибірки</figcaption></figure>
<figure><table><tr><th>Показник</th><th>Значення</th></tr>{rows}
<tr><td>Мода / моди</td><td>{mode}</td></tr></table><figcaption>Таблиця 1 — Характеристики згенерованої вибірки</figcaption></figure>
<details><summary>Початкова вибірка: всі 3000 значень</summary><p class="sample">{original}</p></details>
<details><summary>Проранжована вибірка: всі 3000 значень</summary><p class="sample">{ordered}</p></details>
</html>''', encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--student-number", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260401)
    parser.add_argument("--output", type=Path,
                        default=(LAB_ROOT / "data"))
    parser.add_argument("--print-sample", action="store_true")
    parser.add_argument("--figures-dir", type=Path, default=LAB_ROOT / "figures",
                        help="Каталог векторних рисунків, окремий від даних")
    arguments = parser.parse_args()
    arguments.figures_dir.mkdir(parents=True, exist_ok=True)
    if arguments.student_number < 1:
        parser.error("Номер у журналі має бути додатним цілим числом.")
    size = 3000
    maximum = 5 * arguments.student_number
    generator = random.Random(arguments.seed)
    sample = [generator.randint(1, maximum) for _ in range(size)]
    ordered = sorted(sample)
    counts = Counter(sample)
    cumulative = 0
    frequencies = []
    for value in range(1, maximum + 1):
        count = counts[value]
        start = cumulative + 1 if count else None
        cumulative += count
        frequencies.append({
            "value": value, "count": count, "relative": count / size,
            "rank_start": start, "rank_end": cumulative if count else None,
        })
    results = {
        "student_number": arguments.student_number,
        "seed": arguments.seed, "size": size, "maximum": maximum,
        "sample": sample, "sorted_sample": ordered,
        "frequencies": frequencies, "means": calculate_means(sample),
    }
    folder = arguments.output
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(folder / "sample.csv", ["index", "value"],
              enumerate(sample, start=1))
    write_csv(folder / "sorted_sample.csv", ["rank", "value"],
              enumerate(ordered, start=1))
    write_csv(folder / "frequencies.csv",
              ["value", "count", "relative", "rank_start", "rank_end"],
              ([row[key] for key in
                ["value", "count", "relative", "rank_start", "rank_end"]]
               for row in frequencies))
    lines = [" ".join(map(str, ordered[i:i + 30]))
             for i in range(0, size, 30)]
    (folder / "sorted_sample.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    make_histogram(frequencies, arguments.figures_dir / "histogram.svg")
    generate_charts(results, arguments.figures_dir)
    make_dashboard(results, LAB_ROOT / "index.html")
    print(f"N={arguments.student_number}; n={size}; діапазон=1..{maximum}")
    print(f"Seed: {arguments.seed}")
    for row in frequencies:
        print(f"x={row['value']}: n_i={row['count']}, "
              f"p_i={row['relative']:.6f}")
    for name, value in results["means"].items():
        print(f"{name}: {value}")
    if arguments.print_sample:
        print("Початкова вибірка:", sample)
        print("Проранжована вибірка:", ordered)
    print(f"Дані: {folder}; рисунки: {arguments.figures_dir}; HTML: {LAB_ROOT / 'index.html'}")


if __name__ == "__main__":
    main()
