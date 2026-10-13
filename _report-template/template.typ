#import "profile.typ": student
#import "rules.typ": rules

// Уся верстка спільна для звітів. Зміст роботи сюди не додавати.
#let report(
  discipline: "Теорія прийняття рішень",
  teacher: "доцент Дуфанець Марта Василівна",
  department: "Кафедра оптоелектроніки та інформаційних технологій",
  lab-number: "[Номер]",
  topic: "[Тема лабораторної роботи]",
  variant: none,
  year: "2026",
  with-outline: false,
  body,
) = {
  set document(
    title: "Лабораторна робота № " + str(lab-number) + ". " + topic,
    author: student.name,
  )
  set text(
    font: rules.font,
    size: rules.font-size,
    lang: "uk",
    fill: black,
    top-edge: 0.8em,
    bottom-edge: -0.2em,
  )
  set page(
    paper: rules.paper,
    margin: rules.margins,
    numbering: rules.page-numbering,
    footer: context {
      // Титульна враховується як сторінка 1, але без видимого номера.
      if counter(page).get().first() > 1 {
        align(center, text(size: 12pt, counter(page).display(rules.page-numbering)))
      }
    },
  )
  set par(
    justify: true,
    leading: rules.line-leading,
    first-line-indent: (amount: rules.paragraph-indent, all: true),
    spacing: rules.paragraph-spacing,
  )
  set heading(numbering: rules.heading-numbering)
  show heading: it => block(above: 14pt, below: 7pt, sticky: true, {
    set par(first-line-indent: 0pt, justify: false)
    set text(size: rules.font-size, weight: "bold")
    it
  })
  set list(indent: 0pt, body-indent: 7mm, spacing: 4pt)
  set enum(indent: 0pt, body-indent: 7mm, spacing: 4pt)
  set math.equation(numbering: rules.equation-numbering)
  set figure(numbering: "1", supplement: [Рисунок])
  show figure.where(kind: table): set figure(supplement: [Таблиця])
  show figure.where(kind: table): set figure.caption(position: top)
  show figure.caption: set text(size: rules.caption-size)
  show figure.caption: set par(first-line-indent: 0pt, leading: 0.3em, justify: false)
  set figure.caption(separator: [ — ])
  show table: set text(size: rules.table-size)
  show table: set par(first-line-indent: 0pt, leading: 0.3em, justify: false)
  set table(inset: 5pt, stroke: 0.5pt, align: left + horizon)
  show raw: set text(font: rules.code-font, size: rules.code-size)
  set raw(theme: none)
  show raw.where(block: true): it => block(
    width: 100%,
    breakable: true,
    inset: 8pt,
    stroke: 0.5pt,
    above: 7pt,
    below: 7pt,
    {
      set par(first-line-indent: 0pt, justify: false, leading: 0.3em)
      it
    },
  )

  // Титульний аркуш. Гнучкі відступи утримують місто і рік унизу.
  {
    set par(first-line-indent: 0pt, justify: false, leading: 0.4em, spacing: 0pt)
    align(center)[
      #student.university

      #v(7pt)
      #student.faculty

      #if department != none {
        v(7pt)
        department
      }
    ]
    v(1fr)
    align(center)[
      #text(size: 18pt, weight: "bold")[ЗВІТ]

      #v(10pt)
      з лабораторної роботи № #lab-number

      #v(10pt)
      з дисципліни «#discipline»

      #v(10pt)
      #text(weight: "bold")[Тема: «#topic»]

      #if variant != none {
        v(7pt)
        [Варіант № #variant]
      }
    ]
    v(1fr)
    align(right, block(width: 80mm, align(right)[
      // Явні переноси залишають рядки в одному абзаці, де діє leading.
      #set par(leading: rules.line-leading, spacing: 0pt)
      Виконав:\
      студент групи #student.group\
      #student.name

      #v(14pt)
      Перевірила:\
      #teacher
    ]))
    v(1fr)
    align(center)[#student.city — #year]
  }
  pagebreak()

  if with-outline {
    outline(title: [Зміст], indent: auto)
    pagebreak()
  }
  body
}
