"""Localization credits: extra lines added to the end of a few game texts (both modes), optionally smaller.

Each file in the credits folder belongs to one record (see TARGETS):
  about.txt -> record 658 of ui_menu_english.txt (About screen of the main menu)
  boot.txt  -> record 21 of boot_english.txt (copyright text on the boot screen)
The import (apply_translations.py --credits DIR) adds every line of the file after that record's original (or
translated) text. Font size (1 = normal, 0.8 = 80%): each non-empty line gets the game's size tag ^glyphScale:N^.
  # scale: N            the whole record (original text and credits)
  # scale original: N   only the original text above the credits
  # scale credits: N    only the credit lines
(the specific lines win over "# scale: N"). Size 1 adds no tag - except on the credit lines when the original text
is resized: the game keeps a size for the following lines, so the credits then get ^glyphScale:1^ explicitly.
These records are the ONLY ones allowed to differ from the English in line count and markup: validate.py and
check_consistency.py (with the same --credits DIR) remove exactly these lines and tags before their usual checks,
and report an error if they are missing or different. A missing file = nothing changed in that record.

File format: plain UTF-8 text, one line = one line on screen; empty lines are kept (empty lines at the end are
ignored). Lines starting with "#" are settings/comments and are not shown, e.g. "# scale original: 0.7".
A line must not start with "number) " - it would become a new record.
"""
import os
import re

from landb_txt import HDR, read_raw, split_lines

# credits file -> (game file name, record id, what the player sees)
TARGETS = {
    'about.txt': ('ui_menu_english.txt', 658, 'About screen'),
    'boot.txt': ('boot_english.txt', 21, 'boot screen'),
}
SCALE = re.compile(r'^#\s*scale(?:\s+(original|credits))?\s*:\s*([0-9]*\.?[0-9]+)\s*$', re.I)


def _tag(scale):
    """Size tag, or nothing for the normal size (1)."""
    return f'^glyphScale:{scale}^' if scale and float(scale) != 1 else ''


class Credit:
    def __init__(self, label, lines, scale_original, scale_credits):
        self.label, self.lines = label, lines
        self.scale_original, self.scale_credits = scale_original, scale_credits
        self.tag_original, self.tag_credits = _tag(scale_original), _tag(scale_credits)
        if self.tag_original and not self.tag_credits:
            # the game keeps the size of the lines above, so normal-size credits need their own tag
            self.tag_credits = f'^glyphScale:{scale_credits or 1}^'

    @staticmethod
    def _style(lines, tag):
        return ['' if line == '' else tag + line for line in lines]

    def style_original(self, lines):
        """Put the original-text size tag at the start of every non-empty line."""
        return self._style(lines, self.tag_original)

    def styled_credits(self):
        return self._style(self.lines, self.tag_credits)

    def describe(self):
        o, c = (s if s and float(s) != 1 else None for s in (self.scale_original, self.scale_credits))
        if o == c:
            return f', size {o}' if o else ''
        return f', size: original {o or "normal"}, credits {c or "normal"}'


def read_credits(folder):
    """-> {(game file name, record id): Credit} for every credits file in folder."""
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
        lines, scale = [], {}
        for line in split_lines(read_raw(path))[0]:
            if line.startswith('#'):
                m = SCALE.match(line)
                if m:
                    scale[(m.group(1) or 'both').lower()] = m.group(2)
                elif re.match(r'^#\s*scale', line, re.I):
                    raise SystemExit(f'{path}: write the size as "# scale: 0.8", "# scale original: 0.7" or '
                                     f'"# scale credits: 0.9", not {line!r}')
                continue
            lines.append(line)
        while lines and lines[-1].strip() == '':
            lines.pop()
        bad = [line for line in lines if HDR.match(line)]
        if bad:
            raise SystemExit(f'{path}: a line must not start with "number) " (the game would read it as a new '
                             f'record): {bad[0]!r}')
        if lines or scale:
            out[(game_file, rec_id)] = Credit(f'{label} ({name})', lines, scale.get('original', scale.get('both')),
                                              scale.get('credits', scale.get('both')))
    return out


def credit_for(rel, rec_id, credits):
    """-> Credit if this record gets credits, else None."""
    return credits.get((os.path.basename(rel), rec_id)) if credits else None


def strip_credits(rel, lines, credits):
    """Undo what the import did to this file (credit lines, size tags). -> (lines, [error messages]).
    Files without credits are returned unchanged."""
    errors = []
    for (game_file, rec_id), c in (credits or {}).items():
        if os.path.basename(rel) != game_file:
            continue
        heads = [i for i, line in enumerate(lines) if HDR.match(line)]
        start = next((i for i in heads if int(HDR.match(lines[i]).group(1)) == rec_id), None)
        if start is None:
            errors.append(f'record {rec_id} ({c.label}) not found')
            continue
        end = next((i for i in heads if i > start), len(lines))
        n = len(c.lines)
        if end - start - 1 < n or lines[end - n:end] != c.styled_credits():
            errors.append(f'record {rec_id} ({c.label}) does not end with the {n} credit line(s) - run the import again')
            continue
        body = lines[start + 1:end - n]
        tag = c.tag_original
        if tag:
            if any(line and not line.startswith(tag) for line in body):
                errors.append(f'record {rec_id} ({c.label}): a line does not start with {tag} - run the import again')
                continue
            body = [line[len(tag):] for line in body]
        lines = lines[:start + 1] + body + lines[end:]
    return lines, errors
