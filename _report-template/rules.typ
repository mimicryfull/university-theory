// Базові параметри шаблону, а не підтверджені загальні вимоги ЛНУ.
// Пояснення та правила підготовки звітів — у RULES.md.
#let rules = (
  paper: "a4",
  margins: (left: 30mm, right: 15mm, top: 20mm, bottom: 20mm),
  // Шрифт, обраний користувачем і встановлений локально.
  font: "Literata",
  font-size: 14pt,
  // Висота звичайного рядка 14pt + проміжок 7pt = крок 21pt.
  line-leading: 0.5em,
  paragraph-indent: 12.5mm,
  // Зберігає крок 21pt також на межі сусідніх абзаців.
  paragraph-spacing: 0.5em,
  heading-numbering: "1.1",
  page-numbering: "1",
  equation-numbering: "(1)",
  code-font: "Liberation Mono",
  code-size: 10pt,
  table-size: 12pt,
  caption-size: 12pt,
)
