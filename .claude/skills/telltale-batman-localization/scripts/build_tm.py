"""Build the translation table: every text to translate once, in play order, with context.

Usage:
  python build_tm.py EN_ROOT GENDERS OUT_TABLE [--order PLAY_ORDER] [--official OFFICIAL_USAGE]
                    [--unique-original UNIQUE_EN_DIR]

  EN_ROOT      folder with the English BM_* and BAT_* folders (data/original_data)
  GENDERS      speaker_genders.xlsx (speaker_id, gender M/F/?)
  OUT_TABLE    table to write: .xlsx (Excel/LibreOffice/Google Sheets, with a Help sheet) or .tsv.
               If it already exists, Ukrainian cells and translator notes are kept (matched by key).
               Close it in Excel first.
  --order      ai_context/play_order.txt: sections and game files in play order. Without it, files are sorted
               by name.
  --official   ai_context/official_usage.txt (made once, saved in the repo): fills the "Official" column - how many
               of Telltale's official translations translated the text. "no 0/8" = almost surely never shown.
  --unique-original  also (re)write this folder (data/unique_original_data): every unique English text once, built
               from EN_ROOT only (no genders). The import only checks it. It changes only if the English files do.

Table rows (Excel):
- section header  (EPISODE 1 ..., MENUS & UI, CREDITS, SHADOWS MODE) and scene header (one per game file);
- text row        - the first time a text appears: translate it here (yellow Ukrainian cell);
- reference row   - the same text again later in the story, in grey: its Ukrainian cell shows the text row's
                    translation (a formula) and is never read by the scripts. Repeats inside game files that are
                    mostly copies of an earlier file (shared dialogue databases, 50%+ overlap) get no reference rows.
Only text rows have a key. Normal mode first, in play order; texts that exist only in Shadows (Noir) mode at the end.
Writers' notes, texts without letters and subtitles that are only [sighs]-style notes are left out (stay English).
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landb_txt import exists, read_records, txt_files  # noqa: E402
from tm_lib import (LINE_SEP, analyze_records, check_root, escape_cell, file_order, load_genders,  # noqa: E402
                    loose_text, read_table, table_column_letter, unescape_cell, unique_files, write_table,
                    write_unique)

COPY_OVERLAP = 0.5          # a file sharing >= 50% of its texts with an earlier file is a copy: no reference rows


def load_old(path):
    return {r['key']: r for r in read_table(path)} if exists(path) else {}


def load_official(path):
    """official_usage.txt -> {'counts': {text hash: languages}, 'total': languages}, or None without --official."""
    if not path:
        return None
    if not exists(path):
        print(f'WARNING: {path} not found - the "Official" column stays empty')
        return None
    counts, total = {}, 8
    with open(path, encoding='utf-8-sig') as fh:
        for line in fh:
            m = re.search(r'of the (\d+) languages', line)
            if line.startswith('#'):
                total = int(m.group(1)) if m else total
                continue
            h, _, n = line.strip().partition('\t')
            if h:
                counts[h] = int(n)
    return {'counts': counts, 'total': total}


def read_play_order(path, files):
    """-> [(section title, [(rel, scene title), ...]), ...] covering every BM_* file (missing ones at the end)."""
    sections, seen = [], set()
    if path:
        with open(path, encoding='utf-8-sig') as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('=='):
                    sections.append((line[2:].strip(), []))
                    continue
                name, _, title = line.partition('|')
                rel = name.strip() + '_english.txt'
                if rel not in files:
                    print(f'WARNING: {path}: {name.strip()} is not a game file - ignored')
                    continue
                if not sections:
                    sections.append(('GAME', []))
                sections[-1][1].append((rel, title.strip()))
                seen.add(rel)
    rest = [f for f in sorted(files, key=file_order) if f.startswith('BM_') and f not in seen]
    if rest:
        title = 'NOT IN PLAY ORDER — add these files to ai_context/play_order.txt' if path else 'GAME TEXT'
        sections.append((title, [(f, '') for f in rest]))
        if path:
            print(f'WARNING: {len(rest)} file(s) are not in {path} - put at the end of the table: '
                  + ', '.join(rest[:5]))
    return sections


def main():
    args = sys.argv[1:]
    opts = {}
    for flag in ('--unique-original', '--order', '--official'):
        if flag in args:
            i = args.index(flag)
            if i + 1 >= len(args):
                sys.exit(__doc__)
            opts[flag] = args[i + 1]
            del args[i:i + 2]
    if len(args) != 3:
        sys.exit(__doc__)
    root, gpath, out = args
    genders = load_genders(gpath)
    old = load_old(out)
    files = txt_files(root)
    check_root(files, root)
    sections = read_play_order(opts.get('--order'), set(files))
    official = load_official(opts.get('--official'))

    info = {rel: analyze_records(read_records(os.path.join(root, rel))[0], genders) for rel in files}
    recs_by_id = {rel: sorted(read_records(os.path.join(root, rel))[0], key=lambda x: x['id']) for rel in files}
    base_keys = {rel: {i['key'].split('-')[0] for i in info[rel].values()} for rel in files}

    copy_cache = {}

    def is_copy(rel, master_rel):
        pair = (rel, master_rel)
        if pair not in copy_cache:
            copy_cache[pair] = (rel != master_rel and bool(base_keys[rel]) and
                                len(base_keys[rel] & base_keys[master_rel]) / len(base_keys[rel]) >= COPY_OVERLAP)
        return copy_cache[pair]

    table = []            # rows in table order: dicts with 'kind' = section / scene / text / ref
    master = {}           # key -> its text row
    master_file = {}      # key -> file of its text row

    def add_occurrence(row, i, r, rel):
        row['count'] += 1
        row['speakers'][i['speaker']] += 1
        if i['listener']:
            row['listeners'][i['listener']] += 1
        if i['lg'] and i['how'] == 'nearby':
            row['guessed'] += 1

    def emit_file(rel, scene_title, refs):
        """Rows for one game file. Returns the rows (scene header first) or [] if nothing new to show."""
        rows = []
        last_key = None
        for r in recs_by_id[rel]:
            i = info[rel].get(r['id'])
            if not i:
                continue
            key = i['key']
            if key not in master:
                cores = i['cores']
                notes = []
                if len(cores) > 1:
                    notes.append(f'{len(cores)} lines: keep {len(cores) - 1} ¶')
                if any(re.search(r'\{[^{}]*\}|\^[^^]*\^|<[^<>]+>', c) for c in cores):
                    notes.append('keep markup inside')
                if 'credits' in rel:
                    notes.append('credits: people’s names stay in Latin')
                row = {'kind': 'text', 'key': key, 'english': escape_cell(LINE_SEP.join(cores)), 'ukrainian': '',
                       'speaker_gender': i['sg'], 'listener_gender': i['lg'], 'count': 0,
                       'speakers': collections.Counter(), 'listeners': collections.Counter(),
                       'first_seen': f"{rel}:{r['idx'] + 1}", 'notes': notes, 'guessed': 0}
                master[key], master_file[key] = row, rel
                rows.append(row)
            elif refs and key != last_key and not is_copy(rel, master_file[key]):
                rows.append({'kind': 'ref', 'master': master[key], 'english': master[key]['english'],
                             'speakers': i['speaker'], 'listeners': i['listener'] or '',
                             'first_seen': f"{rel}:{r['idx'] + 1}"})
            add_occurrence(master[key], i, r, rel)
            last_key = key
        if rows:
            name = rel.rsplit('/', 1)[-1].replace('_english.txt', '')
            rows.insert(0, {'kind': 'scene', 'english': scene_title or name, 'first_seen': rel})
        return rows

    for title, entries in sections:
        body = []
        for rel, scene_title in entries:
            body += emit_file(rel, scene_title, refs=True)
        if body:
            table.append({'kind': 'section', 'english': title})
            table += body
    noir = []
    for rel in sorted((f for f in files if not f.startswith('BM_')), key=file_order):
        noir += emit_file(rel, rel.rsplit('/', 1)[-1].replace('_english.txt', ''), refs=False)
    if noir:
        table.append({'kind': 'section', 'english': 'SHADOWS MODE — texts that exist only in Noir mode'})
        table += noir

    for n, row in enumerate(table, 2):            # Excel row number (row 1 = column titles)
        row['row'] = n
    texts = [r for r in table if r['kind'] == 'text']

    first_loose = {}
    for row in texts:
        lk = (loose_text(row['english']), row['speaker_gender'], row['listener_gender'])
        if lk[0] and lk in first_loose:
            row['notes'].append(f"same as row #{first_loose[lk]} (almost)")
        else:
            first_loose.setdefault(lk, row['row'])

    # keep what people typed: same key; or, after a gender change, the same text's earlier version
    def parts(k):
        m = re.match(r'^([0-9a-f]+)(?:-S([MF?]))?(?:-L([MF?]))?$', k)
        return (m.group(1), m.group(2) or '', m.group(3) or '') if m else (k, '', '')

    def has_work(v):
        return v.get('ukrainian') or v.get('translator_notes')
    old_by_hash = collections.defaultdict(list)
    for k, v in old.items():
        if has_work(v):
            old_by_hash[parts(k)[0]].append((k, v))
    used_old = set()
    kept = 0
    for row in texts:
        key = row['key']
        if key in old and has_work(old[key]):
            row['ukrainian'] = old[key].get('ukrainian', '')
            row['translator_notes'] = old[key].get('translator_notes', '')
            used_old.add(key)
            kept += bool(row['ukrainian'])
        else:
            h, sg, lg = parts(key)
            for ok, ov in old_by_hash.get(h, []):
                if ok in master:
                    continue      # that row still exists with its own translation: nothing moved, copy nothing
                _, osg, olg = parts(ok)
                if osg in ('?', '', sg) and olg in ('?', '', lg) or sg in ('?', '') and lg in ('?', ''):
                    row['ukrainian'] = ov.get('ukrainian', '')
                    row['translator_notes'] = ov.get('translator_notes', '')
                    row['notes'].append(f'translation taken from {ok} - check gender forms')
                    used_old.add(ok)
                    kept += bool(row['ukrainian'])
                    break
        if official is not None:
            n = official['counts'].get(parts(key)[0], 0)
            total = official['total']
            row['official'] = f"{'yes' if n == total else 'no' if n == 0 else 'some'} {n}/{total}"
        if row['guessed']:
            row['notes'].append('listener guessed - check scene')
        row['speakers'] = ', '.join(s for s, _ in row['speakers'].most_common(4))
        row['listeners'] = ', '.join(s for s, _ in row['listeners'].most_common(3))
        row['notes'] = '; '.join(row['notes'])

    ucol = table_column_letter('ukrainian')
    for row in table:
        if row['kind'] == 'ref':
            m = row.pop('master')['row']
            row['ukrainian'] = f'=IF({ucol}{m}="","",{ucol}{m})'
            row['notes'] = f'see row #{m}'

    try:
        write_table(out, table)
    except PermissionError:
        sys.exit(f'Cannot write {out} - close it in Excel / LibreOffice first.')
    lost = [k for k, v in old.items() if has_work(v) and k not in master and k not in used_old]
    lost_path = re.sub(r'(\.\w+)$', r'.lost\1', out)
    if lost:
        write_table(lost_path, [dict(old[k], kind='text') for k in lost])
    words = sum(len(unescape_cell(r['english']).split()) for r in texts)
    n_ref = sum(1 for r in table if r['kind'] == 'ref')
    n_notes = sum(1 for r in texts if r.get('translator_notes'))
    print(f'{len(texts)} texts to translate ({words} English words) + {n_ref} reference rows -> {out}. '
          f'Kept {kept} existing translation(s)' + (f' and {n_notes} translator note(s).' if n_notes else '.'))
    if opts.get('--unique-original'):
        d = opts['--unique-original']
        files_u, _ = unique_files(root)
        nfiles = write_unique(files_u, d)
        print(f'Wrote the unique English texts into {nfiles} file(s) in {d} (built from {root} only; '
              f'it changes only if the English files change - check with: git status {d}).')
    if lost:
        print(f'WARNING: {len(lost)} translated row(s) no longer match any text - saved to {lost_path}')


if __name__ == '__main__':
    main()
