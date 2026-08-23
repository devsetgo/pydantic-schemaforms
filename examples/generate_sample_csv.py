#!/usr/bin/env python3
"""Generate deterministic sample CSV files for the DataTableLayout import demo
(see datatable_import_example.py).

Run: python examples/generate_sample_csv.py
Writes examples/sample_data/employees_{10,100,1000,10000}.csv, for exercising
the file-input -> table -> DataTables pipeline at different scales. Every
file's first three rows (by DataTables' default Name-ascending sort) are the
same fixed, deterministic set: one valid row, one with a bad email, and one
with an invalid department -- see FIXED_ROWS -- so every generated sample
reliably demonstrates the per-row validation-error highlighting; the rest
are random but always valid.
"""

import csv
import random
from pathlib import Path

FIRST_NAMES = [
    'Alice', 'Bob', 'Carol', 'Dave', 'Eve', 'Frank', 'Grace', 'Heidi',
    'Ivan', 'Judy', 'Kevin', 'Laura', 'Mallory', 'Niaj', 'Olivia', 'Peggy',
    'Quentin', 'Ruth', 'Sybil', 'Trent', 'Uma', 'Victor', 'Wendy', 'Xavier',
    'Yolanda', 'Zach', 'Amir', 'Bianca', 'Carlos', 'Diana',
]  # fmt: skip
LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
    'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
    'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
    'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark',
    'Ramirez', 'Lewis', 'Robinson',
]  # fmt: skip
DEPARTMENTS = ['engineering', 'sales', 'support']
TEAM_PROJECTS = [
    ('Platform Team', 'Rebuild the customer portal'),
    ('Growth Team', 'Expand into new markets'),
    ('Data Team', 'Build the analytics pipeline'),
    ('Mobile Team', 'Ship the new mobile app'),
]

# Deterministically the first 3 rows once DataTables' default sort (ascending
# by Name, the first column) is applied -- "Aaron A..." sorts before every
# combination FIRST_NAMES/LAST_NAMES can produce (comparing character by
# character, 'a' < 'l'/'m', the earliest letters among FIRST_NAMES's 'Alice'/
# 'Amir'), and the three sort Aaronson < Abbott < Adams among themselves. Row
# 1 is valid (so the table looks normal at a glance); rows 2 and 3 are
# intentionally invalid (bad email, bad enum) so every generated sample
# reliably demonstrates the per-row validation-error highlighting -- without
# a real database to seed, this is the deterministic stand-in.
FIXED_ROWS: list[dict[str, str]] = [
    {
        'name': 'Aaron Aaronson',
        'email': 'aaron.aaronson@example.com',
        'department': 'engineering',
        'project_team_name': 'Platform Team',
        'project_description': 'Rebuild the customer portal',
    },
    {
        'name': 'Aaron Abbott',
        'email': 'not-an-email',  # intentionally invalid -- demonstrates a bad-email row error
        'department': 'sales',
        'project_team_name': 'Growth Team',
        'project_description': 'Expand into new markets',
    },
    {
        'name': 'Aaron Adams',
        'email': 'aaron.adams@example.com',
        'department': 'unknown',  # intentionally invalid -- demonstrates a bad-enum row error
        'project_team_name': 'Data Team',
        'project_description': 'Build the analytics pipeline',
    },
]

SIZES = [10, 100, 1000, 10000]
SEED = 42

OUTPUT_DIR = Path(__file__).resolve().parent / 'sample_data'


def generate_rows(count: int, *, seed: int = SEED) -> list[dict[str, str]]:
    rng = random.Random(seed)
    rows = list(FIXED_ROWS[: min(len(FIXED_ROWS), count)])
    for i in range(max(0, count - len(rows))):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        team_name, project_description = rng.choice(TEAM_PROJECTS)
        rows.append(
            {
                'name': f'{first} {last}',
                # index suffix keeps emails unique even when name combos repeat
                'email': f'{first.lower()}.{last.lower()}{i}@example.com',
                'department': rng.choice(DEPARTMENTS),
                'project_team_name': team_name,
                'project_description': project_description,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                'name',
                'email',
                'department',
                'project_team_name',
                'project_description',
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    for size in SIZES:
        path = OUTPUT_DIR / f'employees_{size}.csv'
        write_csv(path, generate_rows(size))
        print(f'Wrote {path} ({size} rows)')


if __name__ == '__main__':
    main()
