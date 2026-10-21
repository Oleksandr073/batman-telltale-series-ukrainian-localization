"""Put the Ukrainian choice-statistics texts into ChoiceStats.lua - taken from the translation table.

The end-of-episode choices screen ("You and 67.1% of players...") does not use landb files: its texts come from
Telltale's server in 9 languages. The game passes every one of them through ChoiceStats_LocalizeText() in
ChoiceStats.lua. The same texts also exist in the game file BM_pc_Project_data/stats_english.txt, which is part of
translation_table.xlsx - so they are translated there, once, like every other text. This script:
  1. reads the English and the imported Ukrainian stats_english.txt (`npm run import` writes the Ukrainian one),
  2. maps every translated text English -> Ukrainian (style tags like ^glyphScale:1.1^ at the start removed),
  3. writes localized_script/choice_stats_english.txt (the 133 server texts in Ukrainian, for review with git diff),
  4. writes localized_script/ChoiceStats.lua = the original script + a block with those 133 texts. The live
     percentage from the server is kept.
The screen (getWorldChoices in Menu_Stats.lua) shows only the choices the server sends: 26 choices, 133 unique texts
(server data of 2017-03-28), all of them in stats_english.txt. The other ~190 texts of stats_english.txt are unused
candidate choices and are left out of the script.

Usage (from the repo root):
  python apply_choice_stats.py CHOICE_DIR STATS_EN STATS_UA
  e.g. choice_stats_data data/original_data/BM_pc_Project_data/stats_english.txt
       data/localized_data/BM_pc_Project_data/stats_english.txt

Folder layout:
  CHOICE_DIR/original_script/ChoiceStats.lua            decompiled game script - never edited
  CHOICE_DIR/original_script/choice_stats_english.txt   the 133 English server texts - never edited
  CHOICE_DIR/localized_script/choice_stats_english.txt  WRITTEN by this script (translate in the table, not here)
  CHOICE_DIR/localized_script/ChoiceStats.lua           WRITTEN by this script (= original + Ukrainian block)

{percent} stands for the number from the server. A text that is still English stays English in game. With nothing
translated, both outputs equal the originals. Exit code 1 on any error; nothing is written then.
"""
import os
import re
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landb_txt import parse_lines, read_raw, split_lines, write_lines  # noqa: E402
from validate import check_pair  # noqa: E402

TXT = 'choice_stats_english.txt'
LUA = 'ChoiceStats.lua'
MARK_BEGIN = '-- ===== Ukrainian choice statistics (added by apply_choice_stats.py) ====='
MARK_END = '-- ===== end of Ukrainian choice statistics ====='
STYLE_PREFIX = re.compile(r'^(?:\^[A-Za-z]+:[^^]*\^)+')     # ^glyphScale:1.1^^font:..^^color:#24c246^ at the start

# Lua code added after the original script. %TABLE% = the English -> Ukrainian lines.
LUA_BLOCK = r'''
MARK_BEGIN
local kChoiceTextUA = {
%TABLE%
}

-- Server text: "<style tags>You and 67.1%^^ of players ...".
-- Returns the style tags, the text with the numbers replaced by {percent}, and the numbers.
local uaSplit = function(text)
  local s = string.match(text, "^%s*(.-)%s*$")
  local body = s
  while true do
    local rest = string.match(body, "^%^%a+:[^%^]*%^(.*)$")
    if not rest then
      break
    end
    body = rest
  end
  local prefix = string.sub(s, 1, string.len(s) - string.len(body))
  body = string.match(body, "^%s*(.-)%s*$")
  local numbers = {}
  local key = string.gsub(body, "(%d+%.?%d*)(%s?%%)", function(n, pct)
    table.insert(numbers, n)
    return "{percent}" .. pct
  end)
  return prefix, key, numbers
end

function ChoiceStats_TranslateUA(text)
  if type(text) ~= "string" or text == "" then
    return nil
  end
  local prefix, key, numbers = uaSplit(text)
  local ua = kChoiceTextUA[key]
  if not ua then
    return nil
  end
  local i = 0
  ua = string.gsub(ua, "{percent}", function()
    i = i + 1
    return numbers[i] or ""
  end)
  return prefix .. ua
end

-- Keep the game's function and call it for every text without a translation.
local ChoiceStats_LocalizeText_Original = ChoiceStats_LocalizeText
function ChoiceStats_LocalizeText(props)
  if props then
    local ok, english = pcall(PropertyGet, props, "English")
    if ok then
      local ua = ChoiceStats_TranslateUA(english)
      if ua then
        return ua
      end
    end
  end
  return ChoiceStats_LocalizeText_Original(props)
end
MARK_END
'''.replace('MARK_BEGIN', MARK_BEGIN).replace('MARK_END', MARK_END)


def fail(msg):
    print(f'ERROR: {msg}')
    print('Nothing was written.')
    sys.exit(1)


def lua_string(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def strip_style(text):
    """The text without the leading style tags - the form ChoiceStats.lua matches (see uaSplit)."""
    return STYLE_PREFIX.sub('', text.strip()).strip()


def read_texts(path):
    """Return {id: text} from a txt file with 1 text line per record."""
    lines, _ = split_lines(read_raw(path))
    recs, pre = parse_lines(lines)
    if pre:
        fail(f'{path}: text before the first "N) " header')
    texts = {}
    for r in recs:
        if len(r['body']) != 1:
            fail(f'{path}: record {r["id"]} must have exactly 1 text line, has {len(r["body"])}')
        texts[r['id']] = r['body'][0]
    return texts


def translations(stats_en, stats_ua):
    """-> ({English without style tags: Ukrainian without style tags}, [conflict messages])."""
    en, ua = read_texts(stats_en), read_texts(stats_ua)
    if set(en) != set(ua):
        fail(f'{stats_ua} has other records than {stats_en} - run `npm run import` first')
    out, conflicts = {}, []
    for rid, e in en.items():
        u = ua[rid]
        if u == e:
            continue
        ke, ku = strip_style(e), strip_style(u)
        if not ke or not ku:
            continue
        pe, pu = STYLE_PREFIX.match(e.strip()), STYLE_PREFIX.match(u.strip())
        if (pe.group(0) if pe else '') != (pu.group(0) if pu else ''):
            fail(f'{stats_ua}: record {rid}: style tags at the start differ from the English')
        if ke.count('{percent}') != ku.count('{percent}'):
            fail(f'{stats_ua}: record {rid}: {{percent}} count differs from the English')
        if ke in out and out[ke] != ku:
            conflicts.append(f'  "{ke[:60]}": "{out[ke][:40]}" / "{ku[:40]}" (record {rid}) - the first one is used')
            continue
        out[ke] = ku
    return out, conflicts


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    root, stats_en, stats_ua = sys.argv[1:]
    orig_dir = os.path.join(root, 'original_script')
    loc_dir = os.path.join(root, 'localized_script')
    orig_lua = os.path.join(orig_dir, LUA)
    orig_txt = os.path.join(orig_dir, TXT)
    loc_txt = os.path.join(loc_dir, TXT)
    out_lua = os.path.join(loc_dir, LUA)
    for p in (orig_lua, orig_txt, stats_en, stats_ua):
        if not os.path.isfile(p):
            fail(f'missing file: {p}')

    raw_lua = read_raw(orig_lua)
    if raw_lua.startswith(b'\x1bLua'):
        fail(f'{orig_lua} is compiled Lua; it must be the decompiled text script')
    lua = raw_lua.decode('utf-8')
    if MARK_BEGIN in lua:
        fail(f'{orig_lua} already contains the Ukrainian block; put the untouched decompiled script there')
    if 'function ChoiceStats_LocalizeText(' not in lua:
        fail(f'{orig_lua} has no ChoiceStats_LocalizeText function - wrong script?')

    tr, conflicts = translations(stats_en, stats_ua)

    # the localized choice txt = the original one with each known server text replaced (for review)
    known = set(read_texts(orig_txt).values())
    lines, _ = split_lines(read_raw(orig_txt))
    out_lines, n_known = [], 0
    for line in lines:
        if line in known and line.strip() in tr:
            out_lines.append(tr[line.strip()])
            n_known += 1
        else:
            out_lines.append(line)
    os.makedirs(loc_dir, exist_ok=True)
    tmp_txt = loc_txt + '.new'
    write_lines(tmp_txt, out_lines)
    # the same checks as validate.py for the game files: BOM, CRLF, headers, line count, markup ({percent}, ^^)
    report = []
    errs, warns, _ = check_pair(orig_txt, tmp_txt, TXT, report,
                                types.SimpleNamespace(show=50, untranslated=False, verbose=False))
    if report:
        print('\n'.join(report))
    if errs:
        os.remove(tmp_txt)
        fail(f'{errs} error(s) in the Ukrainian choice texts (see above) - fix them in the table')
    os.replace(tmp_txt, loc_txt)

    # only the texts the server sends can reach the screen: the other stats_english.txt texts are left out
    shown = {en: ua for en, ua in tr.items() if en in {k.strip() for k in known}}
    eol = '\r\n' if '\r\n' in lua else '\n'
    if shown:
        table = '\n'.join(f'  [{lua_string(en)}] = {lua_string(ua)},' for en, ua in sorted(shown.items()))
        block = LUA_BLOCK.replace('%TABLE%', table).replace('\n', eol)
        body = lua.rstrip('\r\n') + eol + block
    else:
        body = lua
    with open(out_lua, 'wb') as fh:
        fh.write(body.encode('utf-8'))
    for c in conflicts:
        print('WARNING: one English text, two translations:\n' + c)
    print(f'{len(shown)} of {len(known)} choice-screen texts translated (taken from {stats_ua}), '
          f'{warns} warning(s), 0 errors.')
    print(f'Written: {loc_txt}\nWritten: {out_lua}')


if __name__ == '__main__':
    main()
