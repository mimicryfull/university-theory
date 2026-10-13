#!/usr/bin/env python3
"""Векторні графіки зі збережених числових результатів; лише stdlib."""
import json
from html import escape
from pathlib import Path

BLUE = "#2764bd"
GREEN = "#177245"
ORANGE = "#d27500"
RED = "#b71c1c"
INK = "#17212b"
MUTED = "#64748b"


class SVG:
    def __init__(self, width, height):
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="white"/>', '<g font-family="Liberation Sans, sans-serif" fill="#17212b">']

    def text(self, x, y, value, size=17, color=INK, anchor="start", bold=False):
        weight = "bold" if bold else "normal"
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{escape(str(value))}</text>')

    def rect(self, x, y, w, h, fill, stroke="none", sw=1):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def line(self, x1, y1, x2, y2, color="#e4e8ed", sw=1, dashed=False):
        dash = ' stroke-dasharray="7 5"' if dashed else ''
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"{dash}/>')

    def save(self, path):
        path.write_text("\n".join(self.parts + ["</g></svg>"]), encoding="utf-8")


def shade(value, low, high):
    t = (value - low) / (high - low) if high != low else 0.5
    light, dark = (236, 243, 252), (39, 100, 189)
    return '#' + ''.join(f'{round(a + (b-a)*t):02x}' for a, b in zip(light, dark))


def ids(values):
    return ', '.join(f'A{x}' for x in values)


def main():
    lab_root = Path(__file__).resolve().parent.parent
    figures = lab_root / 'figures'
    figures.mkdir(parents=True, exist_ok=True)
    generate(json.loads((lab_root / 'data' / 'results.json').read_text(encoding='utf-8')), figures)


def generate(result, folder):
    rows = result['alternatives']
    svg = SVG(740, 130 + 65*len(rows))
    svg.text(35, 35, 'Оцінки альтернатив: усі критерії максимізуються', 21, bold=True)
    left, top, cw, ch = 155, 95, 115, 65
    for j in range(4):
        svg.text(left+(j+.5)*cw, top-15, f'Q{j+1}', 19, anchor='middle', bold=True)
    for i, row in enumerate(rows):
        svg.text(left-20, top+i*ch+40, f'A{row["id"]}', 19, anchor='end', bold=True)
        for j, value in enumerate(row['criteria']):
            svg.rect(left+j*cw, top+i*ch, cw-3, ch-3, shade(value, 0, 5))
            svg.text(left+(j+.5)*cw, top+i*ch+40, value, 23, anchor='middle', color='white' if value>=3 else INK, bold=True)
    for tick in range(6):
        svg.rect(645, 80+tick*40, 27, 27, shade(tick, 0, 5))
        svg.text(685, 101+tick*40, tick, 17)
    svg.save(folder / 'criteria-heatmap.svg')

    height = 80 + 125*3
    svg = SVG(1050, height)
    svg.text(25, 33, 'Послідовне звуження множини кандидатів', 23, bold=True)
    runs = [(result['lexicographic'][0], 'Лексикографічний порядок Q2 ≻ Q1 ≻ Q3 ≻ Q4', BLUE),
            (result['lexicographic'][1], 'Лексикографічний порядок Q4 ≻ Q1 ≻ Q2 ≻ Q3', BLUE),
            (result['concessions'], 'Поступки: Q1 ≻ Q2 ≻ Q3 ≻ Q4; Δ = 1, 2, 3', ORANGE)]
    for run_index, (run, label, color) in enumerate(runs):
        top = 80 + run_index*125
        svg.text(25, top-15, label, 18, color=color, bold=True)
        boxes = [('Початкова множина', [r['id'] for r in rows])]
        for step in run['steps']:
            threshold = step.get('threshold', step['optimum'])
            relation = '≥' if run_index == 2 and step['criterion'] < 4 else '='
            boxes.append((f'Q{step["criterion"]} {relation} {threshold}', step['retained_ids']))
        for index, (title, values) in enumerate(boxes):
            x = 25 + 205*index
            svg.rect(x, top, 180, 66, '#f1f5f9', GREEN if index==4 else color, 2)
            svg.text(x+90, top+22, title, 15, anchor='middle', bold=True)
            svg.text(x+90, top+48, ids(values), 17, anchor='middle', color=GREEN if index==4 else INK)
            if index<4:
                svg.text(x+193, top+42, '→', 22, anchor='middle', color=MUTED)
        if run_index==2:
            svg.text(25, top+93, 'Після накладання нового порога попередні обмеження зберігаються.', 16, color=MUTED)
    svg.save(folder / 'selection-flow.svg')


if __name__ == '__main__':
    main()
