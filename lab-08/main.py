#!/usr/bin/env python3
"""Лексикографічна оптимізація та послідовні поступки; лише stdlib."""
import argparse
import csv
import json
import random
from pathlib import Path


def lexicographic(rows, order):
    candidates = list(rows)
    steps = []
    for criterion in order:
        before = [r['id'] for r in candidates]
        best = max(r['criteria'][criterion - 1] for r in candidates)
        candidates = [r for r in candidates if r['criteria'][criterion - 1] == best]
        steps.append(dict(criterion=criterion, before_ids=before, optimum=best,
                          retained_ids=[r['id'] for r in candidates]))
    return dict(order=order, steps=steps, winner_ids=[r['id'] for r in candidates])


def concessions(rows, deltas=(1, 2, 3)):
    candidates = list(rows)
    steps = []
    for criterion in range(1, 5):
        before = [r['id'] for r in candidates]
        best = max(r['criteria'][criterion - 1] for r in candidates)
        delta = deltas[criterion - 1] if criterion < 4 else 0
        threshold = best - delta
        # Кожне наступне обмеження накладаємо на вже звужену множину.
        candidates = [r for r in candidates if r['criteria'][criterion - 1] >= threshold]
        steps.append(dict(criterion=criterion, before_ids=before, optimum=best,
                          delta=delta, threshold=threshold,
                          retained_ids=[r['id'] for r in candidates]))
    return dict(order=[1, 2, 3, 4], deltas=list(deltas), steps=steps,
                winner_ids=[r['id'] for r in candidates])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--student-number', type=int, required=True, help='N — номер у журналі, додатне ціле')
    parser.add_argument('--seed', type=int, default=8008, help='відтворюваний seed (типово 8008)')
    parser.add_argument('--input', type=Path, help='JSON масив N+3 рядків по 4 цілі оцінки 0..5')
    parser.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    if args.student_number < 1:
        parser.error('--student-number має бути додатним')
    count = args.student_number + 3
    if args.input:
        matrix = json.loads(args.input.read_text(encoding='utf-8'))
        if (not isinstance(matrix, list) or len(matrix) != count
                or any(not isinstance(row, list) or len(row) != 4 for row in matrix)
                or any(type(v) is not int or not 0 <= v <= 5 for row in matrix for v in row)):
            parser.error('вхід має містити N+3 рядків по 4 цілі оцінки в межах 0..5')
    else:
        rng = random.Random(args.seed)
        matrix = [[rng.randint(0, 5) for _ in range(4)] for _ in range(count)]
    rows = [dict(id=index, criteria=values) for index, values in enumerate(matrix, 1)]
    result = dict(lab=8, student_number=args.student_number, seed=args.seed,
                  source='input' if args.input else 'random', count=count,
                  bounds=[0, 5], direction='max', alternatives=rows,
                  lexicographic=[lexicographic(rows, order) for order in ([2, 1, 3, 4], [4, 1, 2, 3])],
                  concessions=concessions(rows))
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    (output / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with (output / 'alternatives.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['alternative', 'Q1', 'Q2', 'Q3', 'Q4'])
        writer.writerows([r['id'], *r['criteria']] for r in rows)
    with (output / 'steps.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['method', 'criterion', 'optimum', 'delta', 'threshold', 'before_ids', 'retained_ids'])
        for index, run in enumerate(result['lexicographic'], 1):
            for step in run['steps']:
                writer.writerow([f'lexicographic_{index}', step['criterion'], step['optimum'], 0,
                                 step['optimum'], ' '.join(map(str, step['before_ids'])),
                                 ' '.join(map(str, step['retained_ids']))])
        for step in result['concessions']['steps']:
            writer.writerow(['concessions', step['criterion'], step['optimum'], step['delta'],
                             step['threshold'], ' '.join(map(str, step['before_ids'])),
                             ' '.join(map(str, step['retained_ids']))])
    print(json.dumps(dict(lexicographic=[r['winner_ids'] for r in result['lexicographic']],
                          concessions=result['concessions']['winner_ids']), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
