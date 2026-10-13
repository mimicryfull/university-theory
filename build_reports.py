"""Зібрати PDF зі звітів Typst; не виконує тестів чи перегляду сторінок."""

import argparse
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--typst", default=shutil.which("typst"),
                        help="Шлях до компілятора Typst, якщо він не в PATH")
    args = parser.parse_args()
    if not args.typst:
        parser.error("Встановіть Typst або задайте шлях через --typst.")
    for number in range(4, 11):
        folder = ROOT / f"lab-{number:02d}"
        subprocess.run([
            args.typst, "compile", "--root", str(ROOT),
            str(folder / "report.typ"), str(folder / "report.pdf"),
        ], cwd=ROOT, check=True)
        print(f"Зібрано lab-{number:02d}/report.pdf", flush=True)


if __name__ == "__main__":
    main()
