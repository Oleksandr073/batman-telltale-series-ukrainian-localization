"""Shared reader/writer for Telltale landb text exports ("N) SPEAKER" + text lines).

File format (verified on all 222 Batman S1 files):
  - UTF-8 with BOM, CRLF line endings, file ends with CRLF.
  - Header line: digits + ")" + one space + speaker (speaker may be empty -> line ends with ") ").
  - Every following line up to the next header is the record's text (1..103 lines, can be empty).
"""
import os
import re
import sys

HDR = re.compile(r'^(\d+)\) (.*)$')
BOM = b'\xef\xbb\xbf'

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


def _long(path):
    """Allow Windows paths longer than 260 characters."""
    path = os.path.abspath(path)
    prefix = '\\\\?\\'
    if os.name == 'nt' and not path.startswith(prefix):
        path = prefix + path
    return path


def exists(path):
    return os.path.exists(_long(path))


def read_raw(path):
    with open(_long(path), 'rb') as fh:
        return fh.read()


def split_lines(raw):
    """Return (lines, info) without BOM and CRLF. info holds format facts."""
    info = {
        'bom': raw.startswith(BOM),
        'final_eol': raw.endswith(b'\r\n'),
        'lone_lf': raw.count(b'\n') - raw.count(b'\r\n'),
        'lone_cr': raw.replace(b'\r\n', b'').count(b'\r'),
    }
    text = raw[3:] if info['bom'] else raw
    text = text.decode('utf-8', errors='replace')
    lines = re.split(r'\r\n|\r|\n', text)
    if lines and lines[-1] == '':
        lines.pop()
    return lines, info


def parse_lines(lines):
    """Return list of records: {id, spk, hdr_index, body:[...]}. Text before first header goes to 'pre'."""
    recs, pre = [], []
    for i, line in enumerate(lines):
        m = HDR.match(line)
        if m:
            recs.append({'id': int(m.group(1)), 'spk': m.group(2), 'hdr': line, 'idx': i, 'body': []})
        elif recs:
            recs[-1]['body'].append(line)
        else:
            pre.append(line)
    return recs, pre


def read_records(path):
    lines, info = split_lines(read_raw(path))
    recs, pre = parse_lines(lines)
    return recs, pre, lines, info


def write_lines(path, lines):
    os.makedirs(os.path.dirname(_long(path)), exist_ok=True)
    data = BOM + ('\r\n'.join(lines) + '\r\n').encode('utf-8')
    with open(_long(path), 'wb') as fh:
        fh.write(data)


def txt_files(root):
    out = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if not d.startswith('.')]
        for f in fn:
            if f.lower().endswith('.txt'):
                out.append(os.path.relpath(os.path.join(dp, f), root).replace(os.sep, '/'))
    return sorted(out)


# --- markup tokens that must survive translation unchanged -----------------
TOKEN_RES = {
    'curly {..}': re.compile(r'\{[^{}]*\}'),
    'caret ^..^': re.compile(r'\^[^^]*\^'),
    'image <..>': re.compile(r'(?<!<)<[^<>]+>(?!>)'),
    'double <<..>>': re.compile(r'<<[^<>]*>>'),
    'alt [ALT..]': re.compile(r'\[alt\b[^\[\]]*\]', re.IGNORECASE),
}


def tokens(line):
    return {name: rx.findall(line) for name, rx in TOKEN_RES.items()}


def visible_text(line):
    """Text with all markup removed (roughly what the player sees in a subtitle)."""
    s = re.sub(r'\{[^{}]*\}|\[[^\[\]]*\]|\^[^^]*\^|<<[^<>]*>>|<[^<>]+>', '', line)
    return s.strip()
