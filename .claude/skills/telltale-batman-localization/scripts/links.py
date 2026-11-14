"""The localization author and Telegram channel, kept in ONE place: author.txt in the repo root.

author.txt holds two lines: "author: NAME" and "channel: NAME". Every other settings file uses placeholders, which
the scripts replace when they read the file:
  {author}          the author's name, as written in author.txt
  {telegram}        https://t.me/NAME     full link - opens the Telegram app on phones (QR codes, text)
  {telegram_short}  t.me/NAME             short link for text on screen
  {telegram_web}    https://t.me/s/NAME   web view - for links clicked in game: the Steam overlay browser can't
                                          open the Telegram app (plain t.me/NAME shows an error page there)
Used by: data/game_text/credits/*.txt (credits.py), data/about_button/button.txt (apply_about_button.py),
data/feed_item/feed_item.txt (apply_feed_item.py, make_feed_texture.py).
author.txt is looked up in the folder of the settings file and then in each folder above it, up to the repo root
(the folder with .git or package.json) and never beyond it - so the repo root's author.txt is found for
data/game_text/credits/ as well as for data/about_button/ and data/feed_item/.
"""
import os
import re

FILE = 'author.txt'
PLACEHOLDER = re.compile(r'\{(?:author|telegram[A-Za-z_]*)\}')
KEYS = ('author', 'channel')
_cache = {}


def _find(folder):
    """-> path of the nearest author.txt: in folder or a folder above it, up to the repo root."""
    start = here = os.path.abspath(folder)
    while not os.path.isfile(os.path.join(here, FILE)):
        up = os.path.dirname(here)
        # stop at the repo root (it has .git or package.json), so an author.txt outside the repo is never used
        at_root = any(os.path.exists(os.path.join(here, m)) for m in ('.git', 'package.json'))
        if at_root or up == here:
            raise SystemExit(f'ERROR: {FILE} not found in {start} or the folders above it up to the repo root - it '
                             f'holds "author: NAME" and "channel: NAME", which the {{author}} / {{telegram...}} '
                             f'placeholders need')
        here = up
    return os.path.join(here, FILE)


def load(folder):
    """-> {placeholder: value} from the nearest author.txt."""
    path = _find(folder)
    if path in _cache:
        return _cache[path]
    values = {}
    with open(path, encoding='utf-8-sig') as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            m = re.match(r'^(\w+)\s*:\s*(.*?)$', line)
            if not m or m.group(1) not in KEYS:
                raise SystemExit(f'ERROR: {path} line {n}: expected "author: NAME" or "channel: NAME", got {line!r}')
            if m.group(1) in values:
                raise SystemExit(f'ERROR: {path} line {n}: "{m.group(1)}:" is given twice')
            values[m.group(1)] = m.group(2)
    for key in KEYS:
        if not values.get(key):
            raise SystemExit(f'ERROR: {path}: "{key}: NAME" is missing or empty')
    author, name = values['author'], values['channel']
    if '^' in author or '<' in author or '{' in author:
        raise SystemExit(f'ERROR: {path}: the author must not contain ^, < or {{ (they are game markup)')
    m = re.match(r'^(?:https?://)?(?:t\.me|telegram\.me)/(?:s/)?([A-Za-z0-9_]+)/?$', name)
    if m:
        name = m.group(1)  # a whole link was pasted - keep the name only
    if not re.match(r'^[A-Za-z0-9_]{4,32}$', name):
        raise SystemExit(f'ERROR: {path}: channel name {name!r} - only letters, digits and _ (the part after t.me/)')
    _cache[path] = {
        '{author}': author,
        '{telegram}': f'https://t.me/{name}',
        '{telegram_short}': f't.me/{name}',
        '{telegram_web}': f'https://t.me/s/{name}',
    }
    return _cache[path]


def expand(text, folder, where):
    """Replace the {author} / {telegram...} placeholders in text. folder = the folder of the settings file,
    where = its name (for error messages)."""
    found = PLACEHOLDER.findall(text)
    if not found:
        return text
    values = load(folder)
    for p in found:
        if p not in values:
            raise SystemExit(f'ERROR: {where}: unknown placeholder {p} - use {", ".join(values)}')
        text = text.replace(p, values[p])
    return text
