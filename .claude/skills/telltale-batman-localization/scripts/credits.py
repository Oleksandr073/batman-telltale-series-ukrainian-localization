"""Localization credits: extra lines added to the end of a few game texts (both modes).

Each file in the credits folder belongs to one record (see TARGETS):
  about.txt -> record 658 of ui_menu_english.txt (About screen of the main menu)
  boot.txt  -> record 21 of boot_english.txt (copyright text on the boot screen)
The import (apply_translations.py --credits DIR) adds every line of the file after that record's original (or
translated) text. These records are the ONLY ones allowed to have more lines than the English: validate.py and
check_consistency.py (with the same --credits DIR) remove exactly these lines before their usual checks, and report
an error if they are missing or different. A missing file = nothing added to that record.

File format: plain UTF-8 text, one line = one line on screen; empty lines are kept (empty lines at the end are
ignored). A line must not start with "number) " - it would become a new record.
"""
import os

from landb_txt import HDR, read_raw, split_lines

# credits file -> (game file name, record id, what the player sees)
TARGETS = {
    'about.txt': ('ui_menu_english.txt', 658, 'About screen'),
    'boot.txt': ('boot_english.txt', 21, 'boot screen'),
}


def read_credits(folder):
    """-> {(game file name, record id): (label, lines)} for every non-empty credits file in folder."""
    if not folder:
        return {}
    if not os.path.isdir(folder):
        raise SystemExit(f'Credits folder not found: {folder}')
    unknown = sorted(f for f in os.listdir(folder) if f not in TARGETS)
    if unknown:
        raise SystemExit(f'{folder}: unknown file(s) {unknown} - allowed: {sorted(TARGETS)} (see credits.py)')
    out = {}
    for name, (game_file, rec_id, label) in TARGETS.items():
        path = os.path.join(folder, name)
        if not os.path.exists(path):
            continue
        lines = split_lines(read_raw(path))[0]
        while lines and lines[-1].strip() == '':
            lines.pop()
        bad = [line for line in lines if HDR.match(line)]
        if bad:
            raise SystemExit(f'{path}: a line must not start with "number) " (the game would read it as a new '
                             f'record): {bad[0]!r}')
        if lines:
            out[(game_file, rec_id)] = (f'{label} ({name})', lines)
    return out


def credit_for(rel, rec_id, credits):
    """-> (label, lines) if this record gets credit lines, else None."""
    return credits.get((os.path.basename(rel), rec_id)) if credits else None


def strip_credits(rel, lines, credits):
    """Remove the credit lines the import added to this file. -> (lines, [error messages]).
    Files without credits are returned unchanged."""
    errors = []
    for (game_file, rec_id), (label, extra) in (credits or {}).items():
        if os.path.basename(rel) != game_file:
            continue
        heads = [i for i, line in enumerate(lines) if HDR.match(line)]
        start = next((i for i in heads if int(HDR.match(lines[i]).group(1)) == rec_id), None)
        if start is None:
            errors.append(f'record {rec_id} ({label}) not found')
            continue
        end = next((i for i in heads if i > start), len(lines))
        n = len(extra)
        if end - start - 1 < n or lines[end - n:end] != extra:
            errors.append(f'record {rec_id} ({label}) does not end with the {n} credit line(s) - run the import again')
            continue
        lines = lines[:end - n] + lines[end:]
    return lines, errors
