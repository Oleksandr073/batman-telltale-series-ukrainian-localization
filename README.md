# Batman: The Telltale Series — Ukrainian localization

Ukrainian translation of the game text of *Batman: The Telltale Series* (season 1), for both the normal mode and
Shadows (Noir) mode. The English text was extracted from the game's `.ttarch` archives as `.landb` → `.txt` files
(`N) SPEAKER` header line + text lines). Translators work in one Excel table; one script then writes the translation into
`data/game_text/unique_localized_data/` (each unique text once, to review) and `data/game_text/localized_data/` (exact copies of the 222 game files
with the text replaced).

## Folders

Everything the scripts read and write lives in `data/`: `data/game_text/` (the game's landb text) and one folder
per extra game script (`data/choice_stats/`, `data/about_button/`, `data/feed_item/`). Put new ones there too.

| File / folder | What it is |
|---|---|
| `translation_table.xlsx` | **The translation table**, in story order: episodes and scenes as header rows, each unique text once (~44 000 yellow rows to translate), plus grey rows where a text appears again later (for context, filled automatically). The *Help* sheet explains every column. |
| `speaker_genders.xlsx` | Gender of each speaker (M / F / ?). It fills the *Speaker gender* / *Listener gender* columns of the translation table. Fill in the orange cells, then run `npm run rebuild`. |
| `data/game_text/original_data/` | English game text (222 files). **Never edit.** `BM_*` = normal mode, `BAT_*` = Shadows/Noir mode. |
| `data/game_text/localized_data/` | The same 222 files with Ukrainian text — the final result for the game. Written only by the script below — don't edit by hand. |
| `data/game_text/unique_original_data/` | Every unique English text once (~43 900), in files named like the game files, built from `data/game_text/original_data/` only, never from the gender file. Each entry shows who speaks → to whom (guessed from the scene) and how many times the text is used. Read-only: the import only checks it. |
| `data/game_text/unique_localized_data/` | The same entries with the Ukrainian from the table (untranslated texts stay English). Written by the script. The ~230 texts that need separate male/female Ukrainian versions appear once per version (same English, entry ids ending in `-SM`/`-SF`/`-LM`/`-LF`). |
| `data/choice_stats/` | Texts of the end-of-episode **choices screen** ("You and 67.1% of players…"). They come from Telltale's server, not from landb files, so they live here: `original_script/` = English `choice_stats_english.txt` + the decompiled game script `ChoiceStats.lua` (never edit); `localized_script/` = the same txt in Ukrainian + `ChoiceStats.lua`, both written by `npm run import` from the table (don't edit). See *Choices screen* below. |
| `data/about_button/` | The **"Open Telegram channel" button** on the About screen. `button.txt` = the button text and the link (**edit this**); `original_script/Menu_About.lua` = the decompiled game script (never edit); `localized_script/Menu_About.lua` = the script with the button, written by `npm run import` (don't edit). See *About-screen button* below. |
| `data/feed_item/` | The **Telegram item in the main-menu feed** (the carousel at the bottom left). `feed_item.txt` = header text, link, QR link and picture text (**edit this**); `original_script/UI_Feed.lua` = the decompiled game script (never edit); `localized_script/UI_Feed.lua` = the script with the item, written by `npm run import` (don't edit); `texture/ui_imageUATelegramFeed.d3dtx` = the picture (made by `npm run feed-texture`). See *Main-menu feed item* below. |
| `data/game_text/credits/` | Localization credits: `about.txt` (About screen of the main menu), `boot.txt` (boot screen, under the copyright) and `credits.txt` (start of the end credits of all 5 episodes). Each line here = one line on screen (empty lines are kept). `npm run import` adds them after the original text in both modes. See *Localization credits* below. |
| `telegram.txt` | **The Telegram channel**, the only place to change it (`channel: NAME`). Other files use `{telegram}` (https://t.me/NAME), `{telegram_short}` (t.me/NAME) and `{telegram_web}` (https://t.me/s/NAME), filled in by the scripts. See *Telegram link* below. |
| `ai_context/play_order.txt` | The story order of the game files, with scene titles. Edit it to fix the order, then `npm run rebuild`. Scenes marked `(?)` are guesses. |
| `ai_context/style_guide.md` | Translation style decisions: quotes, apostrophe, punctuation, swearing, tone. |
| `ai_context/speakers.md` | Who talks to whom, with the confirmed ти/ви decisions. |
| `ai_context/scenes/` | Read-only copies of every game file in conversation order (all lines, with repeats) — for reading the context around a line. Not in git; create with `npm run scenes`. |
| `ai_context/official_usage.txt` | Which texts Telltale's official translations (8 languages) translated. It fills the *Official* column of the table. Made once from the official game files, which are not in this repo — keep it as it is. |
| `ai_context/glossary.md` | Names of characters, places and gadgets — translate them the same way everywhere. |
| `.claude/skills/telltale-batman-localization/` | Format rules (`SKILL.md`) and the scripts. |

## Setup (once)

Needs Python 3, Node.js (only for the `npm run` shortcuts) and git. Then install the Excel package:

```
npm run setup
```

Run everything from this folder (the repo root). **Close the Excel files before running a command.**

## Localization flow

1. **Set speaker genders** (only when needed): edit `speaker_genders.xlsx` by hand — fill the orange cells
   (unknown gender that matters) or fix a gender. Save and close the file.
2. **Rebuild the table:** `npm run rebuild`. The gender columns in `translation_table.xlsx` are updated and texts
   said by both men and women get separate rows. Existing translations are kept; rows whose gender changed are marked
   "check gender forms" in *Notes*. Skip steps 1–2 if no gender changed.
3. **Translate:** fill the yellow *Ukrainian* column of `translation_table.xlsx`, by hand or with AI. Follow
   `ai_context/style_guide.md`, `ai_context/glossary.md` and `ai_context/speakers.md`. Save and close the file.
4. **Import:** `npm run import`. It writes `data/game_text/unique_localized_data/` and the 222 files in `data/game_text/localized_data/`,
   and checks them. The output must end with `0 error(s)` and `0 mismatch(es)`:
   - **validation** — every final file has the same structure as the English one (line count, header lines, tags,
     encoding);
   - **consistency** — every text in the 222 files is exactly the text from `data/game_text/unique_localized_data/`, and
     everything not translated is unchanged English.

   If there are errors, the output names the file, line and problem. Fix the table and run `npm run import` again.
   The English folders are never changed.
5. **Review the translations:** `npm run review` — each new or changed text once, English → Ukrainian, with who
   speaks to whom. This is the main review. Wrong wording → fix it in the table and go back to step 4.
6. **Review the game files (optional):** `npm run review:all` — every place in the 222 files of
   `data/game_text/localized_data/` where the text was replaced. You don't need to read it all: step 4 already proved these
   files match step 5.
7. **Commit** (table + `data/` folders together), then pack `data/game_text/localized_data/` into the game archives.

Extra checks any time, without changing anything: `npm run check` (222 files vs. unique texts) and
`npm run validate` (structure of the 222 files). After `git pull`/merge, run `npm run import` (or at least
`npm run check`) before packing.

## AI drafts

Claude can write a first draft into the table, scene by scene; people review it there.

1. `npm run ai:export -- ai_context/batches/<name>.txt --scene BM_pc_Batman101_data/env_mayorsoffice`
   (or `--next 200`, add `--shown-only` for rows the official translations used) — the rows with an empty
   Ukrainian cell, with context: who speaks to whom, genders, glossary names, ти/ви.
2. Claude translates them into `ai_context/batches/<name>.tsv` (`key <TAB> ukrainian <TAB> optional note`).
3. `npm run ai:apply -- ai_context/batches/<name>.tsv` checks every row (lines, tags, leading spaces, ending
   punctuation, `--`/`...`, no ASCII `'` or `"`) and writes the ones that pass **only into empty Ukrainian cells**,
   with `AI draft` (and Claude's note, if any) in *Translator notes*. Rows that fail are listed, not written.
4. Review in the table: fix the text if needed and **delete `AI draft`** from *Translator notes* when the row is
   checked. `npm run ai:status` shows per episode how many rows are by people / AI drafts / empty.
5. Then the usual `npm run import` and `npm run review`.

Cells typed by people are never overwritten. `--replace-drafts` lets a new draft replace a row still marked
`AI draft`. `ai_context/batches/` is not in git: the table is the source of truth.

## Commands

All shortcuts are defined in `package.json` (`scripts`), like in any Node project.

| Command | What it does | When |
|---|---|---|
| `npm run import` | Writes the translations from `translation_table.xlsx` into `data/game_text/unique_localized_data/` and all 222 files in `data/game_text/localized_data/`, then validates and cross-checks them. | **Every time** the table was edited |
| `npm run review` | Shows each new or changed translation once (git diff of `data/game_text/unique_localized_data/`). | After every import |
| `npm run review:all` | Shows every place in the 222 game files where the text was replaced. | Optional |
| `npm run check` | Checks again that the 222 files match the unique texts — changes nothing. | Optional, e.g. after a git merge |
| `npm run validate` | Checks the structure of the 222 files (line count, headers, tags, encoding) — changes nothing. | Optional |
| `npm run rebuild` | Rebuilds `translation_table.xlsx` from the English files and `speaker_genders.xlsx`. Translations and translator notes are kept; everything else in the table is recreated. | After editing `speaker_genders.xlsx` |
| `npm run scenes` | Creates `ai_context/scenes/` (conversation-order views, not in git). | After a fresh clone |
| `npm run unique-original` | Recreates `data/game_text/unique_original_data/` from the English files. | Only if `data/game_text/original_data/` changes |
| `npm run test` | Self-test of the whole flow on random scenes in a temporary copy (fake Ukrainian, every record of the 222 files checked, rebuilds, gender change, deliberate mistakes). Changes nothing in the repo; ~5 min. Repeat a run with `npm run test -- --seed N`. | After changing the scripts |
| `npm run fake` | **Test only, use a separate branch.** Fills the table with a fake translation (English letters swapped for Cyrillic, using all 33 Ukrainian letters to test the font; end credits stay English) and imports it, to check the game build. Stops if the table already has real translations. | Before packing a test build |
| `npm run ai:status` / `ai:export` / `ai:apply` | AI drafts: progress per episode / export a batch / write checked drafts into empty cells (see *AI drafts*). | While translating |
| `npm run choice-stats` | Writes `data/choice_stats/localized_script/` (choice txt + `ChoiceStats.lua`) from the imported `stats_english.txt`. Runs automatically at the end of `npm run import` (see *Choices screen*). | Automatic |
| `npm run about-button` | Writes `data/about_button/localized_script/Menu_About.lua` from `data/about_button/button.txt`. Runs automatically at the end of `npm run import` (see *About-screen button*). | After editing `button.txt` |
| `npm run feed-item` | Writes `data/feed_item/localized_script/UI_Feed.lua` from `data/feed_item/feed_item.txt` (header + link). Runs automatically at the end of `npm run import` (see *Main-menu feed item*). | After editing `header:` / `url:` |
| `npm run feed-texture` | Remakes the feed picture `data/feed_item/texture/ui_imageUATelegramFeed.d3dtx` (QR code + text) from `feed_item.txt`, plus `preview.png` (not in git). Needs `npm run setup:texture` once. Also runs at the end of `npm run import`, which skips it with a note if Pillow/qrcode are not installed. | After editing `qr:` / `line1:`–`line3:` |
| `npm run setup:texture` | Installs Pillow and qrcode for Python (only needed for `npm run feed-texture`). | Once per computer, if you remake the picture |
| `npm run setup` | Installs the Excel package for Python. | Once per computer |

The steps in which to use them are in **Localization flow** above.

**One record needs its own translation** (the same English line needs different Ukrainian in one scene): make a
tab-separated file with columns `file`, `id`, `ukrainian`, `comment` (for example,
`BM_pc_Batman101_data/env_asylumconstructionsite_english.txt`, `11`, `Далі!`, `why`) and run
`npm run import -- --overrides overrides.tsv`.

The full commands behind each shortcut are in `package.json`.

## Choices screen

The choices screen at the end of each episode (and in the menu) gets its texts from Telltale's server, in 9
languages without Ukrainian. The game shows them through `ChoiceStats_LocalizeText()` in `ChoiceStats.lua`, so the
Ukrainian goes into that script instead of a landb file.

1. Translate the texts **in the table**, like everything else: they are the rows from
   `BM_pc_Project_data/stats_english` (section MENUS & UI). Keep `{percent}%` (the number comes from the server) and
   the `^^` after it (it ends the green/red part).
2. `npm run import` (it runs `npm run choice-stats` at the end). That reads the imported `stats_english.txt` and
   writes `data/choice_stats/localized_script/choice_stats_english.txt` (the 133 known server texts in Ukrainian,
   for review with git diff) and `data/choice_stats/localized_script/ChoiceStats.lua` = the original script + a block
   with those 133 texts. The original part is not changed; with nothing translated both files equal the originals.
   A text left in English stays English.

   The screen shows only the 26 choices the server sends (133 texts). `stats_english.txt` has ~190 more choice texts
   that never reach the screen (unused candidates); they stay in the table but are not put into the script.
3. That script is compiled (Lua 5.2 `luac`) and packed into `BAT_pc_PC_Noir_Proj_compressed.ttarch2` — **not**
   `BM_pc_Project_data`: the Noir_Proj patch has its own copy of the script, which overrides the other one.

## About-screen button

The About screen (main menu and pause menu, both modes) gets a second button next to "Previous Menu" that opens a
link in the browser (on Steam: the Steam overlay browser). Controller players get the same on X / Square. The button
text is set in the game script `Menu_About.lua`, not in a landb file, so it is not in the table.

1. Edit `data/about_button/button.txt`:
   ```
   text: Відкрити Telegram канал
   url: {telegram_web}
   ```
   Text: one line, up to 40 characters, no `^` or `<`. For a Telegram channel keep the `t.me/s/NAME` form: plain
   `t.me/NAME` tries to open the Telegram app, which the Steam overlay browser can't do (error page). The script
   refuses a plain `t.me/NAME` link.
2. `npm run about-button` (or `npm run import`, which runs it at the end). It writes
   `data/about_button/localized_script/Menu_About.lua` = the original script + the button. Review it with `git diff`.
3. That script is compiled (Lua 5.2 `luac`) and packed into **both** `BM_pc_Menu_data.ttarch2` and
   `BAT_pc_BatmanNoirMenu_compressed.ttarch2` (not `BAT_pc_PC_Noir_Menu_compressed` — the About script is not there).

## Telegram link

The channel is written once, in `telegram.txt` (`channel: Just1ce_UA_channel`). `data/game_text/credits/*.txt`,
`data/about_button/button.txt` and `data/feed_item/feed_item.txt` use placeholders instead of the link:

| Placeholder | Becomes | Use it for |
|---|---|---|
| `{telegram}` | `https://t.me/NAME` | QR code, text people copy: opens the Telegram app on phones |
| `{telegram_short}` | `t.me/NAME` | short text on screen |
| `{telegram_web}` | `https://t.me/s/NAME` | buttons clicked in game: the Steam overlay browser can't open the app |

To change the channel, edit `telegram.txt` and run `npm run import`. An unknown `{telegram...}` placeholder or a
missing `telegram.txt` stops the scripts with an error.

## Main-menu feed item

The news carousel at the bottom left of the main menu normally shows Telltale's news from their server. The game
script `UI_Feed.lua` is changed so that our item is always shown **first** (Telltale's items follow; the arrows and
the auto-switch every 9 s work as before). If the server feed can't be loaded, our item is shown instead of the
"offline" tile. Clicking it opens a link (on Steam: the Steam overlay browser). The picture is a QR code with some
text. The texts are set in the script and the picture, not in a landb file, so they are not in the table.

1. Edit `data/feed_item/feed_item.txt`:
   ```
   header: Telegram канал перекладу             <- text under the picture (one line, up to 32 characters)
   url: {telegram_web}                          <- what a click opens (t.me/s/NAME form, as for the About button)
   qr: {telegram}                               <- what the QR code opens on a phone (plain t.me/NAME is right here)
   line1: Just1ce_UA                             <- text right of the QR code: large bold,
   line2: Telegram канал                         <-   medium,
   line3: Скануй або натисни                     <-   small
   ```
2. `npm run feed-item` (or `npm run import`, which runs it at the end) for `header:` / `url:`. It writes
   `data/feed_item/localized_script/UI_Feed.lua` = the original script + the item. Review it with `git diff`.
3. For `qr:` / `line1:`–`line3:`: `npm run setup:texture` once on your computer; after that `npm run import` (or
   `npm run feed-texture` alone) remakes the picture each time. Without Pillow/qrcode the import skips the picture with
   the note "Feed picture NOT remade" and keeps the one in git. It
   writes `data/feed_item/texture/ui_imageUATelegramFeed.d3dtx`, plus `preview.png` and `preview_visible_band.png` (the
   red box is the part the game shows; the previews are only for you to look at and are not in git). The script stops if a line is too wide. Uses the Windows fonts Segoe UI.
4. Compile the script (Lua 5.2 `luac`) and pack:

   | File | Archives |
   |---|---|
   | `UI_Feed.lua` (compiled) | **both** `BM_pc_Menu_data.ttarch2` and `BAT_pc_PC_Noir_Menu_compressed.ttarch2` |
   | `ui_imageUATelegramFeed.d3dtx` | **both** `BM_pc_Menu_data.ttarch2` and `BAT_pc_BatmanNoirMenu_compressed.ttarch2` |

   `BAT_pc_BatmanNoirMenu_compressed` is loaded only in Shadows mode — with the picture only there, classic mode
   shows the default picture.

## Localization credits (About screen, boot screen, end credits)

`npm run import` adds the lines of each file in `data/game_text/credits/` to the end of one game text, in both modes:

| File | Game text | Where on screen |
|---|---|---|
| `data/game_text/credits/about.txt` | record 658 of `ui_menu_english.txt` (`BM_pc_Menu_data`, `BAT_pc_PC_Noir_Menu_compressed`) | Main menu → About: after build/engine version and copyright |
| `data/game_text/credits/boot.txt` | record 21 of `boot_english.txt` (`BM_pc_Boot_data`, `BAT_pc_PC_Noir_Boot_compressed`) | Boot screen: after the copyright at the bottom. Keep it to 1–2 short lines |
| `data/game_text/credits/credits.txt` | the episode title: record 216 of `ui_credits101_english.txt`, record 1 of `ui_credits102…105_english.txt` (`BM_pc_Menu_data`, `BAT_pc_PC_Noir_Menu_compressed`) | End credits of every episode: one small line right under the episode title. The credits blocks have fixed positions (more lines would overlap "WRITTEN BY"), so keep it to one line with no empty line before it. The title's large font carries over - keep it small with `^glyphScale:0.4^`. (Or put `# same line` at the top to add the text to the end of the title line instead.) |

Edit a file (plain text, UTF-8; each line = one line on screen), then run `npm run import`. A line must not start
with `number) `. Lines starting with `#` are not shown. **Font size** (1 = normal, 0.8 = 80%; the game's size tag
`^glyphScale:N^` is put at the start of every line):
- `# scale original: 0.7` - the original game text above your info;
- `# scale credits: 0.9` - your info;
- `# scale: 0.8` - both at once (the two lines above win over it).

Delete a line to keep that text at normal size. The game keeps a size for the lines below it, so when the original
text is resized, your info always gets its own tag (`^glyphScale:1^` for normal size). These are the only records allowed to have more lines than the English: `npm run validate` and
`npm run check` know these lines and report it if they are missing or different. The original texts themselves are
still translated in the table as usual. Other file names in `data/game_text/credits/` are refused; to add a new place, add it to
`TARGETS` in `scripts/credits.py`.

## Translation rules in short

- Translate only the yellow **Ukrainian** column. Never change *English* or *key*, and never delete rows.
- Grey rows repeat a text for context; their Ukrainian cell shows the translation from the row in *Notes*
  ("see row #N"). Never type in grey rows — the import warns and ignores them.
- The blue **Translator notes** column is free space for people (questions, doubts, "check in game"). Scripts
  never use it. Other columns are rewritten on `npm run rebuild`, so write notes only there.
- Copy tags inside the text unchanged: `{SmugA}`, `^font:…^`, `^^`, `<ui_…d3dtx:-15>`, `{percent}`. Tags at the
  start of a line (`{AngryA}`, `[pickup]`, `[ALT]`) are already removed and are put back automatically.
- Multi-line texts are joined with ` ¶ `. Keep the same number of lines: type `¶` or press Alt+Enter between them.
  A text without `¶` is one line in the game: no line breaks (Alt+Enter) in its translation. The import skips such
  rows and names their row number (`#` column).
- The *Official* column says how many official translations translated the text: `yes 8/8` = shown in the game,
  `no 0/8` = no language translated it, so it is almost surely never shown (cut lines, alternate takes). It is only
  for information: translate every row as usual.
- Choices like `[Ignore]` are shown in the game: translate inside the brackets and keep the brackets.
- Keep `...`, `--` and the ending punctuation as in the English text.
- Times in 24-hour format with two-digit hours: `8:32 PM` → `20:32`, `6:06 AM` → `06:06`.
- Follow `ai_context/style_guide.md`. Names come from `ai_context/glossary.md`, ти/ви from `ai_context/speakers.md`, and gender forms follow the *Speaker gender* /
  *Listener gender* columns.

Full details: `.claude/skills/telltale-batman-localization/SKILL.md`.
