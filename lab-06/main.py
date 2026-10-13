"""Лінійна та максимінна згортка: відтворювана генерація або ввід JSON."""

import argparse
import json
import math
import random
from pathlib import Path


def generate(student_number, seed):
    if student_number < 1:
        raise ValueError("Номер у журналі має бути додатним.")
    rng = random.Random(seed)
    count = 3 + student_number
    matrix = [[rng.randint(1, count) for _ in range(5)] for _ in range(count)]
    norms = [rng.randint(1, count) for _ in range(5)]
    raw_weights = [rng.randint(1, 100) for _ in range(5)]
    total = sum(raw_weights)
    return {"student_number": student_number, "seed": seed,
            "alternatives": [f"A{i + 1}" for i in range(count)],
            "criteria": [f"Q{i + 1}" for i in range(5)],
            "matrix": matrix, "norms": norms,
            "weight_numerators": raw_weights, "weight_denominator": total,
            "weights": [w / total for w in raw_weights]}


def solve(data):
    matrix, names = data["matrix"], data["alternatives"]
    norms, weights = data["norms"], data["weights"]
    count = 3 + data["student_number"]
    if len(matrix) != count or len(names) != count or len(set(names)) != count:
        raise ValueError("Потрібно 3+N альтернатив з унікальними назвами.")
    if len(norms) != 5 or len(weights) != 5 or any(len(row) != 5 for row in matrix):
        raise ValueError("Потрібно рівно 5 критеріїв, нормативів і ваг.")
    if any(not isinstance(v, int) or isinstance(v, bool) or not 1 <= v <= count
           for row in matrix for v in row):
        raise ValueError("Оцінки мають бути цілими числами в межах 1..3+N.")
    if any(not isinstance(v, int) or isinstance(v, bool) or not 1 <= v <= count for v in norms):
        raise ValueError("Нормативи мають бути цілими числами в межах 1..3+N.")
    if any(not math.isfinite(w) or w <= 0 for w in weights) or not math.isclose(sum(weights), 1):
        raise ValueError("Ваги мають бути додатними із сумою 1.")
    # Межі для min-max задає шкала генерації, а не випадкові екстремуми вибірки.
    lower, upper = 1, count
    norm_matrix = [[v / norms[j] for j, v in enumerate(row)] for row in matrix]
    minmax_matrix = [[(v - lower) / (upper - lower) for v in row] for row in matrix]

    def weighted(rows, reducer):
        return [reducer(w * v for w, v in zip(weights, row)) for row in rows]

    scores = {
        "linear": weighted(matrix, sum),
        "maximin": weighted(matrix, min),
        "normative_maximin": [min(row) for row in norm_matrix],
        "normative_linear": weighted(norm_matrix, sum),
        "normative_weighted_maximin": weighted(norm_matrix, min),
        "normalized_linear": weighted(minmax_matrix, sum),
        "normalized_maximin": weighted(minmax_matrix, min),
    }
    winners = {key: [names[i] for i, score in enumerate(values)
                     if math.isclose(score, max(values), rel_tol=1e-12, abs_tol=1e-12)]
               for key, values in scores.items()}
    return {**data, "normalization_bounds": [lower, upper],
            "normative_matrix": norm_matrix, "normalized_matrix": minmax_matrix,
            "scores": scores, "winners": winners}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--student-number", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260506)
    parser.add_argument("--input", type=Path, help="Ввід альтернатив, нормативів і ваг із JSON")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("results.json"))
    args = parser.parse_args()
    try:
        data = (json.loads(args.input.read_text(encoding="utf-8")) if args.input
                else generate(args.student_number, args.seed))
        if args.input and data["student_number"] != args.student_number:
            raise ValueError("N у JSON має збігатися з --student-number.")
        result = solve(data)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f"Помилка вхідних даних: {exc}\n")
    print(f'N={data["student_number"]}; альтернатив: {len(data["matrix"])}; критеріїв: 5')
    print("Альтернатива | Q1 Q2 Q3 Q4 Q5")
    for name, row in zip(data["alternatives"], data["matrix"]):
        print(name + " | " + " ".join(map(str, row)))
    print("Нормативи:", data["norms"])
    print("Ваги:", " ".join(f"{w:.6f}" for w in data["weights"]))
    for key, values in result["scores"].items():
        print(key, ":", " ".join(f"{v:.6f}" for v in values),
              "; оптимальні:", ", ".join(result["winners"][key]))


if __name__ == "__main__":
    main()
