"""The Telegram channel link, kept in ONE place: telegram.txt in the repo root.

telegram.txt holds the channel name ("channel: NAME"). Every other settings file uses placeholders, which the
scripts replace when they read the file:
  {telegram}        https://t.me/NAME     full link - opens the Telegram app on phones (QR codes, text)
  {telegram_short}  t.me/NAME             short link for text on screen
  {telegram_web}    https://t.me/s/NAME   web view - for links clicked in game: the Steam overlay browser can't
                                          open the Telegram app (plain t.me/NAME shows an error page there)
Used by: credits/*.txt (credits.py), about_button_data/button.txt (apply_about_button.py),
feed_item_data/feed_item.txt (apply_feed_item.py, make_feed_texture.py).
telegram.txt is looked up next to the folder of the settings file (the repo root for all of the above).
"""
import os
import re

FILE = 'telegram.txt'
PLACEHOLDER = re.compile(r'\{telegram[A-Za-z_]*\}')
_cache = {}


def load(folder):
    """-> {placeholder: value} from telegram.txt next to folder (in its parent folder)."""
    path = os.path.join(os.path.dirname(os.path.abspath(folder)), FILE)
    if path in _cache:
        return _cache[path]
    if not os.path.isfile(path):
        raise SystemExit(f'ERROR: {path} not found - it holds the Telegram channel ("channel: NAME"), which the '
                         f'{{telegram...}} placeholders need')
    name = None
    with open(path, encoding='utf-8-sig') as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            m = re.match(r'^channel\s*:\s*(\S+)$', line)
            if not m:
                raise SystemExit(f'ERROR: {path} line {n}: expected "channel: NAME", got {line!r}')
            name = m.group(1)
    if not name:
        raise SystemExit(f'ERROR: {path}: "channel: NAME" is missing')
    m = re.match(r'^(?:https?://)?(?:t\.me|telegram\.me)/(?:s/)?([A-Za-z0-9_]+)/?$', name)
    if m:
        name = m.group(1)  # a whole link was pasted - keep the name only
    if not re.match(r'^[A-Za-z0-9_]{4,32}$', name):
        raise SystemExit(f'ERROR: {path}: channel name {name!r} - only letters, digits and _ (the part after t.me/)')
    _cache[path] = {
        '{telegram}': f'https://t.me/{name}',
        '{telegram_short}': f't.me/{name}',
        '{telegram_web}': f'https://t.me/s/{name}',
    }
    return _cache[path]


def expand(text, folder, where):
    """Replace the {telegram...} placeholders in text. folder = the folder of the settings file, where = its name
    (for error messages)."""
    found = PLACEHOLDER.findall(text)
    if not found:
        return text
    values = load(folder)
    for p in found:
        if p not in values:
            raise SystemExit(f'ERROR: {where}: unknown placeholder {p} - use {", ".join(values)}')
        text = text.replace(p, values[p])
    return text
