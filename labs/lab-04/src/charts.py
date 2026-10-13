"""Векторні графіки зі збережених даних; лише стандартна бібліотека."""
import html
import json
import math
import statistics
from pathlib import Path

COLORS = ['#2563eb', '#d97706', '#059669', '#7c3aed', '#e11d48']


def text(x, y, value, anchor='start', size=23, fill='#172033'):
    return (f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" '
            f'font-size="{size}" fill="{fill}">{html.escape(str(value))}</text>')


def line(x1, y1, x2, y2, color='#cbd5e1', width=1, dashed=False):
    dash = ' stroke-dasharray="9 7"' if dashed else ''
    return f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{width}"{dash}/>'


def save(path, pieces, width=1100, height=600):
    content = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
               '<rect width="100%" height="100%" fill="white"/>',
               '<g font-family="Literata, DejaVu Sans, serif" fill="#172033">']
    content.extend(pieces)
    content.append('</g></svg>')
    path.write_text('\n'.join(content), encoding='utf-8')


def bars(labels, series, title, y_label, y_min=0, y_max=None, median=None, height=520, offset=0):
    """Одна вісь лише для величин із явно спільною шкалою."""
    left, right, top, bottom = 100, 42, 95+offset, 105
    h = height-top+offset-bottom
    w = 1100-left-right
    ceiling = y_max if y_max is not None else max(max(values) for _, values in series)*1.18
    ceiling = max(ceiling, y_min+1e-9)
    yy = lambda value: top+h*(ceiling-value)/(ceiling-y_min)
    out = [text(550, offset+35, title, 'middle', 27), text(100, offset+71, y_label, size=21)]
    for t in range(6):
        value=y_min+(ceiling-y_min)*t/5
        y=yy(value)
        out.extend([line(left,y,1100-right,y), text(left-13,y+7,f'{value:.3g}','end',21)])
    out.append(line(left, yy(0), 1100-right, yy(0), '#475569', 2))
    spacing=w/len(labels)
    bar_width=min(62,spacing*.68/len(series))
    for i,label in enumerate(labels):
        center=left+spacing*(i+.5)
        out.append(text(center, top+h+34,label,'middle',23))
        for j, (_,values) in enumerate(series):
            value=values[i]
            x=center+(j-len(series)/2)*bar_width
            y=min(yy(value),yy(0)); bh=abs(yy(value)-yy(0))
            out.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width*.86:.2f}" height="{bh:.2f}" fill="{COLORS[j]}"/>')
            if bh < 1:
                out.append(line(x,yy(0),x+bar_width*.86,yy(0),COLORS[j],4))
            out.append(text(x+bar_width*.43, y-9 if value>=0 else y+bh+25,f'{value:.3f}','middle',19, COLORS[j]))
    if median is not None:
        out.append(line(left,yy(median),1100-right,yy(median),'#e11d48',3,True))
        out.append(text(1100-right,yy(median)-12,f'Медіана = {median:g}','end',21,'#e11d48'))
    for j,(name, _) in enumerate(series):
        x=left+j*310
        out.append(f'<rect x="{x}" y="{offset+height-34}" width="19" height="19" fill="{COLORS[j]}"/>')
        out.append(text(x+29,offset+height-17,name,size=20))
    return out


def heatmap(path, rows, row_labels, col_labels, title, legend, ceiling=1):
    left,top,cw,ch=180,100,150,70
    width=left+cw*len(col_labels)+100
    height=top+ch*len(rows)+120
    out=[text(width/2,38,title,'middle',27)]
    for j,label in enumerate(col_labels):
        out.append(text(left+cw*(j+.5),top-20,label,'middle',24))
    for i,row in enumerate(rows):
        out.append(text(left-20,top+ch*(i+.5)+8,row_labels[i],'end',24))
        for j,v in enumerate(row):
            ratio=max(0,min(1,v/ceiling))
            rgb=tuple(round(a+(b-a)*ratio) for a,b in zip((239,246,255),(29,78,216)))
            color='#%02x%02x%02x'%rgb
            out.append(f'<rect x="{left+j*cw}" y="{top+i*ch}" width="{cw}" height="{ch}" fill="{color}" stroke="white" stroke-width="3"/>')
            out.append(text(left+cw*(j+.5),top+ch*(i+.5)+8,f'{v:.3f}','middle',23,'white' if ratio>.58 else '#172033'))
    for j in range(11):
        r=j/10;rgb=tuple(round(a+(b-a)*r) for a,b in zip((239,246,255),(29,78,216)))
        out.append(f'<rect x="{left+j*30}" y="{height-75}" width="30" height="18" fill="#%02x%02x%02x"/>'%rgb)
    out.extend([text(left,height-35,'0',size=20),text(left+330,height-35,f'{ceiling:g}','end',20),text(left+370,height-58,legend,size=20)])
    save(path,out,width,height)


def generate_charts(data, folder):
    folder=Path(folder)
    frequencies=data['frequencies']; size=data['size']; maximum=data['maximum']
    left,top,w,h=100,80,920,350
    xx=lambda x:left+w*x/(maximum+1)
    yy=lambda p:top+h*(1-p)
    out=[text(550,35,'Емпірична функція розподілу Fₙ(x)','middle',27),text(100,65,'Накопичена частка спостережень',size=21)]
    for t in range(6):
        p=t/5;y=yy(p)
        out.extend([line(left,y,left+w,y),text(left-15,y+7,f'{p:.1f}','end',21)])
    for x in range(maximum+2):
        out.append(text(xx(x),top+h+35,x,'middle',23))
    previous=0; previous_x=0
    for row in frequencies:
        x=row['value']; new=previous+row['count']/size
        out.append(line(xx(previous_x),yy(previous),xx(x),yy(previous),COLORS[0],4))
        out.append(line(xx(x),yy(previous),xx(x),yy(new),COLORS[0],2,True))
        out.append(f'<circle cx="{xx(x):.2f}" cy="{yy(previous):.2f}" r="5" stroke="{COLORS[0]}" fill="white" stroke-width="2"/>')
        out.append(f'<circle cx="{xx(x):.2f}" cy="{yy(new):.2f}" r="5" fill="{COLORS[0]}"/>')
        out.append(text(xx(x)+13,yy(new)-12,f'{new:.4f}',size=21))
        previous,previous_x=new,x
    out.append(line(xx(previous_x),yy(previous),xx(maximum+1),yy(previous),COLORS[0],4))
    out.extend([text(550,490,'Значення x','middle'),text(100,545,'● значення в точці стрибка; ○ ліва межа; Fₙ(x) = частка значень ≤ x',size=21)])
    save(folder/'empirical-cdf.svg',out,height=580)
    means=data['means'];labels=['H: гармонічне','G: геометричне','A: арифметичне','RMS: квадратичне']
    values=[means[k] for k in ('harmonic','geometric','arithmetic','quadratic')]
    out=bars(labels,[('Середні величини',values)],'Різне зважування тієї самої вибірки','Значення показника',y_max=maximum,median=means['median'])
    out.append(text(100,575,'Мода окремо: '+', '.join(map(str,means['modes']))+f'; найбільша частота = {means["mode_frequency"]} із {size}.',size=23))
    save(folder/'means-comparison.svg',out,height=610)
    ordered=data['sorted_sample']
    q1,q2,q3=statistics.quantiles(ordered,n=4,method='inclusive')
    iqr=q3-q1; lo=q1-1.5*iqr; hi=q3+1.5*iqr
    inside=[v for v in ordered if lo<=v<=hi]
    low,high=min(inside),max(inside)
    x=lambda v:120+860*(v-1)/max(1,maximum-1)
    out=[text(550,38,'Розмах, квартилі та медіана вибірки','middle',27)]
    out.extend([line(x(low),220,x(high),220,'#475569',4),line(x(low),185,x(low),255,'#475569',4),line(x(high),185,x(high),255,'#475569',4)])
    out.append(f'<rect x="{x(q1):.2f}" y="160" width="{x(q3)-x(q1):.2f}" height="120" fill="#dbeafe" stroke="{COLORS[0]}" stroke-width="3"/>')
    out.append(line(x(q2),160,x(q2),280,'#e11d48',5))
    for value,label,y in [(low,'мінімум',120),(q1,'Q₁',315),(q2,'медіана',120),(q3,'Q₃',315),(high,'максимум',120)]:
        out.append(text(x(value),y,f'{label} = {value:g}','middle',22))
    for v in sorted(set(ordered)):
        if v<lo or v>hi:
            out.append(f'<circle cx="{x(v):.2f}" cy="220" r="6" fill="#d97706"/>')
    out.extend([text(100,395,f'IQR = {iqr:g}; межі 1,5·IQR: [{lo:g}; {hi:g}].',size=23),text(100,445,'Квартилі: лінійна інтерполяція за позицією (n−1)·p, method="inclusive".',size=21),text(100,490,'Вуса — крайні спостереження в межах 1,5·IQR; точки — значення поза ними.',size=21)])
    save(folder/'sample-boxplot.svg',out,height=530)


if __name__ == '__main__':
    lab_root = Path(__file__).resolve().parent.parent
    figures = lab_root / 'figures'
    figures.mkdir(parents=True, exist_ok=True)
    result = json.loads((lab_root / 'data' / 'results.json').read_text(encoding='utf-8'))
    generate_charts(result, figures)
