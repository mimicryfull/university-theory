#!/usr/bin/env python3
"""Парето, лінійна згортка та метод ідеальної точки; лише stdlib."""
import argparse
import csv
import json
import math
import random
from pathlib import Path
from charts import generate as generate_charts

LAB_ROOT = Path(__file__).resolve().parent.parent


def solve(points):
    """Обидва критерії максимізуються; зберігаємо всі рівнозначні рішення."""
    ideal = [max(p[j] for p in points) for j in range(2)]
    rows = []
    for index, point in enumerate(points, 1):
        dominators = [i + 1 for i, other in enumerate(points)
                      if all(a >= b for a, b in zip(other, point))
                      and any(a > b for a, b in zip(other, point))]
        # Цілочисловий чисельник усуває похибки порівняння згорток.
        score_tenths = 3 * point[0] + 7 * point[1]
        distance_squared = sum((a - b) ** 2 for a, b in zip(point, ideal))
        rows.append(dict(id=index, x1=point[0], x2=point[1],
                         q1=point[0], q2=point[1], pareto=not dominators,
                         dominators=dominators, score_tenths=score_tenths,
                         score=score_tenths / 10, distance_squared=distance_squared,
                         distance=math.sqrt(distance_squared)))
    best_score = max(r['score_tenths'] for r in rows)
    best_distance = min(r['distance_squared'] for r in rows)
    return dict(alternatives=rows, ideal=ideal,
                pareto_ids=[r['id'] for r in rows if r['pareto']],
                linear_ids=[r['id'] for r in rows if r['score_tenths'] == best_score],
                ideal_ids=[r['id'] for r in rows if r['distance_squared'] == best_distance],
                best_score=best_score / 10,
                best_distance=math.sqrt(best_distance), weights=[0.3, 0.7])


def save_svg(result, path):
    """Графік векторний: точки, Парето-множина, ідеальна точка та підписи."""
    rows = result['alternatives']
    low = min(min(r['q1'], r['q2']) for r in rows) - 1
    high = max(max(r['q1'], r['q2']) for r in rows) + 1
    width, height, left, top, span = 760, 560, 80, 45, 420
    scale = span / (high - low)

    def xy(x, y):
        return left + (x - low) * scale, top + (high - y) * scale

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<g font-family="sans-serif" font-size="14" fill="#17212b">']
    for tick in range(low, high + 1):
        x, y = xy(tick, tick)
        parts += [f'<path d="M{x},{top} V{top+span} M{left},{y} H{left+span}" stroke="#e4e8ed"/>',
                  f'<text x="{x}" y="{top+span+24}" text-anchor="middle">{tick}</text>',
                  f'<text x="{left-12}" y="{y+5}" text-anchor="end">{tick}</text>']
    parts += [f'<path d="M{left},{top} V{top+span} H{left+span}" fill="none" stroke="#17212b" stroke-width="2"/>',
              f'<text x="{left+span+20}" y="{top+span+5}">Q1 → max</text>',
              f'<text x="{left}" y="{top-16}">Q2 → max</text>']
    groups = {}
    for row in rows:
        groups.setdefault((row['q1'], row['q2']), []).append(row)
    for point, group in groups.items():
        x, y = xy(*point)
        color = '#177245' if group[0]['pareto'] else '#64748b'
        ids = ', '.join(f"A{r['id']}" for r in group)
        parts += [f'<circle cx="{x}" cy="{y}" r="6" fill="{color}"/>',
                  f'<text x="{x+10}" y="{y-10}">{ids}</text>']
        if any(r['id'] in result['linear_ids'] for r in group):
            parts.append(f'<circle cx="{x}" cy="{y}" r="10" fill="none" stroke="#2764bd" stroke-width="2"/>')
        if any(r['id'] in result['ideal_ids'] for r in group):
            parts.append(f'<rect x="{x-14}" y="{y-14}" width="28" height="28" fill="none" stroke="#d27500" stroke-width="2"/>')
    x, y = xy(*result['ideal'])
    parts += [f'<path d="M{x-7},{y-7} L{x+7},{y+7} M{x-7},{y+7} L{x+7},{y-7}" stroke="#b71c1c" stroke-width="3"/>',
              f'<text x="{x+12}" y="{y+20}" fill="#b71c1c">Q*</text>',
              '<text x="530" y="80" fill="#177245">● Парето-оптимальні</text>',
              '<text x="530" y="110" fill="#64748b">● Доміновані</text>',
              '<text x="530" y="140" fill="#2764bd">○ Лінійна згортка</text>',
              '<text x="530" y="170" fill="#d27500">□ Ідеальна точка: вибір</text>',
              '<text x="530" y="200" fill="#b71c1c">× Ідеальна точка Q*</text>',
              '</g></svg>']
    path.write_text('\n'.join(parts), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--student-number', type=int, required=True, help='N — номер у журналі, додатне ціле')
    parser.add_argument('--seed', type=int, default=7007, help='відтворюваний seed (типово 7007)')
    parser.add_argument('--input', type=Path, help='JSON масив рівно 10 пар цілих координат; замість генерації')
    parser.add_argument('--output-dir', type=Path, default=(LAB_ROOT / "data"))
    parser.add_argument("--figures-dir", type=Path, default=LAB_ROOT / "figures",
                        help="Каталог векторних рисунків, окремий від даних")
    args = parser.parse_args()
    args.figures_dir.mkdir(parents=True, exist_ok=True)
    if args.student_number < 1:
        parser.error('--student-number має бути додатним')
    low, high = args.student_number - 3, args.student_number + 3
    if args.input:
        points = json.loads(args.input.read_text(encoding='utf-8'))
        if (not isinstance(points, list) or len(points) != 10
                or any(not isinstance(p, list) or len(p) != 2 for p in points)
                or any(type(v) is not int or not low <= v <= high for p in points for v in p)):
            parser.error('вхід має містити 10 пар цілих координат у межах N−3..N+3')
    else:
        rng = random.Random(args.seed)
        points = [[rng.randint(low, high), rng.randint(low, high)] for _ in range(10)]
    result = dict(lab=7, student_number=args.student_number, seed=args.seed,
                  source='input' if args.input else 'random', bounds=[low, high],
                  normalization='none', metric='euclidean', **solve(points))
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    (output / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    fields = ['id', 'x1', 'x2', 'q1', 'q2', 'pareto', 'score', 'distance_squared', 'distance']
    with (output / 'alternatives.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(result['alternatives'])
    save_svg(result, args.figures_dir / 'alternatives.svg')
    generate_charts(result, args.figures_dir)
    print(json.dumps({k: result[k] for k in ('pareto_ids', 'linear_ids', 'ideal_ids', 'ideal')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
