"""Write analysis/speakers.md (ти/ви decision sheet) from analysis/pairs.tsv and speaker_stats.tsv.
Usage: python analysis/tools/make_speakers_md.py   (run from the repo root after speakers.py)"""
import collections
import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = collections.Counter()
with open('analysis/pairs.tsv', encoding='utf-8-sig') as fh:
    for r in csv.DictReader(fh, delimiter='\t', quoting=csv.QUOTE_NONE):
        a = r['speaker'].replace('BRUCE/BATMAN (choice)', 'BRUCE')
        P[(a, r['listener'])] += int(r['lines'])
ALIASES = {'BRUCE': ['BRUCE'], 'BATMAN': ['BATMAN', 'BATMANBRUCE'],
           'REPORTERS': ['REPORTER01', 'REPORTER02', 'REPORTER03', 'REPORTER04', 'REPORTER05', 'RAMARQUE', 'SPENCER']}


def n(a, b):
    return sum(P[(x, y)] for x in ALIASES.get(a, [a]) for y in ALIASES.get(b, [b]))


LABEL = {'BRUCE': 'Bruce', 'BATMAN': 'Batman', 'VICKI': 'Vicki', 'SELINA': 'Selina', 'GORDON': 'Gordon',
         'HARVEY': 'Harvey', 'ALFRED': 'Alfred', 'MONTOYA': 'Montoya', 'LADYARKHAM': 'Lady Arkham',
         'CATWOMAN': 'Catwoman', 'HILL': 'Mayor Hill', 'OSWALD': 'Oswald', 'PENGUIN': 'Penguin',
         'FALCONE': 'Falcone', 'LUCIUS': 'Lucius', 'LELAND': 'Dr. Leland', 'REGINA': 'Regina',
         'JOKER': 'John Doe / Joker', 'REPORTERS': 'reporters'}

# (A, B, A->B suggestion, B->A suggestion, note)
SPEC = [
    ('ALFRED', 'BRUCE', 'ви', 'ти', 'butler who raised him: "Master Bruce", "sir" one way; family the other way'),
    ('ALFRED', 'BATMAN', 'ви', 'ти', 'same as above'),
    ('HARVEY', 'BRUCE', 'ти', 'ти', 'best friends; keep ти when Two-Face turns on Bruce (ep. 4–5)'),
    ('HARVEY', 'BATMAN', 'ви', 'ви', 'strangers; Two-Face → Batman may switch to ти (hostile)'),
    ('SELINA', 'BRUCE', 'ти', 'ти', 'optional ви in their very first meeting (ep. 1); close and flirty after'),
    ('CATWOMAN', 'BATMAN', 'ти', 'ти', 'rivals, then partners'),
    ('GORDON', 'BRUCE', 'ви', 'ви', '"Mr. Wayne" / "Lieutenant"'),
    ('GORDON', 'BATMAN', 'ти', 'ти', 'gruff cop and vigilante, allies; ви also works if you want Gordon formal'),
    ('LUCIUS', 'BRUCE', 'ви', 'ви', 'older employee, mutual respect'),
    ('LUCIUS', 'BATMAN', 'ви', 'ви', ''),
    ('VICKI', 'BRUCE', 'ви', 'ви', 'ви in public (press conference); ти in private once they get close — decide per scene'),
    ('VICKI', 'BATMAN', 'ви', 'ви', 'reporter and vigilante'),
    ('LADYARKHAM', 'BATMAN', 'ти', 'ти', 'enemies'),
    ('OSWALD', 'BRUCE', 'ти', 'ти', 'childhood friends ("mate", "Oz"); stays ти when they become enemies'),
    ('OSWALD', 'BATMAN', 'ти', 'ти', 'enemies'),
    ('PENGUIN', 'BATMAN', 'ти', 'ти', ''),
    ('JOKER', 'BRUCE', 'ти', 'ти', 'John is over-familiar ("Brucie", "pal")'),
    ('HILL', 'BRUCE', 'ви', 'ви', 'Hill may drop to ти when he gets nasty'),
    ('HILL', 'BATMAN', 'ви', 'ти', 'terrified mayor; Batman interrogates him'),
    ('FALCONE', 'BRUCE', 'ти', 'ви', 'old mob boss patronises "the kid"; Bruce stays polite'),
    ('MONTOYA', 'BRUCE', 'ви', 'ви', ''),
    ('MONTOYA', 'BATMAN', 'ти', 'ви', 'she arrests him; he stays cold-polite'),
    ('LELAND', 'BRUCE', 'ви', 'ви', 'doctor and patient'),
    ('REGINA', 'BRUCE', 'ви', 'ви', 'high society'),
    ('REPORTERS', 'BRUCE', 'ви', 'ви', 'REPORTER01–05, RAMARQUE, SPENCER'),
    ('HARVEY', 'VICKI', 'ви', 'ви', ''),
    ('HARVEY', 'SELINA', 'ти', 'ти', 'they date'),
    ('HARVEY', 'GORDON', 'ви', 'ви', 'D.A. and lieutenant'),
    ('HARVEY', 'ALFRED', 'ви', 'ви', ''),
    ('GORDON', 'MONTOYA', 'ти', 'ви', 'boss and officer'),
    ('LADYARKHAM', 'CATWOMAN', 'ти', 'ти', ''),
    ('OSWALD', 'REGINA', 'ви', 'ви', 'business'),
]

unknown = []
with open('analysis/speaker_stats.tsv', encoding='utf-8-sig') as fh:
    for r in csv.DictReader(fh, delimiter='\t', quoting=csv.QUOTE_NONE):
        if r['gender'] == '?' and int(r['lines_where_speaker_gender_matters']) > 0:
            unknown.append(f"{r['speaker']} ({r['lines_where_speaker_gender_matters']})")

out = [
    '# Speakers, gender and ти/ви — Batman S1 (Ukrainian)', '',
    'Files in `analysis/`:',
    '- `speaker_genders.xlsx` — gender of every speaker ID (M/F/?). **Edit it**, then rebuild the translation table.',
    '- `speaker_stats.tsv` — lines per speaker, and how many need the speaker’s / listener’s gender in Ukrainian.',
    '- `pairs.tsv` — every speaker → listener pair with line counts and examples.',
    '- `translation_table.xlsx` — one row per unique text to translate.',
    '- `scenes/` — read-only views of every file sorted by record number (conversation order).', '',
    'How the listener is guessed: a `[to Alfred]` note, else a name used in direct address ("Alfred, …"), else the',
    'most frequent other speaker within 3 records. Only about 10% of lines are found by note or name; the rest are',
    'from neighbours, so treat it as a strong hint. Choice options are spoken by Bruce/Batman.', '',
    '## Speakers whose gender is unknown but matters', '',
    'Number = lines where their gender changes the Ukrainian text. Listen in game, then set M/F in',
    '`speaker_genders.xlsx` and rebuild the table (existing translations are kept, marked "check gender forms"):', '',
    ', '.join(unknown), '',
    '## ти/ви (suggestions — confirm or change in the last column)', '',
    'General rules: **talking to several people = ви** (plural), whatever the table says. Strangers, staff, police,',
    'reporters, nurses ↔ Bruce: ви. Batman ↔ thugs and criminals: ти. Batman → ordinary adults (hostages,',
    'workers): ви; → children: ти. Wayne parents ↔ young Bruce: ти.', '',
    '| Speaker → listener | lines | suggested | Reverse | lines | suggested | Notes | Your decision |',
    '|---|---|---|---|---|---|---|---|']
for a, b, s1, s2, note in SPEC:
    out.append(f'| {LABEL[a]} → {LABEL[b]} | {n(a, b)} | **{s1}** | {LABEL[b]} → {LABEL[a]} | {n(b, a)} | '
               f'**{s2}** | {note} | |')
with open('analysis/speakers.md', 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(out) + '\n')
print('\n'.join(out[-6:]))
