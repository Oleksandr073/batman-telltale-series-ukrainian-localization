"""Put the Telegram item into UI_Feed.lua (the news feed / carousel at the bottom left of the main menu, both modes).

The feed normally shows Telltale's news, downloaded from their server (feed.prop). This script writes a copy of the
game script in which our item is always first (the server items follow; arrows and the 9-second auto-cycle work as
before), is shown instead of the "offline" tile when the server feed can't be loaded, and opens a link on click
(PlatformOpenURL; on Steam the Steam overlay browser). The picture is ui_imageUATelegramFeed.d3dtx (QR code), made by
make_feed_texture.py. The header text is set directly in the script - it is not a landb text, so it is not in the
translation table.

Usage (from the repo root):
  python apply_feed_item.py FEED_DIR
  e.g. data/feed_item

Folder layout:
  FEED_DIR/feed_item.txt                    EDIT THIS: header text and link (+ picture settings, see make_feed_texture.py)
  FEED_DIR/original_script/UI_Feed.lua      decompiled game script - never edited
  FEED_DIR/localized_script/UI_Feed.lua     WRITTEN by this script (= original + the item)
  FEED_DIR/texture/ui_imageUATelegramFeed.d3dtx   the picture

The localized script is compiled (Lua 5.2 luac, outside this repo) and packed into BOTH BM_pc_Menu_data and
BAT_pc_PC_Noir_Menu_compressed; the picture into BOTH BM_pc_Menu_data and BAT_pc_BatmanNoirMenu_compressed
(BatmanNoirMenu is enabled only in Shadows mode). Tested in game, both modes, on 2026-11-13.
Exit code 1 on any error; nothing is written then.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from links import expand  # noqa: E402

LUA = 'UI_Feed.lua'
SETTINGS = 'feed_item.txt'
IMAGE = 'ui_imageUATelegramFeed.d3dtx'
MARK = '-- ===== Ukrainian localization: Telegram item'
MAX_HEADER = 32

ANCHOR_SETTINGS = 'local mbOffline = false\n'
ANCHOR_POPULATE = 'local feedPopulate = function(feedData)\n'
ANCHOR_INIT = ('  Widget.Initialize(self, name)\n'
               '  feedSetup()\n'
               '  mFeedWidget = self\n')

BLOCK_SETTINGS = r'''-- ===== Ukrainian localization: Telegram item in the main-menu feed (settings) =====
-- t.me/s/... = web view of the channel. Plain t.me/... shows an error page in the Steam overlay browser.
local kUAFeedURL = %URL%
local kUAFeedHeader = %HEADER%
local kUAFeedImage = "%IMAGE%" -- QR code picture, packed into BM_pc_Menu_data and BAT_pc_BatmanNoirMenu_compressed
-- ===== end of settings =====

function Feed_UA_OpenTelegram()
  PlatformOpenURL(kUAFeedURL)
end

-- type "lua": clicking runs data as Lua (see feedPopulate)
local kUAFeedItem = {
  id = "ua_telegram",
  type = "lua",
  header = kUAFeedHeader,
  text = "",
  icon = kUAFeedImage,
  data = "Feed_UA_OpenTelegram()",
  max_views = "infinite",
  show = true
}

-- put our item first: server items 0..n-1 become 1..n
local uaFeedAddItem = function()
  if mbOffline then
    return -- offline: feedPopulate(nil) shows our item instead of the "offline" tile
  end
  local items = {}
  items[0] = kUAFeedItem
  for i = 0, mNumItems - 1 do
    items[i + 1] = mFeedData[i]
  end
  mFeedData = items
  mNumItems = mNumItems + 1
end
-- ===== end of Ukrainian localization block =====
'''

BLOCK_POPULATE = '  feedData = feedData or kUAFeedItem -- Ukrainian localization: no data (offline) -> our item\n'

NEW_INIT = ('  Widget.Initialize(self, name)\n'
            '  mFeedData = {} -- Ukrainian localization: start clean, the list is rebuilt below\n'
            '  mNumItems = 0\n'
            '  feedSetup()\n'
            '  uaFeedAddItem()\n'
            '  mFeedWidget = self\n')


def fail(msg):
    print(f'ERROR: {msg}')
    print('Nothing was written.')
    sys.exit(1)


def lua_string(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def read_settings(path):
    """-> dict of the key: value lines of feed_item.txt (shared with make_feed_texture.py)."""
    raw = open(path, 'rb').read()
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    try:
        content = raw.decode('utf-8')
    except UnicodeDecodeError:
        fail(f'{path}: not UTF-8 - save it as UTF-8')
    values = {}
    for n, line in enumerate(content.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        m = re.match(r'^\s*(header|url|qr|line1|line2|line3)\s*:\s*(.*?)\s*$', line)
        if not m:
            fail(f'{path} line {n}: expected "header:", "url:", "qr:" or "line1:".."line3:", got {line!r}')
        if m.group(1) in values:
            fail(f'{path} line {n}: "{m.group(1)}:" is given twice')
        values[m.group(1)] = expand(m.group(2), os.path.dirname(path), path)  # {telegram...}, see links.py
    return values


def check_url(path, url, key):
    if not url:
        fail(f'{path}: "{key}:" is missing or empty')
    if not re.match(r'^https?://\S+$', url):
        fail(f'{path}: "{key}:" must start with https:// and contain no spaces, got {url!r}')


def replace_once(lua, anchor, new, name):
    if lua.count(anchor) != 1:
        fail(f'original script: the place for the {name} was found {lua.count(anchor)} times, expected once '
             f'- is original_script/{LUA} the untouched decompiled script?')
    return lua.replace(anchor, new)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    root = sys.argv[1]
    orig = os.path.join(root, 'original_script', LUA)
    settings = os.path.join(root, SETTINGS)
    out = os.path.join(root, 'localized_script', LUA)
    for p in (orig, settings, os.path.join(root, 'texture', IMAGE)):
        if not os.path.isfile(p):
            fail(f'missing file: {p}')

    raw = open(orig, 'rb').read()
    if raw.startswith(b'\x1bLua'):
        fail(f'{orig} is compiled Lua; it must be the decompiled text script')
    lua = raw.decode('utf-8')
    eol = '\r\n' if '\r\n' in lua else '\n'
    lua = lua.replace('\r\n', '\n')
    if MARK in lua:
        fail(f'{orig} already contains the item; put the untouched decompiled script there')

    values = read_settings(settings)
    header, url = values.get('header', ''), values.get('url', '')
    if not header:
        fail(f'{settings}: "header:" is missing or empty')
    if '^' in header or '<' in header:
        fail(f'{settings}: the header must not contain ^ or < (they are game markup)')
    if len(header) > MAX_HEADER:
        fail(f'{settings}: the header is {len(header)} characters - keep it to {MAX_HEADER} or less, it is one line '
             f'under the picture')
    check_url(settings, url, 'url')
    m = re.match(r'^https?://(?:www\.)?(?:t\.me|telegram\.me)/(?!s/)([A-Za-z0-9_]+)/?$', url)
    if m:
        fail(f'{settings}: url: use https://t.me/s/{m.group(1)} - plain t.me/{m.group(1)} shows an error in the '
             f'Steam overlay (the qr: line is for phones and may stay plain)')

    block = (BLOCK_SETTINGS.replace('%URL%', lua_string(url)).replace('%HEADER%', lua_string(header))
             .replace('%IMAGE%', IMAGE))
    lua = replace_once(lua, ANCHOR_SETTINGS, ANCHOR_SETTINGS + block, 'settings')
    lua = replace_once(lua, ANCHOR_POPULATE, ANCHOR_POPULATE + BLOCK_POPULATE, 'offline fallback')
    lua = replace_once(lua, ANCHOR_INIT, NEW_INIT, 'item list')

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'wb') as fh:
        fh.write(lua.replace('\n', eol).encode('utf-8'))
    print(f'Main-menu feed item: "{header}" -> {url}')
    print(f'Written: {out}')


if __name__ == '__main__':
    main()
