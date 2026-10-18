"""Build translated Shadows/Noir (BAT_*) files from a finished default-mode (BM_*) translation.

Usage:
  python sync_noir.py --en EN_ROOT --tr TR_ROOT --out OUT_ROOT [--report todo.txt]

  EN_ROOT  folder with the original English BM_* and BAT_* folders (this repo)
  TR_ROOT  folder with your translated BM_* folders (same relative paths as in EN_ROOT)
  OUT_ROOT where translated BAT_* folders are written (structure copied 1:1 from English BAT files)

For every BAT record, in this order:
  1. same episode + same file name + same id in BM, and identical English text -> that translation
  2. identical English text anywhere else in BM -> most common translation of it (marked "reused")
  3. no letters outside markup (empty, "...", only an icon) -> copied from the English BAT file
  4. otherwise the English text is kept and the record is listed in the report as NEEDS TRANSLATION
Headers, line counts, BOM and CRLF always come from the English BAT file, so output structure is exact.
"""
import argparse
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landb_txt import exists, read_records, txt_files, write_lines  # noqa: E402


def group_key(rel):
    folder, name = rel.split('/')[0], rel.split('/')[-1]
    m = re.search(r'(10[1-5])', folder)
    if m:
        grp = m.group(1)
    else:
        grp = next((g for g in ('Menu', 'Boot', 'Project') if g in folder), folder)
    return grp, name


MARKUP = re.compile(r'\{[^{}]*\}|\^[^^]*\^|<<[^<>]*>>|<[^<>]+>')


def has_text(body):
    """Letters outside {..} ^..^ <..> markup. [..] counts as text: bracket-only choices are shown in game."""
    return any(any(c.isalpha() for c in MARKUP.sub('', l)) for l in body)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--en', required=True)
    ap.add_argument('--tr', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--report', default=None, help='where to write the to-do list (default OUT/noir_todo.txt)')
    ap.add_argument('--default-prefix', default='BM_')
    ap.add_argument('--noir-prefix', default='BAT_')
    a = ap.parse_args()

    by_id, by_text = {}, collections.defaultdict(collections.Counter)
    skipped_bad = 0
    for rel in txt_files(a.en):
        if not rel.startswith(a.default_prefix):
            continue
        tr_path = os.path.join(a.tr, rel)
        if not exists(tr_path):
            continue
        en_recs = {r['id']: r for r in read_records(os.path.join(a.en, rel))[0]}
        for r in read_records(tr_path)[0]:
            e = en_recs.get(r['id'])
            if not e or len(e['body']) != len(r['body']):
                skipped_bad += 1
                continue
            en_body, tr_body = tuple(e['body']), tuple(r['body'])
            by_id[group_key(rel) + (r['id'],)] = (en_body, tr_body)
            if tr_body != en_body:
                by_text[en_body][tr_body] += 1

    todo, stats = [], collections.Counter()
    for rel in txt_files(a.en):
        if not rel.startswith(a.noir_prefix):
            continue
        recs, pre, _, _ = read_records(os.path.join(a.en, rel))
        out = list(pre)
        for r in recs:
            body = tuple(r['body'])
            hit = by_id.get(group_key(rel) + (r['id'],))
            if hit and hit[0] == body:
                new, how = hit[1], 'same id'
            elif body in by_text:
                new, how = by_text[body].most_common(1)[0][0], 'reused'
            elif not has_text(body):
                new, how = body, 'copied'
            else:
                new, how = body, 'todo'
                todo.append((rel, r['idx'] + 1, r['hdr'], body))
            stats[how] += 1
            out.append(r['hdr'])
            out.extend(new)
        write_lines(os.path.join(a.out, rel), out)

    report = a.report or os.path.join(a.out, 'noir_todo.txt')
    with open(report, 'w', encoding='utf-8-sig', newline='\r\n') as fh:
        fh.write(f'{len(todo)} Noir record(s) still in English - translate them in the files under {a.out}\n\n')
        for rel, ln, hdr, body in todo:
            fh.write(f'{rel}:{ln}  {hdr}\n')
            for l in body:
                fh.write(f'    {l}\n')
    print(f"Records: {stats['same id']} same id, {stats['reused']} reused by text, {stats['copied']} copied "
          f"(no letters), {stats['todo']} NEED TRANSLATION. Skipped {skipped_bad} broken BM record(s).")
    print(f'To-do list: {report}')


if __name__ == '__main__':
    main()
