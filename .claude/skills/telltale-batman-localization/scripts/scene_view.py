"""Write read-only "script views" of landb .txt files: records sorted by record number, which is the
order the lines were written in, so each conversation reads together. File order only groups identical lines.

Usage:
  python scene_view.py SOURCE_ROOT OUT_DIR [--prefix BM_] [--markup]

Each output line:  L<line in real file>  <id>  <SPEAKER or "> choice/UI">  <text>
{..} ^..^ <..> markup is hidden unless --markup; [..] notes are kept because they explain tone.
Empty records are skipped. Never import these views - edit the real files.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landb_txt import read_records, txt_files, write_lines  # noqa: E402

HIDE = re.compile(r'\{[^{}]*\}|\^[^^]*\^|<<[^<>]*>>|<[^<>]+>')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('source')
    ap.add_argument('out')
    ap.add_argument('--prefix', default='BM_', help='only folders starting with this (default BM_; "" = all)')
    ap.add_argument('--markup', action='store_true', help='keep {..} ^..^ <..> markup visible')
    a = ap.parse_args()

    count = 0
    for rel in txt_files(a.source):
        if not rel.startswith(a.prefix):
            continue
        recs = sorted(read_records(os.path.join(a.source, rel))[0], key=lambda r: r['id'])
        out = [f'# {rel} - sorted by record number. READ-ONLY view, edit the real file (L = its line).', '']
        for r in recs:
            body = [l if a.markup else HIDE.sub('', l) for l in r['body']]
            if not any(l.strip() for l in body):
                continue
            who = r['spk'] or '> choice/UI'
            pad = ' ' * (len(f"L{r['idx'] + 1:<6} {r['id']:>5}  {who:<14} "))
            out.append(f"L{r['idx'] + 1:<6} {r['id']:>5}  {who:<14} {body[0]}")
            out.extend(pad + l for l in body[1:])
        write_lines(os.path.join(a.out, rel), out)
        count += 1
    print(f'Wrote {count} view(s) to {a.out}')


if __name__ == '__main__':
    main()
