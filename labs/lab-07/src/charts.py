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
    svg = SVG(900, 710)
    svg.text(35, 35, 'Лінійна згортка та відстань до ідеальної точки', 22, bold=True)
    for panel, (key, title, optimum, winners, color) in enumerate([
        ('score', 'Згортка S = 0,3Q1 + 0,7Q2 → максимум', result['best_score'], result['linear_ids'], BLUE),
        ('distance', 'Евклідова відстань d до Q* → мінімум', result['best_distance'], result['ideal_ids'], ORANGE),
    ]):
        left, top, plotw, ploth = 75, 90 + panel * 325, 760, 225
        low = min(0, min(row[key] for row in rows))
        high = max(0, max(row[key] for row in rows))
        if high == low:
            high = low + 1
        def y(value):
            return top + ploth - (value-low) / (high-low) * ploth
        svg.text(left, top-23, title, 18, color=color, bold=True)
        for i in range(5):
            value = low + (high-low) * i / 4
            yy = y(value)
            svg.line(left, yy, left+plotw, yy)
            svg.text(left-10, yy+5, f'{value:.2f}', 14, anchor='end')
        svg.line(left, y(0), left+plotw, y(0), MUTED, 1.5)
        for i, row in enumerate(rows):
            center = left + plotw * (i+.5) / len(rows)
            value = row[key]
            yy = y(value)
            chosen = row['id'] in winners
            svg.rect(center-20, min(yy, y(0)), 40, max(abs(yy-y(0)), 1), GREEN if chosen else color)
            svg.text(center, yy-8 if value>=0 else yy+19, f'{value:.2f}', 14, anchor='middle', bold=chosen)
            svg.text(center, top+ploth+24, f'A{row["id"]}', 15, anchor='middle', color=GREEN if chosen else INK, bold=chosen)
        svg.text(left, top+ploth+52, f'Оптимум: {ids(winners)}; значення {optimum:.4f}. Зеленим позначено вибір.', 15, color=GREEN)
    svg.save(folder / 'methods.svg')


if __name__ == '__main__':
    main()
