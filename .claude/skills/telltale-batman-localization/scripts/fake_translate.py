"""Fill the table with a FAKE Ukrainian translation, for testing the game build: every English letter is swapped
for a Cyrillic one (Good night -> Гюд ніґт), using all 33 Ukrainian letters to test the game font; tags, ¶ and punctuation are kept. End credits stay English (as planned for
the real translation).

Usage:
  python fake_translate.py TABLE [--force]

Stops if the table already has a real (not fake) translation, unless --force is given. Use it on a test branch,
then run the import (npm run import) to write the game files.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import selftest as T  # noqa: E402
from tm_lib import save_stable  # noqa: E402


def main():
    args = [a for a in sys.argv[1:] if a != '--force']
    if len(args) != 1:
        sys.exit(__doc__)
    path = args[0]
    wb, ws, col = T.load_sheet(path)
    rows = [r for r in T.table_rows(ws, col) if r['kind'] == 'text']
    plan, real, credits = {}, [], 0
    for r in rows:
        if 'ui_credits' in str(r['first_seen'] or ''):
            credits += 1
            continue
        cell = T.fake(r['english'])
        old = str(r['ukrainian'] or '')
        if old and old != cell:
            real.append(r['row'])
        plan[r['row']] = cell
    if real and '--force' not in sys.argv:
        sys.exit(f'STOP: {len(real)} row(s) already have a real translation (e.g. rows {real[:5]}). '
                 f'This would overwrite them. Use a test branch, or add --force.')
    for n, cell in plan.items():
        ws.cell(row=n, column=col['ukrainian']).value = cell
    try:
        save_stable(wb, path)
    except PermissionError:
        sys.exit(f'Cannot write {path} - close it in Excel / LibreOffice first.')
    print(f'Fake translation written into {len(plan)} row(s) of {path} '
          f'({credits} end-credit rows left English). Now run: npm run import')


if __name__ == '__main__':
    main()
