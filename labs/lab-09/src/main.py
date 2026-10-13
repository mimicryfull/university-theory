#!/usr/bin/env python3
"""Навчальний AHP: власний степеневий метод, лише стандартна бібліотека."""
import argparse
import csv
import json
import math
from pathlib import Path
from charts import generate as generate_charts

LAB_ROOT = Path(__file__).resolve().parent.parent

RI = {1: 0, 2: 0, 3: .58, 4: .90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}


def comparison_matrix(scores):
    """Перетворити навчальні оцінки в обернену матрицю шкали 1..9."""
    n = len(scores)
    if any(not math.isfinite(x) or x <= 0 for x in scores):
        raise ValueError("Навчальні оцінки мають бути додатними скінченними числами")
    a = [[1.0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            ratio = scores[i] / scores[j]
            strength = min(9, max(1, math.floor(max(ratio, 1 / ratio) + .5)))
            a[i][j] = float(strength) if ratio >= 1 else 1 / strength
            a[j][i] = 1 / a[i][j]
    return a


def priorities(a):
    n = len(a)
    if n not in RI or any(len(row) != n for row in a):
        raise ValueError("Потрібна квадратна матриця порядку від 1 до 10")
    for i in range(n):
        for j in range(n):
            if not math.isfinite(a[i][j]) or a[i][j] <= 0:
                raise ValueError("Елементи матриці мають бути додатними та скінченними")
            if abs(a[i][j] * a[j][i] - 1) > 1e-9 or (i == j and abs(a[i][j] - 1) > 1e-9):
                raise ValueError("Матриця повинна бути взаємно оберненою з одиничною діагоналлю")
    w = [1 / n] * n
    for iteration in range(1, 10001):
        aw = [sum(a[i][j] * w[j] for j in range(n)) for i in range(n)]
        new = [x / sum(aw) for x in aw]
        delta = max(abs(new[i] - w[i]) for i in range(n))
        w = new
        if delta < 1e-12:
            break
    else:
        raise ArithmeticError("Степеневий метод не збігся за 10000 ітерацій")
    aw = [sum(a[i][j] * w[j] for j in range(n)) for i in range(n)]
    lam = sum(aw[i] / w[i] for i in range(n)) / n
    ci = max(0.0, (lam - n) / (n - 1)) if n > 1 else 0.0
    geometric = [math.exp(sum(math.log(x) for x in row) / n) for row in a]
    geometric = [x / sum(geometric) for x in geometric]
    return {"matrix": a, "weights": w, "geometric_weights": geometric,
            "lambda_max": lam, "ci": ci, "ri": RI[n], "cr": ci / RI[n] if RI[n] else 0.0,
            "iterations": iteration, "acceptable": ci / RI[n] <= .1 if RI[n] else True}


def solve(data):
    criteria, alternatives = data["criteria"], data["alternatives"]
    if len(criteria) < 5 or len(alternatives) < 5:
        raise ValueError("Для роботи потрібні щонайменше 5 критеріїв і 5 альтернатив")
    def matrix(item):
        return item["matrix"] if "matrix" in item else comparison_matrix(item["scores"])
    root = priorities(matrix(data["criteria_comparisons"]))
    if len(root["weights"]) != len(criteria):
        raise ValueError("Розмір матриці критеріїв не відповідає переліку критеріїв")
    local = []
    for criterion in criteria:
        result = priorities(matrix(data["alternative_comparisons"][criterion]))
        if len(result["weights"]) != len(alternatives):
            raise ValueError("Розмір матриці альтернатив не відповідає переліку альтернатив")
        result["criterion"] = criterion
        local.append(result)
    weights = [sum(root["weights"][j] * local[j]["weights"][i]
                   for j in range(len(criteria))) for i in range(len(alternatives))]
    ranking = sorted(range(len(alternatives)), key=lambda i: (-weights[i], i))
    global_ci = root["ci"] + sum(root["weights"][j] * local[j]["ci"] for j in range(len(criteria)))
    global_ri = root["ri"] + sum(root["weights"][j] * local[j]["ri"] for j in range(len(criteria)))
    return {"goal": data["goal"], "criteria": criteria, "alternatives": alternatives,
            "criteria_result": root, "local_results": local,
            "local_priority_matrix": [[local[j]["weights"][i] for j in range(len(criteria))]
                                      for i in range(len(alternatives))],
            "global_weights": weights, "ranking": [{"rank": k + 1, "alternative": alternatives[i],
                                                      "weight": weights[i]} for k, i in enumerate(ranking)],
            "global_ci": global_ci, "global_ri": global_ri, "global_cr": global_ci / global_ri,
            "all_local_acceptable": root["acceptable"] and all(x["acceptable"] for x in local)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=(LAB_ROOT / "data" / "input.json"))
    parser.add_argument("--output-dir", type=Path, default=(LAB_ROOT / "data"))
    parser.add_argument("--figures-dir", type=Path, default=LAB_ROOT / "figures",
                        help="Каталог векторних рисунків, окремий від даних")
    args = parser.parse_args()
    args.figures_dir.mkdir(parents=True, exist_ok=True)
    data = json.loads(args.input.read_text(encoding="utf-8"))
    result = solve(data)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (args.output_dir / "ranking.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Місце", "Альтернатива", "Глобальний пріоритет"])
        for row in result["ranking"]:
            writer.writerow([row["rank"], row["alternative"], row["weight"]])
    generate_charts(result, args.figures_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
