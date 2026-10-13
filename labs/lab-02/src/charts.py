#!/usr/bin/env python3
"""Три SVG рисунки для бінарних відношень; стандартна бібліотека."""
import json
from html import escape
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parent.parent
BLUE, GREEN, INK, MUTED = '#2764bd', '#177245', '#17212b', '#64748b'


class SVG:
    def __init__(self, width, height):
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="white"/>', '<g font-family="Liberation Sans, sans-serif" fill="#17212b">']

    def text(self, x, y, value, size=18, color=INK, anchor='start', bold=False):
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{"bold" if bold else "normal"}">{escape(str(value))}</text>')

    def rect(self, x, y, width, height, color):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{color}"/>')

    def line(self, x1, y1, x2, y2, color='#e4e8ed'):
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}"/>')

    def save(self, path):
        path.write_text('\n'.join(self.parts+['</g></svg>']), encoding='utf-8')


def matrix_panel(svg, relation, names, x, y, step=62):
    size = len(names)
    svg.text(x-40, y-57, relation['title'], 23, bold=True)
    for i,name in enumerate(names):
        label=name[0].upper()
        svg.text(x+(i+.5)*step, y-15, label, 21, anchor='middle', bold=True)
        svg.text(x-22, y+(i+.5)*step+7, label, 21, anchor='end', bold=True)
    for i,row in enumerate(relation['matrix']):
        for j,value in enumerate(row):
            svg.rect(x+j*step,y+i*step,step-3,step-3,BLUE if value else '#eef2f7')
            svg.text(x+(j+.5)*step,y+(i+.5)*step+8,value,24,anchor='middle',color='white' if value else MUTED)
    svg.text(x,y+size*step+29,f'Кількість пар: {relation["count"]}',17)


def generate_charts(data, folder):
    names = data['names']
    relations = data['relations']
    size = len(names)
    panel_width = max(420, size*62+150)
    height = size*62+210
    svg=SVG(panel_width*2,height)
    svg.text(28,32,'Матриці P і Q: рядок — перший елемент, стовпець — другий',22,bold=True)
    for index,key in enumerate(('P','Q')):
        matrix_panel(svg,relations[key],names,85+index*panel_width,115)
    svg.text(28,height-23,'Позначення: '+ '; '.join(name[0].upper()+' — '+name for name in names)+'. Синій = 1; світлий = 0.',17)
    svg.save(folder/'initial-relations.svg')
    keys=['intersection','union','difference','symmetric_difference','complement_p','inverse_p','composition','reverse_difference','complement_q','reverse_composition','square_p']
    columns=3
    cellwidth=max(330, size*48+115)
    cellheight=size*48+110
    rows=(len(keys)+columns-1)//columns
    svg=SVG(cellwidth*columns,rows*cellheight+85)
    svg.text(25,32,'Результати операцій над P та Q',24,bold=True)
    for index,key in enumerate(keys):
        matrix_panel(svg,relations[key],names,75+(index%columns)*cellwidth,115+(index//columns)*cellheight,48)
    svg.save(folder/'operation-matrices.svg')
    svg=SVG(930,90+len(relations)*45)
    svg.text(25,32,'Кількість впорядкованих пар',24,bold=True)
    left,top,length=280,70,530
    maxcount=size*size
    for tick in range(5):
        value=maxcount*tick/4
        x=left+length*tick/4
        svg.line(x,top,x,top+len(relations)*45)
        svg.text(x,top-13,f'{value:g}',16,anchor='middle')
    for index,(key,relation) in enumerate(relations.items()):
        y=top+index*45
        svg.text(left-15,y+25,relation['title'],19,anchor='end')
        width=length*relation['count']/maxcount
        svg.rect(left,y+5,width,28,GREEN if key=='Q' else BLUE)
        svg.text(left+width+10,y+25,relation['count'],19,bold=True)
    svg.save(folder/'relation-counts.svg')


if __name__ == '__main__':
    figures=LAB_ROOT/'figures'
    figures.mkdir(parents=True,exist_ok=True)
    generate_charts(json.loads((LAB_ROOT/'data/results.json').read_text(encoding='utf-8')),figures)
