"""Speaker / listener statistics for Ukrainian gender and ти/ви decisions (default-mode BM_* files).

Usage: python .claude/skills/telltale-batman-localization/scripts/speakers.py ROOT GENDERS_TSV OUT_DIR
Writes OUT_DIR/speaker_stats.tsv and OUT_DIR/pairs.tsv.
Uses the same listener guessing as the translation table (tm_lib.py).
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landb_txt import read_records, txt_files  # noqa: E402
from tm_lib import LISTENER_GENDERED, SPEAKER_GENDERED, analyze_records, load_genders, spoken  # noqa: E402

root, gpath, out = sys.argv[1:4]
genders = load_genders(gpath)
stats = collections.defaultdict(collections.Counter)
eps = collections.defaultdict(set)
ex = {}
pairs = collections.Counter()
how = collections.defaultdict(collections.Counter)
pex = collections.defaultdict(list)
for rel in txt_files(root):
    if not rel.startswith('BM_'):
        continue
    ep = re.search(r'(10\d|Menu|Boot|Project)', rel).group(1)
    for rid, i in analyze_records(read_records(os.path.join(root, rel))[0], genders).items():
        s = i['speaker']
        text = spoken(' '.join(i['cores'])).strip()
        st = stats[s]
        st['lines'] += 1
        eps[s].add(ep)
        if SPEAKER_GENDERED.search(text):
            st['speaker_gendered'] += 1
            ex.setdefault(s, text[:100])
        if LISTENER_GENDERED.search(text):
            st['listener_gendered'] += 1
        sp = 'BRUCE/BATMAN (choice)' if s == 'choice/UI' else s
        if i['listener']:
            pairs[(sp, i['listener'])] += 1
            how[(sp, i['listener'])][i['how']] += 1
            if len(pex[(sp, i['listener'])]) < 3 and len(text) > 20 and re.search(r'\byou', text, re.I):
                pex[(sp, i['listener'])].append(text[:90])

os.makedirs(out, exist_ok=True)
with open(os.path.join(out, 'speaker_stats.tsv'), 'w', encoding='utf-8-sig', newline='\r\n') as fh:
    fh.write('speaker\tgender\tlines\tlines_where_speaker_gender_matters\tlines_where_listener_gender_matters'
             '\tepisodes\texample\n')
    for s, st in sorted(stats.items(), key=lambda x: -x[1]['lines']):
        g = 'M (Bruce)' if s == 'choice/UI' else genders.get(s, 'not in genders file')
        fh.write(f"{s}\t{g}\t{st['lines']}\t{st['speaker_gendered']}\t{st['listener_gendered']}\t"
                 f"{','.join(sorted(eps[s]))}\t{ex.get(s, '')}\n")
with open(os.path.join(out, 'pairs.tsv'), 'w', encoding='utf-8-sig', newline='\r\n') as fh:
    fh.write('speaker\tlistener\tlines\tby_note\tby_name\tby_neighbour\texamples_with_you\n')
    for (a, b), n in pairs.most_common():
        h = how[(a, b)]
        fh.write(f"{a}\t{b}\t{n}\t{h['note']}\t{h['name']}\t{h['nearby']}\t{' | '.join(pex[(a, b)])}\n")
print(f'{len(stats)} speakers, {len(pairs)} speaker->listener pairs -> {out}')
