"""Build the translation table: one row per unique text to translate, for all files of both modes.

Usage:
  python build_tm.py EN_ROOT GENDERS_TSV OUT_TSV

  EN_ROOT      folder with the English BM_* and BAT_* folders
  GENDERS_TSV  analysis/speaker_genders.tsv (speaker_id, gender M/F/?)
  OUT_TSV      table to write. If it already exists, filled-in "ukrainian" cells are kept (matched by key).

Columns: key, english, ukrainian, speaker_gender, listener_gender, count, speakers, listeners, first_seen, notes
- Translate only the "ukrainian" column. Leave it empty to keep English.
- Multi-line texts are joined with " ¶ " - keep exactly the same number of ¶ in the translation.
- Leading {tags} and [notes] such as [ALT] are NOT in the table; they are put back automatically.
- Tabs inside text are written as \\t.
- speaker_gender / listener_gender are filled only when the Ukrainian form depends on them
  (M = male, F = female, ? = unknown - decide from the scene). The same English can then appear in 2-3 rows.
Rows are ordered default mode first (episode 101 -> 105, menus), then Noir-only texts; inside a file by record
number, so neighbouring rows are usually the same conversation.
Writers' notes, texts without letters and subtitles that are only [sighs]-style notes are left out (stay English).
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landb_txt import exists, read_records, txt_files  # noqa: E402
from tm_lib import LINE_SEP, analyze_records, escape_cell, load_genders, loose_text, unescape_cell  # noqa: E402

COLS = ['key', 'english', 'ukrainian', 'speaker_gender', 'listener_gender', 'count', 'speakers', 'listeners',
        'first_seen', 'notes']


def file_order(rel):
    folder = rel.split('/')[0]
    mode = 0 if folder.startswith('BM_') else 1
    m = re.search(r'(10[1-5])', folder)
    grp = m.group(1) if m else {'Menu': '200', 'Boot': '300', 'Project': '400'}.get(
        next((g for g in ('Menu', 'Boot', 'Project') if g in folder), ''), '900')
    return mode, grp, rel


def read_table(path):
    rows = {}
    if not exists(path):
        return rows
    with open(path, encoding='utf-8-sig') as fh:
        header = fh.readline().rstrip('\r\n').split('\t')
        for line in fh:
            row = dict(zip(header, line.rstrip('\r\n').split('\t')))
            if row.get('key'):
                rows[row['key']] = row
    return rows


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    root, gpath, out = sys.argv[1:]
    genders = load_genders(gpath)
    old = read_table(out)

    rows, order = {}, []
    for rel in sorted(txt_files(root), key=file_order):
        recs = read_records(os.path.join(root, rel))[0]
        info = analyze_records(recs, genders)
        for r in sorted(recs, key=lambda x: x['id']):
            if r['id'] not in info:
                continue
            i = info[r['id']]
            key = i['key']
            if key not in rows:
                cores = i['cores']
                notes = []
                if len(cores) > 1:
                    notes.append(f'{len(cores)} lines: keep {len(cores) - 1} ¶')
                if any(re.search(r'\{[^{}]*\}|\^[^^]*\^|<[^<>]+>', c) for c in cores):
                    notes.append('keep markup inside')
                if 'credits' in rel:
                    notes.append('credits: people’s names stay in Latin')
                rows[key] = {'key': key, 'english': escape_cell(LINE_SEP.join(cores)), 'ukrainian': '',
                             'speaker_gender': i['sg'], 'listener_gender': i['lg'], 'count': 0,
                             'speakers': collections.Counter(), 'listeners': collections.Counter(),
                             'first_seen': f"{rel}:{r['idx'] + 1}", 'notes': notes, 'guessed': 0}
                order.append(key)
            row = rows[key]
            row['count'] += 1
            row['speakers'][i['speaker']] += 1
            if i['listener']:
                row['listeners'][i['listener']] += 1
            if i['lg'] and i['how'] == 'nearby':
                row['guessed'] += 1

    first_loose = {}
    for key in order:
        row = rows[key]
        lk = (loose_text(row['english']), row['speaker_gender'], row['listener_gender'])
        if lk[0] and lk in first_loose:
            row['notes'].append(f'near-copy of {first_loose[lk]}')
        else:
            first_loose.setdefault(lk, key)

    # rows translated earlier whose gender was "?" and is now known (or the reverse) keep their translation
    def parts(k):
        m = re.match(r'^([0-9a-f]+)(?:-S([MF?]))?(?:-L([MF?]))?$', k)
        return (m.group(1), m.group(2) or '', m.group(3) or '') if m else (k, '', '')
    old_by_hash = collections.defaultdict(list)
    for k, v in old.items():
        if v.get('ukrainian'):
            old_by_hash[parts(k)[0]].append((k, v))
    used_old = set()

    kept = 0
    with open(out, 'w', encoding='utf-8-sig', newline='\r\n') as fh:
        fh.write('\t'.join(COLS) + '\n')
        for key in order:
            row = rows[key]
            if key in old and old[key].get('ukrainian'):
                row['ukrainian'] = old[key]['ukrainian']
                used_old.add(key)
                kept += 1
            else:
                h, sg, lg = parts(key)
                for ok, ov in old_by_hash.get(h, []):
                    _, osg, olg = parts(ok)
                    if osg in ('?', '', sg) and olg in ('?', '', lg) or sg in ('?', '') and lg in ('?', ''):
                        row['ukrainian'] = ov['ukrainian']
                        row['notes'].append(f'translation taken from {ok} - check gender forms')
                        used_old.add(ok)
                        kept += 1
                        break
            if row['guessed']:
                row['notes'].append('listener guessed - check scene')
            row['speakers'] = ', '.join(s for s, _ in row['speakers'].most_common(4))
            row['listeners'] = ', '.join(s for s, _ in row['listeners'].most_common(3))
            row['notes'] = '; '.join(row['notes'])
            fh.write('\t'.join(str(row[c]) for c in COLS) + '\n')
    lost = [k for k, v in old.items() if v.get('ukrainian') and k not in rows and k not in used_old]
    if lost:
        with open(out + '.lost.tsv', 'w', encoding='utf-8-sig', newline='\r\n') as fh:
            fh.write('\t'.join(COLS) + '\n')
            for k in lost:
                fh.write('\t'.join(old[k].get(c, '') for c in COLS) + '\n')
    words = sum(len(unescape_cell(rows[k]['english']).split()) for k in order)
    print(f'{len(order)} rows ({words} English words) -> {out}. Kept {kept} existing translation(s).')
    if lost:
        print(f'WARNING: {len(lost)} translated row(s) no longer match any text - saved to {out}.lost.tsv')


if __name__ == '__main__':
    main()
