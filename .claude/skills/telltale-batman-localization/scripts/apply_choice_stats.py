"""Put the Ukrainian choice-statistics texts into ChoiceStats.lua.

The end-of-episode choices screen ("You and 67.1% of players...") does not use landb files: its texts come from
Telltale's server in 9 languages. The game passes every one of them through ChoiceStats_LocalizeText() in
ChoiceStats.lua. This script appends a block to that script which replaces the English server text with the
Ukrainian from the translated txt. The live percentage from the server is kept.

Usage (from the repo root):
  python apply_choice_stats.py choice_stats_data

Folder layout:
  choice_stats_data/original_script/ChoiceStats.lua            decompiled game script - never edited
  choice_stats_data/original_script/choice_stats_english.txt   English texts - never edited
  choice_stats_data/localized_script/choice_stats_english.txt  the same file, translated
  choice_stats_data/localized_script/ChoiceStats.lua           WRITTEN by this script (= original + Ukrainian block)

The txt files use the game txt format ("N) " header + 1 text line, UTF-8 with BOM, CRLF). {percent} stands for the
number from the server; keep it and the % after it. ^^ ends the coloured part (green/red), keep it after {percent}%.
A text that is still English stays English in game. With nothing translated, the output equals the original script.
Exit code 1 on any error; nothing is written then.
"""
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landb_txt import parse_lines, read_raw, split_lines  # noqa: E402
from validate import check_pair  # noqa: E402

TXT = 'choice_stats_english.txt'
LUA = 'ChoiceStats.lua'
MARK_BEGIN = '-- ===== Ukrainian choice statistics (added by apply_choice_stats.py) ====='
MARK_END = '-- ===== end of Ukrainian choice statistics ====='

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


def read_texts(path):
    """Return {id: text} from a choice txt file (1 text line per record)."""
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


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    root = sys.argv[1]
    orig_dir = os.path.join(root, 'original_script')
    loc_dir = os.path.join(root, 'localized_script')
    orig_lua = os.path.join(orig_dir, LUA)
    orig_txt = os.path.join(orig_dir, TXT)
    loc_txt = os.path.join(loc_dir, TXT)
    out_lua = os.path.join(loc_dir, LUA)
    for p in (orig_lua, orig_txt, loc_txt):
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

    # Same checks as validate.py for the game files: BOM, CRLF, headers, line count, markup ({percent}, ^^).
    report = []
    errs, warns, _ = check_pair(orig_txt, loc_txt, TXT, report,
                                types.SimpleNamespace(show=50, untranslated=False, verbose=False))
    if report:
        print('\n'.join(report))
    if errs:
        fail(f'{errs} error(s) in {loc_txt} (see above)')

    english = read_texts(orig_txt)
    ukrainian = read_texts(loc_txt)
    pairs = []
    for rid, en in english.items():
        ua = ukrainian[rid]
        if ua.strip() and ua != en:
            if en.count('{percent}') != ua.count('{percent}'):
                fail(f'record {rid}: {{percent}} count differs from the English')
            pairs.append((en.strip(), ua.strip()))

    eol = '\r\n' if '\r\n' in lua else '\n'
    if pairs:
        table = '\n'.join(f'  [{lua_string(en)}] = {lua_string(ua)},' for en, ua in pairs)
        block = LUA_BLOCK.replace('%TABLE%', table).replace('\n', eol)
        body = lua.rstrip('\r\n') + eol + block
    else:
        body = lua
    with open(out_lua, 'wb') as fh:
        fh.write(body.encode('utf-8'))
    print(f'{len(pairs)} of {len(english)} texts translated, {warns} warning(s), 0 errors.')
    print(f'Written: {out_lua}')


if __name__ == '__main__':
    main()
