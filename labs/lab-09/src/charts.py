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


def bars(svg, labels, values, top, title, chosen=None):
    left, length, rowh = 320, 455, 45
    svg.text(30, top-15, title, 21, bold=True)
    for tick in range(5):
        value = tick*.1
        x = left + length*value/.4
        svg.line(x, top, x, top+rowh*len(values))
        svg.text(x, top+rowh*len(values)+22, f'{value:.1f}', 14, anchor='middle')
    for i, (label, value) in enumerate(zip(labels, values)):
        y = top + i*rowh
        svg.text(left-15, y+27, label, 16, anchor='end')
        svg.rect(left, y+7, length*value/.4, 28, GREEN if i==chosen else BLUE)
        svg.text(left+length*value/.4+9, y+27, f'{value:.4f}', 16, bold=i==chosen)


def generate(result, folder):
    svg = SVG(900, 650)
    bars(svg, result['criteria'], result['criteria_result']['weights'], 65, 'Ваги критеріїв (сума = 1)')
    rows = result['ranking']
    bars(svg, [r['alternative'] for r in rows], [r['weight'] for r in rows], 380,
         'Глобальні пріоритети: альтернативи впорядковано за спаданням', chosen=0)
    svg.save(folder / 'priorities.svg')

    matrices = [result['criteria_result']] + result['local_results']
    labels = ['Критерії'] + [f'Q{i+1}: {x["criterion"]}' for i,x in enumerate(result['local_results'])]
    svg = SVG(940, 430)
    svg.text(30, 35, 'Узгодженість матриць попарних порівнянь', 23, bold=True)
    left, length, top, rowh, limit = 355, 480, 85, 45, .12
    for tick in range(7):
        value = tick*.02
        x = left+length*value/limit
        svg.line(x, top, x, top+rowh*len(matrices))
        svg.text(x, top+rowh*len(matrices)+24, f'{value:.2f}', 14, anchor='middle')
    for i,(label,matrix) in enumerate(zip(labels,matrices)):
        y=top+i*rowh
        svg.text(left-15,y+26,label,16,anchor='end')
        svg.rect(left,y+7,max(2,length*matrix['cr']/limit),27,GREEN if matrix['cr']<=.1 else RED)
        svg.text(left+length*matrix['cr']/limit+10,y+26,f'{matrix["cr"]:.5f}',15)
    x=left+length*.1/limit
    svg.line(x,top-5,x,top+rowh*len(matrices),RED,2,True)
    svg.text(x,top-17,'Поріг CR = 0,10',16,RED,anchor='middle')
    svg.text(30,410,f'CR ієрархії = {result["global_cr"]:.6f}; зелені стовпчики — прийнятна узгодженість.',16)
    svg.save(folder / 'consistency.svg')


if __name__ == '__main__':
    main()
