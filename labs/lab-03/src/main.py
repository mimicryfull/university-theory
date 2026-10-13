#!/usr/bin/env python3
"""Агрегування та факторизація відношення за взаємною досяжністю."""
import argparse
import csv
import json
from html import escape
from pathlib import Path

from charts import generate

LAB_ROOT = Path(__file__).resolve().parent.parent


def composition(a, b):
    """Булева композиція: існує k з a[i][k] та b[k][j]."""
    n = len(a)
    return [[int(any(a[i][k] and b[k][j] for k in range(n)))
             for j in range(n)] for i in range(n)]


def properties(a):
    n = len(a)
    return {
        "reflexive": all(a[i][i] for i in range(n)),
        "symmetric": all(a[i][j] == a[j][i] for i in range(n) for j in range(n)),
        "antisymmetric": all(i == j or not (a[i][j] and a[j][i]) for i in range(n) for j in range(n)),
        "transitive": all(not (a[i][k] and a[k][j]) or a[i][j]
                          for i in range(n) for k in range(n) for j in range(n)),
    }


def solve(base, student_number, shift_mode, max_powers):
    if not base or any(len(row) != len(base) for row in base):
        raise ValueError("Матриця повинна бути непорожньою та квадратною")
    if any(value not in (0, 1) for row in base for value in row):
        raise ValueError("Елементи матриці мають дорівнювати 0 або 1")
    if student_number < 1:
        raise ValueError("Номер студента має бути додатним")
    n = len(base)
    shift = student_number - 1
    if shift_mode == "rows":
        k = shift % n
        p = [row[k:] + row[:k] for row in base]
    else:
        flat = [value for row in base for value in row]
        k = shift % (n * n)
        flat = flat[k:] + flat[:k]
        p = [flat[i * n:(i + 1) * n] for i in range(n)]
    current = p
    seen = {}
    powers = []
    closure = [[0] * n for _ in range(n)]
    for exponent in range(1, max_powers + 1):
        key = tuple(tuple(row) for row in current)
        powers.append({"exponent": exponent, "matrix": current})
        closure = [[int(closure[i][j] or current[i][j]) for j in range(n)] for i in range(n)]
        if key in seen:
            first_occurrence = seen[key]
            repeated_at = exponent
            break
        seen[key] = exponent
        current = composition(current, p)
    else:
        raise ValueError("Межу степенів до першого повторення перевищено; збільште --max-powers")
    reach = [[int(i == j or closure[i][j]) for j in range(n)] for i in range(n)]
    mutual = [[int(reach[i][j] and reach[j][i]) for j in range(n)] for i in range(n)]
    unassigned = set(range(n))
    classes = []
    while unassigned:
        first = min(unassigned)
        group = [i for i in sorted(unassigned) if mutual[first][i]]
        classes.append(group)
        unassigned.difference_update(group)
    quotient = [[int(any(p[i][j] for i in left for j in right))
                 for right in classes] for left in classes]
    condensation = [[int(i != j and quotient[i][j]) for j in range(len(classes))]
                    for i in range(len(classes))]
    witnesses = [{"source_class": i + 1, "target_class": j + 1,
                  "original_edges": [[u + 1, v + 1] for u in classes[i] for v in classes[j] if p[u][v]]}
                 for i in range(len(classes)) for j in range(len(classes)) if quotient[i][j]]
    return {"student_number": student_number, "shift_count": shift, "shift_mode": shift_mode,
            "base_matrix": base, "matrix": p, "powers": powers,
            "first_repeated_exponent": repeated_at, "first_occurrence_exponent": first_occurrence,
            "period": repeated_at - first_occurrence, "transitive_closure": closure,
            "reachability": reach, "mutual_reachability": mutual,
            "classes": [[i + 1 for i in group] for group in classes],
            "quotient": quotient, "condensation": condensation, "factor_witnesses": witnesses,
            "properties": {"initial": properties(p), "transitive_closure": properties(closure),
                           "reachability": properties(reach), "mutual_reachability": properties(mutual),
                           "quotient": properties(quotient)}}


def write_matrix_csv(path, matrix):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["row/column", *range(1, len(matrix) + 1)])
        for i, row in enumerate(matrix, 1):
            writer.writerow([i, *row])


def write_dashboard(result, path):
    parts = ['<!doctype html><html lang="uk"><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             '<title>Лабораторна 3 — агрегування та факторизація</title>',
             '<style>body{font:18px/1.6 Literata,serif;max-width:1000px;margin:32px auto;padding:0 24px;color:#17212b}figure{margin:12pt 0}img{display:block;width:100%}figcaption{margin-top:6pt;font-size:12pt;text-align:center}table{border-collapse:collapse;margin:auto}th,td{border:1px solid #d5dee8;padding:8px 18px;text-align:center}</style>',
             '<h1>Агрегування та факторизація</h1>',
             '<p>Біжик Юрій Володимирович · ФЕІ-34с · N=1</p>',
             '<p>' + escape(result['source']) + '</p>']
    for number, (key, title) in enumerate([
        ('matrix', 'Початкове відношення P'),
        ('transitive_closure', 'Транзитивне замикання'),
        ('reachability', 'Відношення досяжності'),
        ('mutual_reachability', 'Взаємна досяжність D'),
        ('quotient', 'Фактор-відношення P/D'),
    ], 1):
        matrix = result[key]
        rows = ''.join('<tr>' + ''.join(f'<td>{v}</td>' for v in row) + '</tr>' for row in matrix)
        parts.append(f'<figure><table>{rows}</table><figcaption>Таблиця {number} — {title}</figcaption></figure>')
    for i, group in enumerate(result['classes'], 1):
        parts.append(f'<p>A{i} = {{{", ".join("x"+str(v) for v in group)}}}</p>')
    for number, (filename, title) in enumerate([
        ('initial-graph.svg', 'Первісний граф'), ('relation-matrices.svg', 'Матриці відношень'),
        ('factor-graph.svg', 'Фактор-граф'), ('condensation.svg', 'Конденсація без петель'),
    ], 1):
        parts.append(f'<figure><img src="figures/{filename}" alt="{title}"><figcaption>Рисунок {number} — {title}</figcaption></figure>')
    parts.append('<p>Фактор-граф може мати внутрішньокласову петлю. Ациклічний граф конденсації отримується після її вилучення.</p></html>')
    path.write_text('\n'.join(parts) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--student-number", type=int, default=1)
    parser.add_argument("--input", type=Path, default=LAB_ROOT / "data" / "input.json")
    parser.add_argument("--output-dir", type=Path, default=LAB_ROOT / "data")
    parser.add_argument("--figures-dir", type=Path, default=LAB_ROOT / "figures")
    parser.add_argument("--shift-mode", choices=["flat", "rows"], default="flat",
                        help="Циклічний зсув всієї послідовності елементів або кожного рядка")
    parser.add_argument("--max-powers", type=int, default=10000)
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        result = solve(data["base_matrix"], args.student_number, args.shift_mode, args.max_powers)
        result["source"] = data.get("source", "Власна матриця з вхідного JSON")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        args.figures_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for key in ["matrix", "transitive_closure", "reachability", "mutual_reachability", "quotient", "condensation"]:
            write_matrix_csv(args.output_dir / f"{key}.csv", result[key])
        with (args.output_dir / "classes.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["class", "vertices"])
            for i, group in enumerate(result["classes"], 1):
                writer.writerow([i, " ".join(f"x{value}" for value in group)])
        generate(result, args.figures_dir)
        write_dashboard(result, LAB_ROOT / "index.html")
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f"Помилка: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
