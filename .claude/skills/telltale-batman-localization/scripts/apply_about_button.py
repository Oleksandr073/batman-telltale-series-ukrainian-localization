"""Put the Telegram button into Menu_About.lua (About screen of the main menu and the pause menu, both modes).

The About screen has only a "Previous Menu" button. This script writes a copy of the game script with one more
button next to it, which opens a link in the browser (PlatformOpenURL; on Steam it opens the Steam overlay browser).
Controller players get the same action on X / Square in the bottom hint row. The button text is set directly in
the script - it is not a landb text, so it is not in the translation table.

Usage (from the repo root):
  python apply_about_button.py ABOUT_DIR
  e.g. about_button_data

Folder layout:
  ABOUT_DIR/button.txt                       EDIT THIS: the button text and the link
  ABOUT_DIR/original_script/Menu_About.lua   decompiled game script - never edited
  ABOUT_DIR/localized_script/Menu_About.lua  WRITTEN by this script (= original + the button)

The localized script is compiled (Lua 5.2 luac, outside this repo) and packed into BOTH BM_pc_Menu_data and
BAT_pc_BatmanNoirMenu_compressed (with "Encrypt Lua for new games"). Tested in game on 2026-11-11.
Exit code 1 on any error; nothing is written then.
"""
import os
import re
import sys

LUA = 'Menu_About.lua'
SETTINGS = 'button.txt'
MARK = '-- ===== Ukrainian localization: Telegram button'

# Where the three blocks go: each anchor is a piece of the original script that must occur exactly once.
ANCHOR_SETTINGS = 'local kAboutTextBigProp = "ui_aboutTextBig.prop"\n'
ANCHOR_LEGEND = '    Legend_Add("faceButtonRight", "legend_previousMenu", "Menu_Pop()")\n'
ANCHOR_BUTTON = ('    function legendButton:Place()\n'
                 '      self:AnchorToAgent(menu.agent, menu.align, "bottom")\n'
                 '    end\n')

BLOCK_SETTINGS = r'''-- ===== Ukrainian localization: Telegram button (settings) =====
-- t.me/s/... = web view of the channel. Plain t.me/... tries to open the Telegram app (tg://), which the Steam
-- overlay browser can't do - it showed an error page.
local kTelegramURL = %URL%
local kTelegramText = %TEXT%
local kTelegramGap = 0.15 -- space between "Previous Menu" and the new button
-- ===== end of settings =====

function Menu_About_OpenTelegram()
  PlatformOpenURL(kTelegramURL)
end

'''

BLOCK_LEGEND = '    Legend_Add("faceButtonLeft", kTelegramText, "Menu_About_OpenTelegram()") -- controller: X / Square\n'

BLOCK_BUTTON = r'''
    -- mouse: a button to the right of "Previous Menu", same height
    local telegramButton = Menu_Add(LegendButton, "legendButton_telegram", "Menu_About_OpenTelegram()")

    function telegramButton:Place()
      self:AnchorToAgent(legendButton.agent, "outside_right", nil)
      local pos = AgentGetPos(self.agent)
      pos.x = pos.x + kTelegramGap
      pos.y = AgentGetPos(legendButton.agent).y
      AgentSetPos(self.agent, pos)
    end

    -- The button's prop file links it to the landb text "legendButton_back" (arrow + "Previous Menu"), and a
    -- landb link wins over "Text String". So: remove the link, then set our text.
    local setTelegramText = function()
      local agent = telegramButton.agent
      if AgentGetProperty(agent, "Text Dialog 2.0 Node Name") ~= "" then
        AgentSetProperty(agent, "Text Dialog 2.0 Node Name", "")
      end
      if AgentGetProperty(agent, "Text String") ~= kTelegramText then
        AgentSetProperty(agent, "Text String", kTelegramText)
      end
    end
    local fitTelegramButton = function()
      MenuUtils_ScaleAgentToFitTextAgent(telegramButton.agent, telegramButton.agent, "center")
      telegramButton:Place()
    end

    -- repeat for a few frames: removing the link starts the game's own resize, which may clear the text again,
    -- and "Previous Menu" may still be moving
    ThreadStart(function()
      for i = 1, 15 do
        if not pcall(setTelegramText) then
          return -- the menu was closed
        end
        WaitForCallbacks()
        if not pcall(fitTelegramButton) then
          return
        end
        WaitForNextFrame()
      end
    end)
'''


def fail(msg):
    print(f'ERROR: {msg}')
    print('Nothing was written.')
    sys.exit(1)


def lua_string(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def read_settings(path):
    """-> (text, url) from button.txt."""
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
        m = re.match(r'^\s*(text|url)\s*:\s*(.*?)\s*$', line)
        if not m:
            fail(f'{path} line {n}: expected "text: ..." or "url: ...", got {line!r}')
        if m.group(1) in values:
            fail(f'{path} line {n}: "{m.group(1)}:" is given twice')
        values[m.group(1)] = m.group(2)
    text, url = values.get('text', ''), values.get('url', '')
    if not text:
        fail(f'{path}: "text:" is missing or empty')
    if not url:
        fail(f'{path}: "url:" is missing or empty')
    if '^' in text or '<' in text:
        fail(f'{path}: the text must not contain ^ or < (they are game markup)')
    if len(text) > 40:
        fail(f'{path}: the text is {len(text)} characters - keep it to 40 or less, it is one button')
    if not re.match(r'^https?://\S+$', url):
        fail(f'{path}: the url must start with https:// and contain no spaces, got {url!r}')
    m = re.match(r'^https?://(?:www\.)?(?:t\.me|telegram\.me)/(?!s/)([A-Za-z0-9_]+)/?$', url)
    if m:
        fail(f'{path}: use https://t.me/s/{m.group(1)} - plain t.me/{m.group(1)} shows an error in the Steam overlay')
    return text, url


def insert_after(lua, anchor, block, name):
    if lua.count(anchor) != 1:
        fail(f'original script: the place for the {name} was found {lua.count(anchor)} times, expected once '
             f'- is original_script/{LUA} the untouched decompiled script?')
    return lua.replace(anchor, anchor + block)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    root = sys.argv[1]
    orig = os.path.join(root, 'original_script', LUA)
    settings = os.path.join(root, SETTINGS)
    out = os.path.join(root, 'localized_script', LUA)
    for p in (orig, settings):
        if not os.path.isfile(p):
            fail(f'missing file: {p}')

    raw = open(orig, 'rb').read()
    if raw.startswith(b'\x1bLua'):
        fail(f'{orig} is compiled Lua; it must be the decompiled text script')
    lua = raw.decode('utf-8')
    eol = '\r\n' if '\r\n' in lua else '\n'
    lua = lua.replace('\r\n', '\n')
    if MARK in lua:
        fail(f'{orig} already contains the button; put the untouched decompiled script there')

    text, url = read_settings(settings)
    lua = insert_after(lua, ANCHOR_SETTINGS,
                       BLOCK_SETTINGS.replace('%URL%', lua_string(url)).replace('%TEXT%', lua_string(text)),
                       'settings')
    lua = insert_after(lua, ANCHOR_LEGEND, BLOCK_LEGEND, 'controller hint')
    lua = insert_after(lua, ANCHOR_BUTTON, BLOCK_BUTTON, 'mouse button')

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'wb') as fh:
        fh.write(lua.replace('\n', eol).encode('utf-8'))
    print(f'About-screen button: "{text}" -> {url}')
    print(f'Written: {out}')


if __name__ == '__main__':
    main()
