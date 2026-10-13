"""Виконати лабораторні 1–10 та зберегти результати (без тестів)."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
JOBS = [
    (1, ["--student-number", "1"]),
    (2, ["--variant", "1"]),
    (3, ["--student-number", "1"]),
    (4, ["--student-number", "1", "--seed", "20260401"]),
    (5, []),
    (6, ["--student-number", "1", "--seed", "20260506"]),
    (7, ["--student-number", "1"]),
    (8, ["--student-number", "1"]),
    (9, []),
    (10, ["--variant", "1"]),
]


def main() -> None:
    for number, options in JOBS:
        print(f"\nЛабораторна {number}", flush=True)
        script = ROOT / "labs" / f"lab-{number:02d}" / "src" / "main.py"
        subprocess.run([sys.executable, str(script), *options],
                       cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
