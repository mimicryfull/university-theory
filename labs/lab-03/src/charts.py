#!/usr/bin/env python3
"""Програмна генерація SVG графів і матриць бінарних відношень."""
import json
import math
from html import escape
from pathlib import Path


def start(width, height):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="white"/>',
            '<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="#2764bd"/></marker></defs>',
            '<g font-family="Literata,serif" fill="#17212b">']


def text(parts, x, y, value, size=18, anchor="middle", fill="#17212b"):
    parts.append(f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{fill}">{escape(str(value))}</text>')


def finish(parts, path):
    path.write_text("\n".join(parts + ['</g></svg>']) + "\n", encoding="utf-8")


def graph(matrix, labels, title, path, subtitle="", footer=""):
    parts = start(780, 650)
    text(parts, 390, 35, title, 23)
    text(parts, 390, 65, subtitle, 17)
    n = len(matrix)
    radius = 185 if n > 1 else 0
    positions = [(390 + radius * math.cos(-math.pi / 2 + 2 * math.pi * i / n),
                  370 + radius * math.sin(-math.pi / 2 + 2 * math.pi * i / n)) for i in range(n)]
    for i in range(n):
        x, y = positions[i]
        for j in range(n):
            if not matrix[i][j]:
                continue
            if i == j:
                parts.append(f'<path d="M{x-20} {y-21} C{x-95} {y-110}, {x+95} {y-110}, {x+20} {y-21}" fill="none" stroke="#2764bd" stroke-width="2.5" marker-end="url(#arrow)"/>')
            else:
                xx, yy = positions[j]
                distance = math.hypot(xx-x, yy-y)
                dx, dy = (xx-x)/distance, (yy-y)/distance
                ax, ay, bx, by = x+31*dx, y+31*dy, xx-34*dx, yy-34*dy
                if matrix[j][i]:
                    cx, cy = (ax+bx)/2 - dy*27, (ay+by)/2 + dx*27
                    d = f'M{ax} {ay} Q{cx} {cy} {bx} {by}'
                else:
                    d = f'M{ax} {ay} L{bx} {by}'
                parts.append(f'<path d="{d}" fill="none" stroke="#2764bd" stroke-width="2.5" marker-end="url(#arrow)"/>')
    for (x, y), label in zip(positions, labels):
        parts.append(f'<circle cx="{x}" cy="{y}" r="29" fill="#eef4fc" stroke="#2764bd" stroke-width="2"/>')
        text(parts, x, y+7, label, 21)
    text(parts, 390, 620, footer, 17)
    finish(parts, path)


def heatmaps(result, path):
    matrices = [("Початкове P", result["matrix"]),
                ("Транзитивне замикання", result["transitive_closure"]),
                ("Досяжність R", result["reachability"]),
                ("Взаємна досяжність D", result["mutual_reachability"])]
    n = len(result["matrix"])
    cell = min(54, 250/n)
    panel_height = 85 + n*cell
    parts = start(920, 70 + 2*panel_height)
    text(parts, 460, 33, "Матриці первісного та похідних відношень", 23)
    for index, (title, matrix) in enumerate(matrices):
        left, top = 85 + (index % 2)*460, 110 + (index // 2)*panel_height
        text(parts, left+n*cell/2, top-42, title, 19)
        for j in range(n):
            text(parts, left+(j+.5)*cell, top-12, f"x{j+1}", 16)
        for i, row in enumerate(matrix):
            text(parts, left-20, top+(i+.5)*cell+6, f"x{i+1}", 16)
            for j, value in enumerate(row):
                fill = '#2764bd' if value else '#eef3f9'
                parts.append(f'<rect x="{left+j*cell}" y="{top+i*cell}" width="{cell-2}" height="{cell-2}" fill="{fill}"/>')
                text(parts, left+(j+.5)*cell, top+(i+.5)*cell+6, value, 19, fill='white' if value else '#64748b')
    finish(parts, path)


def generate(result, folder):
    labels = [f"x{i+1}" for i in range(len(result["matrix"]))]
    graph(result["matrix"], labels, "Граф початкового бінарного відношення", folder/'initial-graph.svg',
          "Стрілка xi → xj відповідає одиниці pᵢⱼ",
          "Петлі відповідають одиницям на діагоналі; сині дуги — відношенню P.")
    labels = [f"A{i+1}" for i in range(len(result["classes"]))]
    legend = "; ".join(f"A{i+1} = {{{', '.join('x'+str(v) for v in group)}}}" for i, group in enumerate(result["classes"]))
    graph(result["quotient"], labels, "Граф факторизованого відношення", folder/'factor-graph.svg',
          legend, "Петля зберігається, якщо в класі є хоча б одна первісна дуга.")
    graph(result["condensation"], labels, "Конденсація без внутрішньокласових петель", folder/'condensation.svg',
          legend, "Після стягування компонент між різними класами циклів немає.")
    heatmaps(result, folder/'relation-matrices.svg')


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    folder = root/'figures'
    folder.mkdir(parents=True, exist_ok=True)
    generate(json.loads((root/'data/results.json').read_text(encoding='utf-8')), folder)
