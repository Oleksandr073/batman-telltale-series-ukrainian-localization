"""Check that the final game files contain exactly the texts from the unique folder.

Usage:
  python check_consistency.py ORIGINAL GENDERS UNIQUE_LOCALIZED LOCALIZED [--overrides OVERRIDES_TSV]

  ORIGINAL          original_data            (English game files)
  GENDERS           reference/speaker_genders.xlsx (same file the table was built with)
  UNIQUE_LOCALIZED  unique_localized_data    (each unique text once, "#### key | ..." entries)
  LOCALIZED         localized_data           (final game files)

It does not read the translation table. For every record of every file in ORIGINAL:
  - if the record has an entry in UNIQUE_LOCALIZED, the record in LOCALIZED must be exactly the English
    record with each text line's core replaced by that entry's line (the leading tags/[ALT] and trailing
    spaces from the English line kept);
  - otherwise (writers' notes, "[sighs]" lines, texts without letters) it must be identical to the English record;
  - header lines must be identical.
It also reports unique entries that no game file uses, and files missing in LOCALIZED.
Records listed in --overrides are allowed to differ (reported separately).
Exit code 1 on any mismatch.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landb_txt import exists, read_records, split_lines, read_raw, txt_files  # noqa: E402
from tm_lib import analyze_records, check_root, load_genders, split_line  # noqa: E402


def read_unique(folder):
    """-> {key: [lines]} from all .txt files in the unique folder."""
    entries = {}
    for rel in txt_files(folder):
        lines, _ = split_lines(read_raw(os.path.join(folder, rel)))
        key, buf = None, []
        for line in lines + ['#### END']:
            if line.startswith('#### '):
                if key is not None:
                    entries[key] = buf[:-1] if buf and buf[-1] == '' else buf  # drop the separator line
                key, buf = line[5:].split(' | ', 1)[0].strip(), []
            elif key is not None:
                buf.append(line)
    entries.pop('END', None)
    return entries


def read_override_keys(path):
    keys = set()
    if path:
        with open(path, encoding='utf-8-sig') as fh:
            header = fh.readline().rstrip('\r\n').split('\t')
            for line in fh:
                row = dict(zip(header, line.rstrip('\r\n').split('\t')))
                if row.get('file') and row.get('id') and row.get('ukrainian'):
                    keys.add((row['file'].replace('\\', '/'), int(row['id'])))
    return keys


def check(original, genders_path, unique_dir, localized, overrides=None, show=20):
    genders = load_genders(genders_path)
    files = txt_files(original)
    check_root(files, original)
    unique = read_unique(unique_dir)
    override_keys = read_override_keys(overrides)
    problems, used = [], set()
    n_tr = n_same = n_over = 0
    for rel in files:
        loc_path = os.path.join(localized, rel)
        if not exists(loc_path):
            problems.append(f'{rel}: missing in {localized}')
            continue
        en_recs = read_records(os.path.join(original, rel))[0]
        loc_recs = read_records(loc_path)[0]
        if len(en_recs) != len(loc_recs):
            problems.append(f'{rel}: {len(loc_recs)} records, English has {len(en_recs)}')
            continue
        info = analyze_records(en_recs, genders)
        for e, l in zip(en_recs, loc_recs):
            where = f"{rel}:{e['idx'] + 1}"
            if e['hdr'] != l['hdr']:
                problems.append(f'{where}: header {l["hdr"]!r} should be {e["hdr"]!r}')
                continue
            i = info.get(e['id'])
            expected = e['body']
            if i:
                # entries are listed by table key only when one English text has several Ukrainian versions;
                # otherwise by the plain text id (the key without the -S/-L gender ending)
                k = i['key'] if i['key'] in unique else i['key'].split('-')[0]
                used.add(k)
                entry = unique.get(k)
                if entry is None:
                    problems.append(f"{where}: key {i['key']} not found in {unique_dir} (run the import again)")
                    continue
                if len(entry) != len(e['body']):
                    problems.append(f"{where}: unique entry {i['key']} has {len(entry)} line(s), record has "
                                    f"{len(e['body'])}")
                    continue
                expected = []
                for line, new in zip(e['body'], entry):
                    prefix, _, suffix = split_line(line)
                    expected.append('' if line == '' else prefix + new + suffix)
            if l['body'] == expected:
                if expected != e['body']:
                    n_tr += 1
                else:
                    n_same += 1
            elif (rel, e['id']) in override_keys:
                n_over += 1
            else:
                problems.append(f'{where}: text differs from {unique_dir}\n      expected: {expected!r:.150}'
                                f'\n      found:    {l["body"]!r:.150}')
    unused = sorted(set(unique) - used)
    print(f'Checked {len(files)} file(s) against {len(unique)} unique text(s): {n_tr} record(s) translated as in '
          f'{unique_dir}, {n_same} unchanged (English)' + (f', {n_over} override(s)' if n_over else '') + '.')
    if unused:
        print(f'  {len(unused)} unique text(s) not used by any game file: {", ".join(unused[:5])}')
    for p in problems[:show]:
        print('  MISMATCH ' + p)
    if len(problems) > show:
        print(f'  ... {len(problems) - show} more')
    print(f'Consistency: {len(problems)} mismatch(es).')
    return len(problems) + len(unused)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('original')
    ap.add_argument('genders')
    ap.add_argument('unique_localized')
    ap.add_argument('localized')
    ap.add_argument('--overrides')
    ap.add_argument('--show', type=int, default=20)
    a = ap.parse_args()
    sys.exit(1 if check(a.original, a.genders, a.unique_localized, a.localized, a.overrides, a.show) else 0)


if __name__ == '__main__':
    main()
