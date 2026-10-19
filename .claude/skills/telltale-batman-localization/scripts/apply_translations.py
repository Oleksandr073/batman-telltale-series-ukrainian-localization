"""Put translations from the table back into the game files (both modes), then validate them.

Usage:
  python apply_translations.py EN_ROOT GENDERS TABLE OUT_ROOT [--unique UNIQUE_EN UNIQUE_UK]
                               [--overrides OVERRIDES_TSV] [--only PREFIX]

  EN_ROOT        English BM_* and BAT_* folders (never modified)
  GENDERS        reference/speaker_genders.xlsx - must be the same file the table was built with
  TABLE          table from build_tm.py (.xlsx or .tsv) with the "Ukrainian" column (partly) filled
  OUT_ROOT       where translated files are written (same folder structure as EN_ROOT)
  --overrides    optional TSV with columns: file, id, ukrainian[, comment]
                 a translation for one specific record (file = path like BM_pc_Batman101_data/x_english.txt),
                 used when one table row needs a different translation in one scene. Same ¶ rules as the table.
  --only         only write files whose path starts with this (e.g. BM_ or BAT_pc_BatmanNoir103_data)
  --unique       UNIQUE_EN UNIQUE_UK: the folders with every unique text once (see build_tm.py).
                 UNIQUE_EN (unique_original_data) is only CHECKED against EN_ROOT, never written; if it does not
                 match, the script stops. UNIQUE_UK (unique_localized_data) is rewritten with the Ukrainian
                 from the table (untranslated rows keep English), so `git diff UNIQUE_UK` shows each
                 translation once. After writing, the 222 files are compared with UNIQUE_UK.

Headers, empty lines, leading {tags}/[notes] like [ALT], trailing spaces, BOM and CRLF are copied from the
English file. Records without a translation stay English. After writing, every file is validated.
"""
import argparse
import collections
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landb_txt import read_records, txt_files, write_lines  # noqa: E402
from tm_lib import (analyze_records, check_root, compare_unique, load_genders, read_table,  # noqa: E402
                    split_line, split_translation, unique_files, write_unique)
import validate  # noqa: E402
import check_consistency  # noqa: E402


def read_tsv(path):
    with open(path, encoding='utf-8-sig') as fh:
        header = fh.readline().rstrip('\r\n').split('\t')
        return [dict(zip(header, line.rstrip('\r\n').split('\t'))) for line in fh if line.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('en')
    ap.add_argument('genders')
    ap.add_argument('table')
    ap.add_argument('out')
    ap.add_argument('--overrides')
    ap.add_argument('--only', default='')
    ap.add_argument('--unique', nargs=2, metavar=('UNIQUE_EN_DIR', 'UNIQUE_UK_DIR'),
                    help='also write every unique text once (English / Ukrainian) for easy git diff')
    a = ap.parse_args()

    check_root(txt_files(a.en), a.en)
    genders = load_genders(a.genders)
    rows = read_table(a.table)
    table = {r['key']: r.get('ukrainian', '') for r in rows if r.get('key')}
    if a.unique:
        stale = compare_unique(a.en, a.unique[0])
        if stale:
            sys.exit(f'{a.unique[0]} does not match the table ({len(stale)} file(s), e.g. {stale[0]}). '
                     f'It must be built from {a.en} only - create it with build_tm.py --unique-original '
                     f'{a.unique[0]} (see README). Nothing was written.')
        files, bad = unique_files(a.en, rows)
        nfiles = write_unique(files, a.unique[1])
        print(f'{a.unique[0]} matches {a.en} (not changed). Wrote {len(rows)} unique texts into {nfiles} '
              f'file(s) in {a.unique[1]}' + (f' ({bad} with a wrong ¶ count kept in English)' if bad else ''))
    overrides = {}
    if a.overrides:
        for r in read_tsv(a.overrides):
            if r.get('file') and r.get('id') and r.get('ukrainian'):
                overrides[(r['file'].replace('\\', '/'), int(r['id']))] = r['ukrainian']

    st = collections.Counter()
    problems, missing_keys = [], set()
    written = []
    for rel in txt_files(a.en):
        if not rel.startswith(a.only):
            continue
        recs, pre, _, _ = read_records(os.path.join(a.en, rel))
        info = analyze_records(recs, genders)
        out = list(pre)
        for r in recs:
            out.append(r['hdr'])
            i = info.get(r['id'])
            cell = overrides.get((rel, r['id']))
            src = 'override' if cell else 'table'
            if i and not cell:
                if i['key'] not in table:
                    missing_keys.add(i['key'])
                cell = table.get(i['key'], '')
            if not i and not cell:
                out.extend(r['body'])
                st['not in table (stays English)'] += 1
                continue
            if not cell:
                out.extend(r['body'])
                st['not translated yet'] += 1
                continue
            parts = split_translation(cell, len(r['body']))
            if parts is None:
                problems.append(f"{rel}:{r['idx'] + 1} ({src}) needs {len(r['body']) - 1} ¶ "
                                f"but has {cell.count('¶')} - left in English")
                out.extend(r['body'])
                st['wrong ¶ count'] += 1
                continue
            for line, tr in zip(r['body'], parts):
                prefix, core, suffix = split_line(line)
                out.append('' if line == '' else prefix + tr + suffix)
            st['translated (override)' if src == 'override' else 'translated'] += 1
        write_lines(os.path.join(a.out, rel), out)
        written.append(rel)

    print(f'Wrote {len(written)} file(s) to {a.out}')
    for k, v in st.most_common():
        print(f'  {k}: {v}')
    if missing_keys:
        print(f'  WARNING: {len(missing_keys)} record key(s) not found in the table - rebuild the table '
              f'(build_tm.py) after changing the genders file.')
    for p in problems[:30]:
        print('  ' + p)
    if len(problems) > 30:
        print(f'  ... {len(problems) - 30} more')

    print('\nValidating...')
    args = types.SimpleNamespace(show=10, untranslated=False, verbose=False)
    msgs, errors = [], 0
    for rel in written:
        e, _, _ = validate.check_pair(os.path.join(a.en, rel), os.path.join(a.out, rel), rel, msgs, args)
        errors += e
    print('\n'.join(msgs) if msgs else 'No problems found.')
    print(f'Validation: {errors} error(s) in {len(written)} file(s).')
    mismatches = 0
    if a.unique and not a.only:
        print(f'\nComparing {a.out} with {a.unique[1]}...')
        mismatches = check_consistency.check(a.en, a.genders, a.unique[1], a.out, a.overrides)
    sys.exit(1 if errors or problems or mismatches else 0)


if __name__ == '__main__':
    main()
