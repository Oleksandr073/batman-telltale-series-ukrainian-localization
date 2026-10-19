"""Shared logic for the translation table (build_tm.py) and putting translations back (apply_translations.py).

Core text: each text line is split into  prefix + core + suffix.
  prefix = leading {tags} and [notes] (e.g. "{AngryA}[pickup][ALT]"), copied back untouched;
  core   = what the translator translates (mid-line tags stay inside it);
  suffix = trailing spaces/tabs.
  A line that is only brackets ("[Ignore]", "[sighs]") keeps its brackets in the core.

Ukrainian gender: a core is split into separate table rows by speaker gender when it has first-person
past tense / "I'm sure"-type words, and by listener gender when it has "you" + past tense / adjective.
Speaker gender comes from analysis/speaker_genders.tsv; the listener is guessed (see guess_listeners).
"""
import collections
import hashlib
import re

NOTE = re.compile(r'^\(\w[\w .]*, \w{3} \w{3}')          # writers' timestamped notes
MARKUP = re.compile(r'\{[^{}]*\}|\^[^^]*\^|<<[^<>]*>>|<[^<>]+>')
PREFIX = re.compile(r'^(?:\s*(?:\{[^{}]*\}|\[[^\[\]]*\]))+\s*')
TAGS_ONLY_PREFIX = re.compile(r'^(?:\s*\{[^{}]*\})+\s*')
DEV_SPEAKER = re.compile(r'^(DIR|STUB|NOTES?|QUESTION|GAMEPLAY|CHANGED?|WRITING|VFX|QTE|FILE|HTTPS?|REF|TESTDIR)')
LINE_SEP = ' ¶ '                                         # joins lines of a multi-line record in the table

_IRREG = ('was|were|did|saw|made|had|went|got|told|said|thought|knew|found|left|took|gave|came|felt|kept|lost|'
          'met|heard|meant|brought|bought|caught|fought|forgot|forgave|ran|sat|stood|understood|wrote|became|'
          'began|broke|chose|drove|fell|flew|grew|hid|hit|hurt|let|put|read|rode|sent|shot|slept|spoke|spent|'
          'stole|swore|taught|threw|tried|won|woke|could|would')
_ADJ = ('sure|glad|sorry|ready|tired|afraid|happy|alone|wrong|right|done|busy|serious|grateful|curious|aware|'
        'late|free|alive|dead|crazy|drunk|innocent|guilty|proud|scared|worried|surprised|impressed|interested|'
        'disappointed|married|responsible|calm|safe|sick|honest|able|certain|positive|convinced|lucky|young|'
        'old|good|fine|okay|alright|new|mad|angry|upset|lonely|jealous|stupid|smart|strong|weak|hungry|awake')
_ADV = r'(?:just |never |already |really |always |only |even |also |not |so |very |too |quite |a little |still |all )*'
SPEAKER_GENDERED = re.compile(
    rf"\bI(?:’d|'d|’ve|'ve| had| have| would have)?\s+{_ADV}(?:\w+ed|{_IRREG})\b"
    rf"|\bI(?:’m|'m| am| was)\s+{_ADV}(?:{_ADJ}|\w+ed)\b|\bmyself\b", re.I)
LISTENER_GENDERED = re.compile(
    rf"\byou(?:’d|'d|’ve|'ve| had| have| would have)?\s+{_ADV}(?:\w+ed|{_IRREG})\b"
    rf"|\byou(?:’re|'re| are| were)\s+{_ADV}(?:{_ADJ}|\w+ed)\b|\b(?:did|were|have|had) you\b|\byourself\b", re.I)

ALIAS = {'BATMANBRUCE': 'BATMAN', 'DENT': 'HARVEY', 'HARBEY': 'HARVEY', 'RENEE': 'MONTOYA', 'JOE CHILL': 'JOECHILL'}
VOCATIVES = {
    'BRUCE': r'Bruce|Mr\. Wayne|Master Bruce|Master Wayne|Brucie|Wayne', 'BATMAN': r'Batman|Bats',
    'ALFRED': r'Alfred|Pennyworth', 'HARVEY': r'Harvey|Harv|Mr\. Dent|Dent|Mayor Dent',
    'SELINA': r'Selina|Ms\. Kyle|Miss Kyle|Kyle', 'CATWOMAN': r'Catwoman',
    'GORDON': r'Gordon|Jim|Lieutenant|Commissioner', 'OSWALD': r'Oswald|Oz|Ozzy|Cobblepot', 'PENGUIN': r'Penguin',
    'VICKI': r'Vicki|Ms\. Vale|Miss Vale', 'LUCIUS': r'Lucius|Mr\. Fox', 'FALCONE': r'Falcone|Carmine',
    'MONTOYA': r'Montoya|Renee', 'HILL': r'Mayor Hill|Hill|Mr\. Mayor', 'JOKER': r'John|Doe',
    'LELAND': r'Dr\. Leland|Leland|Doctor', 'LADYARKHAM': r'Lady Arkham', 'ZSASZ': r'Zsasz|Victor',
    'REGINA': r'Regina|Mrs\. Zellerbach'}
_VOC_RE = {k: re.compile(rf'(?:^|[,!?.]\s*|--\s*)(?:{v})(?:\s*[,!?.]|\s*--|\s*$)') for k, v in VOCATIVES.items()}
_TO_RE = re.compile(r'\[(?:[^\]]*;\s*)?to ([A-Za-z .’\-]+?)\s*[;\]]', re.I)


def load_genders(path):
    g = {}
    with open(path, encoding='utf-8-sig') as fh:
        next(fh)
        for line in fh:
            parts = line.rstrip('\r\n').split('\t')
            if len(parts) >= 2 and parts[0]:
                g[parts[0]] = parts[1].strip().upper() or '?'
    return g


def norm_speaker(s):
    return ALIAS.get(s, s)


def is_dev_record(rec):
    return bool(DEV_SPEAKER.match(rec['spk'])) or any(NOTE.match(l) for l in rec['body'][:1])


TRAILING_ALT = re.compile(r'\s*\[alt\b[^\[\]]*\]$', re.I)


def split_line(line):
    """-> (prefix, core, suffix)."""
    stripped = line.rstrip(' \t')
    suffix = line[len(stripped):]
    m = TRAILING_ALT.search(stripped)
    if m and stripped[:m.start()].strip():
        suffix = stripped[m.start():] + suffix
        stripped = stripped[:m.start()]
    m = PREFIX.match(stripped)
    if m and stripped[m.end():].strip():
        return stripped[:m.end()], stripped[m.end():], suffix
    m = TAGS_ONLY_PREFIX.match(stripped)           # only brackets left: keep them in the core
    if m and stripped[m.end():].strip():
        return stripped[:m.end()], stripped[m.end():], suffix
    return '', stripped, suffix


def has_letters(text):
    return any(c.isalpha() for c in MARKUP.sub('', text))


def spoken(text):
    return re.sub(r'\[[^\]]*\]', ' ', MARKUP.sub('', text))


def guess_listeners(recs):
    """recs sorted by id. Returns {id: (listener, how)} for records with a speaker (how = note/name/nearby).
    Records without a speaker (choices) are spoken by Bruce/Batman to the nearest other speaker."""
    seq = [(i, norm_speaker(r['spk'])) for i, r in enumerate(recs)
           if r['spk'] and not is_dev_record(r) and any(l.strip() for l in r['body'])]
    pos = {i: k for k, (i, _) in enumerate(seq)}
    out = {}
    for i, r in enumerate(recs):
        if is_dev_record(r):
            continue
        me = norm_speaker(r['spk']) if r['spk'] else 'BRUCE'
        text = MARKUP.sub('', ' '.join(r['body']))
        target, how = None, None
        m = _TO_RE.search(text)
        if m:
            name = re.sub(r'[^A-Z]', '', m.group(1).upper())
            for k, rx in VOCATIVES.items():
                alts = [re.sub(r'[^A-Z]', '', a.upper()) for a in rx.replace('\\.', '').split('|')]
                if name == k or name in alts:
                    target, how = k, 'note'
                    break
        if not target:
            sp = spoken(text)
            for k, rx in _VOC_RE.items():
                if k != me and rx.search(sp):
                    target, how = k, 'name'
                    break
        if not target:
            if i in pos:
                k0 = pos[i]
                near = [s for _, s in seq[max(0, k0 - 3):k0 + 4] if s != me]
            else:  # choice: look at speakers around it
                around = [s for j, s in seq if abs(j - i) <= 4 and s not in ('BRUCE', 'BATMAN')]
                near = around
            if near:
                target, how = collections.Counter(near).most_common(1)[0][0], 'nearby'
        out[r['id']] = (target, how)
    return out


def record_key(cores, speaker_gender, listener_gender):
    """Stable id of a table row. Gender parts are added only when the text needs them."""
    joined = '\n'.join(cores)
    sp = spoken(joined)
    sg = speaker_gender if SPEAKER_GENDERED.search(sp) else ''
    lg = listener_gender if LISTENER_GENDERED.search(sp) else ''
    h = hashlib.sha1(joined.encode('utf-8')).hexdigest()[:10]
    return h + (f'-S{sg}' if sg else '') + (f'-L{lg}' if lg else ''), sg, lg


def analyze_records(recs, genders):
    """recs: records of one file. Returns {id: info} for every record that belongs in the table.
    info = dict(cores, key, sg, lg, speaker, listener, how). Missing id = stays English (notes, no letters,
    subtitles that are only [sighs])."""
    by_id = sorted(recs, key=lambda r: r['id'])
    listeners = guess_listeners(by_id)
    out = {}
    for r in by_id:
        if is_dev_record(r):
            continue
        cores = [split_line(l)[1] for l in r['body']]
        if not has_letters(' '.join(cores)):
            continue
        if r['spk'] and not has_letters(re.sub(r'\[[^\[\]]*\]', '', ' '.join(cores))):
            continue
        spk = norm_speaker(r['spk']) if r['spk'] else 'BRUCE'
        lst, how = listeners.get(r['id'], (None, None))
        sg_all = genders.get(r['spk'], genders.get(spk, '?'))
        lg_all = genders.get(lst, '?') if lst else '?'
        key, sg, lg = record_key(cores, sg_all, lg_all)
        out[r['id']] = {'cores': cores, 'key': key, 'sg': sg, 'lg': lg,
                        'speaker': r['spk'] or 'choice/UI', 'listener': lst, 'how': how}
    return out


def split_translation(cell, n_lines):
    """Table cell -> list of n_lines core lines, or None if the ¶ count is wrong."""
    cell = unescape_cell(cell)
    if n_lines == 1:
        return [cell]
    parts = cell.split(LINE_SEP)               # exact " ¶ " keeps spaces inside lines
    if len(parts) != n_lines:
        parts = re.split(r' ?¶ ?', cell)       # editor trimmed a space somewhere
    return parts if len(parts) == n_lines else None


def loose_text(s):
    """Lower-case letters/digits only - for spotting near-identical rows."""
    s = re.sub(r'\{[^}]*\}|\[[^\]]*\]|\^[^^]*\^|<[^>]*>', '', s).replace('’', "'").lower()
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def escape_cell(s):
    return s.replace('\\', '\\\\').replace('\t', '\\t')


def unescape_cell(s):
    return re.sub(r'\\(\\|t)', lambda m: '\t' if m.group(1) == 't' else '\\', s)
