"""Compare translated landb .txt files against the English originals.

Usage:
  python validate.py ORIGINAL  TRANSLATED   [--show N] [--untranslated]
  (ORIGINAL/TRANSLATED can both be files or both be folders; folders are matched by relative path)

ERRORS (file will break or import wrong):
  - missing BOM, LF-only / CR-only line endings, missing final CRLF
  - different number of lines
  - header line ("N) SPEAKER") changed, moved, or a text line that now looks like a header
  - empty text line filled in (or the reverse) - it breaks multi-line layouts
  - {..} ^..^ <..> <<..>> markup added, lost or changed
WARNINGS (probably fine, but look):
  - markup order changed inside a line
  - leading/trailing spaces or tabs differ from the original
  - straight " quotes introduced (the English files use only typographic quotes)
Exit code 1 if any error.
"""
import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landb_txt import HDR, exists, parse_lines, read_raw, split_lines, tokens, txt_files, visible_text  # noqa: E402


def check_pair(orig_path, tr_path, rel, out, args):
    errs, warns = [], []
    E = lambda ln, msg: errs.append((ln, msg))
    W = lambda ln, msg: warns.append((ln, msg))

    o_lines, o_info = split_lines(read_raw(orig_path))
    t_lines, t_info = split_lines(read_raw(tr_path))

    if o_info['bom'] and not t_info['bom']:
        E(0, 'UTF-8 BOM missing (save as "UTF-8 with BOM")')
    if t_info['lone_lf'] or t_info['lone_cr']:
        E(0, f"line endings must be CRLF: {t_info['lone_lf']} LF-only, {t_info['lone_cr']} CR-only")
    if o_info['final_eol'] and not t_info['final_eol']:
        E(0, 'file must end with CRLF (an empty line after the last text)')
    if len(o_lines) != len(t_lines):
        E(0, f'line count {len(t_lines)} != original {len(o_lines)} (diff {len(t_lines) - len(o_lines):+d})')

    # Find the first record whose line count changed; lines after it are shifted, so stop checking there.
    stop_at = min(len(o_lines), len(t_lines))
    o_recs, _ = parse_lines(o_lines)
    t_recs, _ = parse_lines(t_lines)
    for a, b in zip(o_recs, t_recs):
        if a['id'] != b['id'] or a['idx'] != b['idx'] or len(a['body']) != len(b['body']):
            E(a['idx'] + 1, f"FIRST BROKEN RECORD: original {a['hdr']!r} has {len(a['body'])} text line(s), "
                            f"translation {b['hdr']!r} has {len(b['body'])}. Fix this first; later lines not checked.")
            stop_at = min(a['idx'], b['idx'])
            for i in range(stop_at, min(len(o_lines), len(t_lines))):
                if bool(HDR.match(o_lines[i])) != bool(HDR.match(t_lines[i])):
                    what = ('text line looks like a header (starts with "number) ")' if HDR.match(t_lines[i])
                            else 'header expected here - a line was added or removed before this')
                    E(i + 1, f'{what}: {t_lines[i][:60]!r}')
                    break
            break
    else:
        if len(o_recs) != len(t_recs):
            E(0, f'record count {len(t_recs)} != original {len(o_recs)}')

    untranslated = 0
    for i in range(stop_at):
        o, t = o_lines[i], t_lines[i]
        ln = i + 1
        o_hdr = HDR.match(o)
        if o_hdr:
            if t != o:
                hint = '' if HDR.match(t) else '  <- a line was added/removed above this point'
                E(ln, f'header changed: {o!r} -> {t!r}{hint}')
            continue
        if HDR.match(t):
            E(ln, f'text line looks like a header (starts with "number) "): {t[:60]!r}')
            continue
        if (o == '') != (t == ''):
            E(ln, 'empty line filled in' if o == '' else f'line emptied (original: {o[:60]!r})')
        ot, tt = tokens(o), tokens(t)
        for kind in ot:
            if collections.Counter(ot[kind]) != collections.Counter(tt[kind]):
                miss = list((collections.Counter(ot[kind]) - collections.Counter(tt[kind])).elements())
                extra = list((collections.Counter(tt[kind]) - collections.Counter(ot[kind])).elements())
                E(ln, f'{kind} markup differs; missing {miss} extra {extra}')
            elif ot[kind] != tt[kind]:
                W(ln, f'{kind} markup order changed: {ot[kind]} -> {tt[kind]}')
        if o and t:
            if (o[:1] in ' \t') != (t[:1] in ' \t'):
                W(ln, 'leading whitespace differs from original')
            if (o[-1:] in ' \t') != (t[-1:] in ' \t'):
                W(ln, 'trailing whitespace differs from original')
            if o.count('\t') != t.count('\t'):
                W(ln, 'tab count differs from original')
            if '"' in t and '"' not in o:
                W(ln, 'straight " quote introduced (original files use typographic quotes only)')
        if o == t and visible_text(o) and any(c.isalpha() for c in visible_text(o)):
            untranslated += 1
            if args.untranslated:
                W(ln, f'untranslated: {o[:70]!r}')

    if errs or warns or args.verbose:
        out.append(f'\n== {rel}: {len(errs)} error(s), {len(warns)} warning(s), {untranslated} untranslated line(s)')
        for ln, msg in (errs + warns)[: args.show]:
            tag = 'ERROR' if (ln, msg) in errs else 'warn '
            out.append(f'  {tag} line {ln}: {msg}')
        if len(errs) + len(warns) > args.show:
            out.append(f'  ... {len(errs) + len(warns) - args.show} more (use --show)')
    return len(errs), len(warns), untranslated


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('original')
    ap.add_argument('translated')
    ap.add_argument('--show', type=int, default=30, help='max messages per file (default 30)')
    ap.add_argument('--untranslated', action='store_true', help='list lines identical to English')
    ap.add_argument('-v', '--verbose', action='store_true', help='also print files without problems')
    args = ap.parse_args()

    if os.path.isdir(args.original):
        rels = txt_files(args.original)
        pairs = [(os.path.join(args.original, r), os.path.join(args.translated, r), r) for r in rels]
    else:
        pairs = [(args.original, args.translated, os.path.basename(args.translated))]

    out, te, tw, tu, missing = [], 0, 0, 0, []
    for o, t, rel in pairs:
        if not exists(t):
            missing.append(rel)
            continue
        e, w, u = check_pair(o, t, rel, out, args)
        te, tw, tu = te + e, tw + w, tu + u
    print('\n'.join(out))
    if missing:
        print(f'\n{len(missing)} file(s) not found in translated folder (skipped): ' + ', '.join(missing[:10]) +
              (' ...' if len(missing) > 10 else ''))
    print(f'\nChecked {len(pairs) - len(missing)} file(s): {te} error(s), {tw} warning(s), {tu} untranslated line(s).')
    sys.exit(1 if te else 0)


if __name__ == '__main__':
    main()
