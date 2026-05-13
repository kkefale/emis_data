"""
setup.py
--------
One-time setup script: converts emis.csv → emis.db (SQLite).

Usage:
    python setup.py

The CSV uses semicolons as delimiters and European-style decimal commas.
This script imports it verbatim into a table called `emis` so the dashboard
can query it via optimised SQL.
"""

import csv
import sqlite3
import sys
from pathlib import Path

ROOT    = Path(__file__).parent
CSV_PATH = ROOT / "emis.csv"
DB_PATH  = ROOT / "emis.db"


def main() -> None:
    if not CSV_PATH.exists():
        print(
            f"[ERROR] '{CSV_PATH.name}' not found.\n"
            "Download the SA EMIS dataset and place it in this directory."
        )
        sys.exit(1)

    if DB_PATH.exists():
        print(f"[INFO ] '{DB_PATH.name}' already exists — skipping rebuild.")
        print("        Delete 'emis.db' and re-run if you want to force a refresh.")
        return

    print(f"[INFO ] Reading '{CSV_PATH.name}' …")
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh, delimiter=";")
        headers = next(reader)
        rows    = list(reader)

    print(f"[INFO ] {len(rows):,} rows · {len(headers)} columns")

    print(f"[INFO ] Building '{DB_PATH.name}' …")
    ph = ", ".join("?" * len(headers))
    cols = ", ".join(f'"{h}"' for h in headers)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute(f'DROP TABLE IF EXISTS emis')
        conn.execute(f'CREATE TABLE emis ({cols})')
        conn.executemany(f'INSERT INTO emis VALUES ({ph})', rows)
        # Useful indexes for the dashboard queries
        conn.execute("CREATE INDEX IF NOT EXISTS idx_province ON emis(Province)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_district ON emis(EIDistrict)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_quintile ON emis(Quintile)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_status   ON emis(Status)")
        conn.commit()

    size_mb = DB_PATH.stat().st_size / 1_048_576
    print(f"[OK   ] emis.db created ({size_mb:.1f} MB) — ready to launch the dashboard.")


if __name__ == "__main__":
    main()
