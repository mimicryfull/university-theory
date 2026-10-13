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


def payoff_color(value, bound):
    t = abs(value)/bound if bound else 0
    dark = (23,114,69) if value>=0 else (39,100,189)
    return '#' + ''.join(f'{round(245+(b-245)*t):02x}' for b in dark)


def generate(result, folder):
    for index, game in enumerate(result['games'], 1):
        matrix = game['matrix']
        rows, cols = len(matrix), len(matrix[0])
        svg=SVG(960, 370+max(rows,cols)*52)
        svg.text(25,35,game['name'],22,bold=True)
        svg.text(25,62,'Платежі першому гравцеві: рядки — його стратегії, стовпці — стратегії другого.',16)
        left, top, cw, ch = 120, 110, 105, 64
        saddle={(p['row']-1,p['column']-1) for p in game['saddle_points']}
        bound=max(abs(v) for row in matrix for v in row)
        for j in range(cols):
            svg.text(left+(j+.5)*cw,top-15,f'B{j+1}',19,anchor='middle',bold=True)
        svg.text(left+(cols+.65)*cw,top-15,'min рядка',17,anchor='middle')
        for i,row in enumerate(matrix):
            svg.text(left-20,top+i*ch+40,f'A{i+1}',19,anchor='end',bold=True)
            for j,value in enumerate(row):
                svg.rect(left+j*cw,top+i*ch,cw-3,ch-3,payoff_color(value,bound),ORANGE if (i,j) in saddle else 'white',5 if (i,j) in saddle else 1)
                svg.text(left+(j+.5)*cw,top+i*ch+40,f'{value:g}',23,anchor='middle',color='white' if abs(value)>bound*.6 else INK,bold=True)
            value=game['row_minima'][i]
            svg.text(left+(cols+.65)*cw,top+i*ch+40,f'{value:g}',21,anchor='middle',color=GREEN if value==game['lower_value'] else MUTED,bold=value==game['lower_value'])
        svg.text(left-20,top+rows*ch+38,'max стовпця',16,anchor='end')
        for j,value in enumerate(game['column_maxima']):
            svg.text(left+(j+.5)*cw,top+rows*ch+38,f'{value:g}',21,anchor='middle',color=GREEN if value==game['upper_value'] else MUTED,bold=value==game['upper_value'])
        yy=top+rows*ch+85
        svg.text(25,yy,f'α = {game["lower_value"]:g}; β = {game["upper_value"]:g}; '+ ('є чиста рівновага' if game['pure_equilibrium'] else 'чистої рівноваги немає'),21,bold=True)
        svg.text(25,yy+29,'Помаранчева рамка — сідлова точка; зелений текст — оптимальна гранична оцінка.',15,color=MUTED)
        for i in range(max(rows,cols)):
            if i<rows:
                svg.text(25,yy+63+i*27,f'A{i+1}: {game["row_strategies"][i]}',15)
            if i<cols:
                svg.text(485,yy+63+i*27,f'B{i+1}: {game["column_strategies"][i]}',15)
        svg.save(folder / f'payoff-{index}.svg')


if __name__ == '__main__':
    main()
