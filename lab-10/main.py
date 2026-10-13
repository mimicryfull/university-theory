#!/usr/bin/env python3
"""Пошук усіх сідлових точок матричної гри з нульовою сумою."""
import argparse
import csv
import json
import math
from pathlib import Path


def solve_game(game):
    a = game["matrix"]
    if not a or not a[0] or any(len(row) != len(a[0]) for row in a):
        raise ValueError("Матриця повинна бути непорожньою та прямокутною")
    if any(not math.isfinite(x) for row in a for x in row):
        raise ValueError("Виграші мають бути скінченними числами")
    if len(game["row_strategies"]) != len(a) or len(game["column_strategies"]) != len(a[0]):
        raise ValueError("Кількість назв стратегій має відповідати розмірам матриці")
    row_minima = [min(row) for row in a]
    column_maxima = [max(row[j] for row in a) for j in range(len(a[0]))]
    lower, upper = max(row_minima), min(column_maxima)
    saddles = [{"row": i + 1, "column": j + 1, "value": a[i][j],
                "row_strategy": game["row_strategies"][i], "column_strategy": game["column_strategies"][j]}
               for i in range(len(a)) for j in range(len(a[0]))
               if a[i][j] == row_minima[i] and a[i][j] == column_maxima[j]]
    result = dict(game)
    result.update(row_minima=row_minima, column_maxima=column_maxima,
                  lower_value=lower, upper_value=upper, saddle_points=saddles,
                  pure_equilibrium=bool(saddles), pure_value=lower if saddles else None)
    # Для 2x2 без чистої рівноваги додатково отримуємо змішані стратегії.
    if not saddles and len(a) == len(a[0]) == 2:
        aa, b = a[0]
        c, d = a[1]
        denominator = aa - b - c + d
        if denominator:
            p, q = (d - c) / denominator, (d - b) / denominator
            if 0 <= p <= 1 and 0 <= q <= 1:
                result["mixed_solution"] = {"row_probabilities": [p, 1 - p],
                                            "column_probabilities": [q, 1 - q],
                                            "value": (aa * d - b * c) / denominator}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", type=int, default=1, choices=[1])
    parser.add_argument("--input", type=Path, default=Path(__file__).with_name("input.json"))
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    result = {"variant": args.variant, "games": [solve_game(game) for game in data["games"]]}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (args.output_dir / "results.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Гра", "Нижня ціна", "Верхня ціна", "Сідлові точки (рядок, стовпець)", "Ціна у чистих стратегіях"])
        for game in result["games"]:
            writer.writerow([game["name"], game["lower_value"], game["upper_value"],
                             "; ".join(f'({x["row"]}, {x["column"]})' for x in game["saddle_points"]), game["pure_value"]])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
