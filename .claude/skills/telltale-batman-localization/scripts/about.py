"""Extra lines for the About screen of the main menu (localization credits).

The About screen shows record 658 of ui_menu_english.txt (both modes: BM_pc_Menu_data and
BAT_pc_PC_Noir_Menu_compressed). The import (apply_translations.py --about FILE) appends every line of FILE to the
end of that record, after the original (or translated) text. This is the ONLY record allowed to have more lines
than the English one: validate.py and check_consistency.py (with the same --about FILE) remove exactly these lines
before their usual checks, and report an error if they are missing or different.

FILE: plain UTF-8 text, one line = one line on screen; empty lines are kept (empty lines at the end are ignored).
A line must not start with "number) " - it would become a new record.
"""
import os

from landb_txt import HDR, read_raw, split_lines

ABOUT_FILE = 'ui_menu_english.txt'
ABOUT_ID = 658


def read_about(path):
    """-> list of lines to append, or None if no file / empty file."""
    if not path:
        return None
    if not os.path.exists(path):
        raise SystemExit(f'About file not found: {path}')
    lines = split_lines(read_raw(path))[0]
    while lines and lines[-1].strip() == '':
        lines.pop()
    bad = [line for line in lines if HDR.match(line)]
    if bad:
        raise SystemExit(f'{path}: a line must not start with "number) " (the game would read it as a new record): '
                         f'{bad[0]!r}')
    return lines or None


def is_about(rel, rec_id):
    return os.path.basename(rel) == ABOUT_FILE and rec_id == ABOUT_ID


def strip_about(rel, lines, about):
    """Remove the About lines appended to record 658. -> (lines, error message or None).
    Files other than ui_menu_english.txt, or no about lines: returned unchanged."""
    if not about or os.path.basename(rel) != ABOUT_FILE:
        return lines, None
    heads = [i for i, line in enumerate(lines) if HDR.match(line)]
    start = next((i for i in heads if int(HDR.match(lines[i]).group(1)) == ABOUT_ID), None)
    if start is None:
        return lines, f'record {ABOUT_ID} (About screen) not found'
    end = next((i for i in heads if i > start), len(lines))
    n = len(about)
    if end - start - 1 < n or lines[end - n:end] != about:
        return lines, (f'record {ABOUT_ID} (About screen) does not end with the {n} line(s) of the About file '
                       f'- run the import again')
    return lines[:end - n] + lines[end:], None
