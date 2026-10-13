# Лабораторна робота 6 — лінійна та максимінна згортка

Номер студента в журналі **N=1**; за методичкою використовуються 4 альтернативи
і 5 критеріїв, усі спрямовані на максимізацію. Python 3, без сторонніх бібліотек.

```bash
cd /home/katanix/Documents/LNU/Theory/labs/lab-06
uv run python src/main.py --student-number 1 --seed 20260506 --output data/results.json
typst compile report/report.typ report/report.pdf --root ../.. --font-path ../../fonts
```

Фіксоване зерно забезпечує відтворюваний навчальний набір. `data/results.json` містить
вхідні дані, обидві нормовані матриці, усі оцінки і повні списки переможців.
Він також придатний як вхідний файл для повторного обчислення з іншими вагами:

```bash
uv run python src/main.py --student-number 1 --input data/results.json --output data/revised-results.json
```

У JSON потрібні поля `student_number`, `alternatives`, `matrix`, `norms`, `weights`.
Оцінки та нормативи — цілі від 1 до 3+N, п'ять ваг додатні з сумою 1.
В усіх згортках повертаються всі альтернативи, що досягають максимуму.

Програма розділяє min-max нормування за формулою теоретичної частини методички
і ділення на норматив за формулою (1). Друге не гарантує інтервал [0,1].
Нормативний максимін без ваг відтворює приклад 3; додатково обчислюються
вагові нормативні згортки. Min-max використовує задані межі шкали [1,3+N].

`src/charts.py` створює `figures/normalized-criteria.svg`, `figures/raw-convolutions.svg`,
`figures/normative-convolutions.svg` та `figures/normalized-convolutions.svg`;
викликається автоматично з `src/main.py`. Для регенерації лише рисунків із JSON:

```bash
uv run python src/charts.py
```

Графіки згорток мають окремі панелі з власними шкалами; висоти між панелями
не інтерпретуються як порівняння числових величин різних методів.

## Організація

`src/` містить Python-код; `data/` — вхідні дані й числові результати; `figures/` — SVG; `report/` — Typst і PDF. Команди для цієї роботи виконувати з її кореневої папки. Значення `--figures-dir` можна задати окремо; типово рисунки потрапляють у `figures/`, а числові результати — у `data/`.
