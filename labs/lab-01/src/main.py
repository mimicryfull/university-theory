"""Сім дискретних/неперервних розподілів; параметри CLI або JSON."""

import argparse
import csv
import json
import math
from pathlib import Path
from charts import generate_charts, make_dashboard

LAB_ROOT = Path(__file__).resolve().parent.parent


def parameters(number):
    return {"student_number": number,
            "bernoulli": {"p": 1 / (number + 1)},
            "binomial": {"p": 1 / (number + 1), "n": number + 2},
            "poisson": {"rate": number + 10, "kmax": number + 5},
            "uniform": {"a": -number, "b": number},
            "normal": {"mean": number, "variance": number / 2},
            "pareto": {"shape": number, "minimum": number},
            "student": {"df": number}}


def beta_fraction(a, b, x):
    """Ланцюговий дріб неповної бета-функції (модифікований алгоритм Ленца)."""
    tiny = 1e-300
    c = 1.0
    d = 1 - (a + b) * x / (a + 1)
    d = 1 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 301):
        even = m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m))
        odd = -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))
        for term in (even, odd):
            d = 1 + term * d
            c = 1 + term / c
            d = 1 / (d if abs(d) > tiny else tiny)
            c = c if abs(c) > tiny else tiny
            delta = d * c
            h *= delta
        if abs(delta - 1) < 3e-14:
            return h
    raise ArithmeticError("Неповна бета-функція не збіглася.")


def regularized_beta(x, a, b):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    factor = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                      + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1) / (a + b + 2):
        return factor * beta_fraction(a, b, x) / a
    return 1 - factor * beta_fraction(b, a, 1 - x) / b


def student_pdf(x, df):
    coefficient = math.exp(math.lgamma((df + 1) / 2) - math.lgamma(df / 2)) / math.sqrt(df * math.pi)
    return coefficient * (1 + x * x / df) ** (-(df + 1) / 2)


def student_cdf(x, df):
    if df == 1:
        return 0.5 + math.atan(x) / math.pi
    probability = 0.5 * regularized_beta(df / (df + x * x), df / 2, 0.5)
    return probability if x < 0 else 1 - probability


def continuous(name, label, params, start, stop, pdf, cdf, mean, variance, extra_points=()):
    xs = sorted(set([start + (stop - start) * i / 800 for i in range(801)] + list(extra_points)))
    return {"key": name, "label": label, "kind": "continuous", "parameters": params,
            "rows": [{"x": x, "value": pdf(x), "cdf": cdf(x)} for x in xs],
            "mean": mean, "variance": variance,
            "visible_mass": cdf(stop) - cdf(start)}


def discrete(name, label, params, xs, pmf, mean, variance):
    total = 0
    rows = []
    for x in xs:
        value = pmf(x)
        total += value
        rows.append({"x": x, "value": value, "cdf": total})
    return {"key": name, "label": label, "kind": "discrete", "parameters": params,
            "rows": rows, "mean": mean, "variance": variance, "visible_mass": total}


def solve(config):
    number = config["student_number"]
    if not isinstance(number, int) or number < 1:
        raise ValueError("N має бути додатним цілим.")
    bern, bino, pois = (config[key] for key in ("bernoulli", "binomial", "poisson"))
    unif, norm, par, stu = (config[key] for key in ("uniform", "normal", "pareto", "student"))
    if not 0 < bern["p"] < 1 or not 0 < bino["p"] < 1:
        raise ValueError("Ймовірності повинні належати (0,1).")
    if not isinstance(bino["n"], int) or bino["n"] < 1 or not isinstance(pois["kmax"], int) or pois["kmax"] < 0:
        raise ValueError("n — додатне ціле; kmax — невід'ємне ціле.")
    if pois["rate"] <= 0 or unif["a"] >= unif["b"] or norm["variance"] <= 0 or min(par.values()) <= 0 or stu["df"] <= 0:
        raise ValueError("Некоректні параметри розподілу.")
    p, n, rate = bino["p"], bino["n"], pois["rate"]
    distributions = [
        discrete("bernoulli", "Розподіл Бернуллі", bern, range(2),
                 lambda x: bern["p"] if x == 1 else 1 - bern["p"], bern["p"], bern["p"] * (1 - bern["p"])),
        discrete("binomial", "Біноміальний розподіл", bino, range(n + 1),
                 lambda x: math.comb(n, x) * p ** x * (1 - p) ** (n - x), n * p, n * p * (1 - p)),
        discrete("poisson", "Розподіл Пуассона", pois, range(pois["kmax"] + 1),
                 lambda x: math.exp(-rate + x * math.log(rate) - math.lgamma(x + 1)), rate, rate),
    ]
    a, b = unif["a"], unif["b"]
    # Додаткові точки обабіч меж відображають стрибки густини без згладжування.
    gap = (b - a) * 1e-8
    distributions.append(continuous("uniform", "Рівномірний розподіл", unif, a - (b - a) / 4, b + (b - a) / 4,
                                   lambda x: 1 / (b - a) if a <= x <= b else 0,
                                   lambda x: max(0, min(1, (x - a) / (b - a))),
                                   (a + b) / 2, (b - a) ** 2 / 12, (a - gap, a, b, b + gap)))
    mean, variance = norm["mean"], norm["variance"]
    sigma = math.sqrt(variance)
    distributions.append(continuous("normal", "Нормальний розподіл", norm, mean - 4 * sigma, mean + 4 * sigma,
                                   lambda x: math.exp(-(x - mean) ** 2 / (2 * variance)) / math.sqrt(2 * math.pi * variance),
                                   lambda x: (1 + math.erf((x - mean) / math.sqrt(2 * variance))) / 2,
                                   mean, variance))
    shape, minimum = par["shape"], par["minimum"]
    distributions.append(continuous("pareto", "Розподіл Парето", par, 0, 10 * minimum,
                                   lambda x: shape * minimum ** shape / x ** (shape + 1) if x >= minimum else 0,
                                   lambda x: 1 - (minimum / x) ** shape if x >= minimum else 0,
                                   shape * minimum / (shape - 1) if shape > 1 else "+∞",
                                   shape * minimum ** 2 / ((shape - 1) ** 2 * (shape - 2)) if shape > 2 else "не існує як скінченна",
                                   (minimum - minimum * 1e-8, minimum)))
    df = stu["df"]
    distributions.append(continuous("student", "Розподіл Стьюдента", stu, -10, 10,
                                   lambda x: student_pdf(x, df), lambda x: student_cdf(x, df),
                                   0 if df > 1 else "не існує",
                                   df / (df - 2) if df > 2 else "не існує як скінченна"))
    tails = [{"x": x / 10, "normal_survival": 0.5 * math.erfc(x / 10 / math.sqrt(2)),
              "student_survival": 1 - student_cdf(x / 10, df)} for x in range(61)]
    return {"student_number": number, "config": config, "distributions": distributions,
            "tails": tails, "tail_comparison": "Стандартна N(0,1) і Стьюдента з ν=N"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--student-number", type=int, default=1)
    parser.add_argument("--input", type=Path, help="Параметри всіх розподілів у JSON")
    parser.add_argument("--output", type=Path, default=LAB_ROOT / "data")
    parser.add_argument("--figures-dir", type=Path, default=LAB_ROOT / "figures")
    args = parser.parse_args()
    try:
        config = json.loads(args.input.read_text(encoding="utf-8")) if args.input else parameters(args.student_number)
        result = solve(config)
        args.output.mkdir(parents=True, exist_ok=True)
        args.figures_dir.mkdir(parents=True, exist_ok=True)
        (args.output / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        for distribution in result["distributions"]:
            with (args.output / (distribution["key"] + ".csv")).open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=("x", "value", "cdf"))
                writer.writeheader()
                writer.writerows(distribution["rows"])
        generate_charts(result, args.figures_dir)
        make_dashboard(result, LAB_ROOT / "index.html")
    except (ValueError, KeyError, TypeError, OSError, ArithmeticError) as exc:
        parser.exit(2, f"Помилка: {exc}\n")
    for distribution in result["distributions"]:
        print(f'{distribution["label"]}: E={distribution["mean"]}; D={distribution["variance"]}; '
              f'показана маса={distribution["visible_mass"]:.9f}')


if __name__ == "__main__":
    main()
