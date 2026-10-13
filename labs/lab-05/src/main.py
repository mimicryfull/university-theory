"""Метод Терстоуна, випадок V: повна матриця парних переваг."""

import argparse
import json
import math
from pathlib import Path
from statistics import NormalDist
from charts import generate_charts

LAB_ROOT = Path(__file__).resolve().parent.parent


def thurstone(probabilities):
    """МНК для z_ij = M_i - M_j з обмеженням sum(M_i) = 0."""
    n = len(probabilities)
    if n < 2 or any(len(row) != n for row in probabilities):
        raise ValueError("Потрібна квадратна матриця щонайменше 2×2.")
    normal = NormalDist()
    z = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            p = probabilities[i][j]
            if not isinstance(p, (int, float)) or not math.isfinite(p):
                raise ValueError("Ймовірності мають бути скінченними числами.")
            if i == j:
                if not math.isclose(p, 0.5, abs_tol=1e-9):
                    raise ValueError("Діагональні ймовірності мають дорівнювати 0.5.")
            else:
                if not 0 < p < 1:
                    raise ValueError("Для скінченних квантилів потрібно 0 < p < 1.")
                if not math.isclose(p + probabilities[j][i], 1, abs_tol=1e-9):
                    raise ValueError("Потрібно p_ij + p_ji = 1.")
                z[i][j] = normal.inv_cdf(p)
    means = [sum(row) / n for row in z]
    # Формула є розв'язком нормальних рівнянь для повного графа порівнянь.
    residuals = [means[i] - means[j] - z[i][j]
                 for i in range(n) for j in range(i + 1, n)]
    sse = sum(r * r for r in residuals)
    return {"quantiles": z, "means": means,
            "shifted_means": [m - min(means) for m in means],
            "sse": sse, "rmse": math.sqrt(sse / len(residuals)),
            "ranking": sorted(range(n), key=lambda i: (-means[i], i))}


def solve(data):
    names = data["alternatives"]
    result = thurstone(data["probabilities"])
    n = len(names)
    if len(result["means"]) != n:
        raise ValueError("Кількість альтернатив і розмір матриці різні.")
    for key in ("direct_scores", "midpoint_scores", "churchman_initial", "churchman_final"):
        if len(data[key]) != n or any(not math.isfinite(x) for x in data[key]):
            raise ValueError(f"Некоректні оцінки {key}.")
    final = data["churchman_final"]
    if any(x < 0 for x in final) or any(final[i] <= final[i + 1] for i in range(n - 1)):
        raise ValueError("Оцінки Черчмена мають бути невід'ємними і строго спадати.")
    comparisons = []
    for judgement in data["churchman_judgements"]:
        i, group = judgement["left"], judgement["right"]
        if i < 0 or i >= n or not group or i in group or len(set(group)) != len(group):
            raise ValueError("Некоректний набір індексів порівняння.")
        if any(j < 0 or j >= n for j in group):
            raise ValueError("Індекс альтернативи поза діапазоном.")
        a, b = final[i], sum(final[j] for j in group)
        relation = judgement["relation"]
        if relation not in (">", "<="):
            raise ValueError("Відношення має бути > або <=.")
        satisfied = a > b if relation == ">" else a <= b
        comparisons.append({**judgement, "left_score": a, "right_sum": b,
                            "satisfied": satisfied})
    return {"note": data["note"], "alternatives": names,
            "direct_scores": data["direct_scores"],
            "midpoint_scores": data["midpoint_scores"],
            "churchman_scores": final, "churchman_comparisons": comparisons,
            "thurstone": result,
            "ranking": [names[i] for i in result["ranking"]]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=(LAB_ROOT / "data" / "input.json"))
    parser.add_argument("--output", type=Path, default=(LAB_ROOT / "data" / "results.json"))
    parser.add_argument("--figures-dir", type=Path, default=LAB_ROOT / "figures",
                        help="Каталог векторних рисунків, окремий від даних")
    args = parser.parse_args()
    args.figures_dir.mkdir(parents=True, exist_ok=True)
    try:
        inputs = json.loads(args.input.read_text(encoding="utf-8"))
        result = solve(inputs)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        generate_charts(result, args.figures_dir, inputs)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f"Помилка вхідних даних: {exc}\n")
    print(result["note"])
    print("Альтернатива | M (центрована шкала) | M (мінімум = 0)")
    for i in result["thurstone"]["ranking"]:
        print(f'{result["alternatives"][i]} | {result["thurstone"]["means"][i]:.6f} | '
              f'{result["thurstone"]["shifted_means"][i]:.6f}')
    print(f'Сума квадратів нев’язок: {result["thurstone"]["sse"]:.8g}')


if __name__ == "__main__":
    main()
