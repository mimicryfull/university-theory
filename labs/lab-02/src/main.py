#!/usr/bin/env python3
"""Бінарні відношення сезонів та основні операції над ними."""
import argparse
import csv
import json
from pathlib import Path
from charts import generate_charts

LAB_ROOT = Path(__file__).resolve().parent.parent
ORDERINGS = {
    1: 'ЗВЛО', 2: 'ВЛОЗ', 3: 'ЛОЗВ', 4: 'ОЗВЛ',
    5: 'ВЗЛО', 6: 'ЗЛОВ', 7: 'ЛОВЗ', 8: 'ОВЗЛ',
    9: 'ЗЛВО', 10: 'ЛВОЗ', 11: 'ВОЗЛ', 12: 'ОЗЛВ',
    13: 'ЗВОЛ', 14: 'ВОЛЗ', 15: 'ОЛЗВ', 16: 'ЛЗВО',
}
SEASONS = {'З': ('зима', 0), 'В': ('весна', 1),
           'Л': ('літо', 2), 'О': ('осінь', 1)}


def read_relation(matrix, names):
    """Матриця 0/1 → множина впорядкованих пар індексів."""
    size = len(names)
    if (len(matrix) != size or any(len(row) != size for row in matrix)
            or any(type(x) is not int or x not in (0, 1) for row in matrix for x in row)):
        raise ValueError('Матриці P і Q мають бути квадратними матрицями 0/1.')
    return {(i, j) for i in range(size) for j in range(size) if matrix[i][j]}


def compose(first, second):
    """За методичкою: спочатку first, потім second; x first z second y."""
    return {(x, y) for x, z in first for zz, y in second if z == zz}


def solve(names, p, q):
    """Усі операції виконуються над скінченними множинами пар."""
    size = len(names)
    universe = {(i, j) for i in range(size) for j in range(size)}
    operations = [
        ('P', 'P: не холодніше', p),
        ('Q', 'Q: так само', q),
        ('intersection', 'P ∩ Q', p & q),
        ('union', 'P ∪ Q', p | q),
        ('difference', 'P \\ Q', p - q),
        ('reverse_difference', 'Q \\ P', q - p),
        ('symmetric_difference', 'P Δ Q', p ^ q),
        ('complement_p', 'Доповнення P', universe - p),
        ('complement_q', 'Доповнення Q', universe - q),
        ('inverse_p', 'P⁻¹', {(j, i) for i, j in p}),
        ('composition', 'P ○ Q', compose(p, q)),
        ('reverse_composition', 'Q ○ P', compose(q, p)),
        ('square_p', 'P²', compose(p, p)),
    ]
    results = {}
    for key, title, relation in operations:
        results[key] = {
            'title': title, 'count': len(relation),
            'matrix': [[int((i, j) in relation) for j in range(size)] for i in range(size)],
            'pairs': [[names[i], names[j]] for i, j in sorted(relation)],
            'domain': [names[i] for i in range(size) if any(x == i for x, y in relation)],
            'range': [names[j] for j in range(size) if any(y == j for x, y in relation)],
        }
    return {'names': names, 'size': size, 'relations': results,
            'inclusions': {'Q_subset_P': q <= p, 'P_subset_Q': p <= q}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', type=int, default=1, choices=range(1, 17))
    parser.add_argument('--input', type=Path, help='JSON з names, P, Q для власних відношень')
    parser.add_argument('--output-dir', type=Path, default=LAB_ROOT / 'data')
    parser.add_argument('--figures-dir', type=Path, default=LAB_ROOT / 'figures')
    args = parser.parse_args()
    if args.input:
        source = json.loads(args.input.read_text(encoding='utf-8'))
        names = source['names']
        if not names or len(names) != len(set(names)):
            parser.error('Назви елементів мають бути непорожнім переліком без повторень.')
        p, q = read_relation(source['P'], names), read_relation(source['Q'], names)
        source_kind = 'input'
    else:
        ordered = [SEASONS[c] for c in ORDERINGS[args.variant]]
        names = [name for name, level in ordered]
        levels = [level for name, level in ordered]
        p = {(i, j) for i in range(len(names)) for j in range(len(names)) if levels[i] >= levels[j]}
        q = {(i, j) for i in range(len(names)) for j in range(len(names)) if levels[i] == levels[j]}
        source = {'names': names, 'P': [[int((i,j) in p) for j in range(len(names))] for i in range(len(names))],
                  'Q': [[int((i,j) in q) for j in range(len(names))] for i in range(len(names))],
                  'ordinal_levels': levels}
        source_kind = 'seasons'
    result = {'variant': args.variant, 'source': source_kind, **solve(names, p, q)}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.figures_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'input.json').write_text(json.dumps(source, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (args.output_dir / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    with (args.output_dir / 'pairs.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['relation', 'first', 'second'])
        for key, relation in result['relations'].items():
            writer.writerows([key, *pair] for pair in relation['pairs'])
    with (args.output_dir / 'summary.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['relation', 'count', 'domain', 'range'])
        for key, relation in result['relations'].items():
            writer.writerow([key, relation['count'], ', '.join(relation['domain']), ', '.join(relation['range'])])
    generate_charts(result, args.figures_dir)
    figures = [('initial-relations.svg', 'Матриці початкових відношень P і Q'),
               ('operation-matrices.svg', 'Матриці результатів основних операцій'),
               ('relation-counts.svg', 'Кількість пар у кожному відношенні')]
    figures_html = ''.join(f'<figure><img src="figures/{filename}" alt="{title}"><figcaption>Рисунок {i} — {title}</figcaption></figure>' for i,(filename,title) in enumerate(figures,1))
    (LAB_ROOT / 'index.html').write_text('''<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Лабораторна 2 — Бінарні відношення</title><style>body{font:18px/1.6 Literata,serif;max-width:1100px;margin:32px auto;padding:0 20px;color:#17212b}img{width:100%}figure{margin:24px 0}figcaption{text-align:center;font-size:16px}</style><h1>Бінарні відношення та операції над ними</h1><p>Біжик Юрій Володимирович · ФЕІ-34с · варіант 1</p><p>P: не холодніше; Q: так само. Весна й осінь мають однаковий порядковий рівень.</p>'''+figures_html+'<p><a href="report/report.pdf">PDF-звіт</a> · <a href="data/results.json">Повні результати JSON</a></p></html>', encoding='utf-8')
    for key, relation in result['relations'].items():
        print(f'{relation["title"]}: {relation["count"]} пар; область визначення {relation["domain"]}; область значень {relation["range"]}')
        for row in relation['matrix']:
            print(' '.join(map(str, row)))


if __name__ == '__main__':
    main()
