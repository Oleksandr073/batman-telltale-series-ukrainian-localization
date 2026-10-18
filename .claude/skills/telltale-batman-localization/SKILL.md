---
name: telltale-batman-localization
description: Rules and tools for translating Telltale "Batman - The Telltale Series" landb text exports (files like env_*_english.txt, ui_*_english.txt with "N) SPEAKER" headers), including the Shadows/Noir mode (BAT_* folders). Use whenever translating, editing, checking or syncing these .txt files, or when line counts / tags / headers must be preserved.
---

# Telltale Batman S1 — landb .txt localization rules

Analysis base: 222 files, ~185 000 records, ~43 600 unique English strings (~365 000 words).
Folders: `BM_*` = default mode, `BAT_*` = Shadows/Noir mode.

Confidence tags used below:
- **[100%]** measured on every file, zero exceptions.
- **[VERIFIED + exceptions]** measured; the exceptions are listed.
- **[LIKELY]** strong evidence, not proven in-game.
- **[TEST IN GAME]** cannot be decided from the text alone.

---

## 1. File format — breaking any of these breaks import

| Rule | Confidence |
|---|---|
| Encoding is UTF-8 **with BOM** (`EF BB BF`). | [100%] |
| Line endings are **CRLF** only. No LF-only, no CR-only lines. | [100%] |
| File ends with CRLF after the last text line. | [100%] |
| A record = 1 header line + 1..N text lines. Header regex: `^\d+\) .*$` — digits, `)`, **one space**, speaker. | [100%] |
| Empty speaker ⇒ the header ends in `) ` (trailing space). Speaker present ⇒ no trailing space (`43) VICKI`). | [100%] |
| Record IDs are unique within a file. | [100%] |
| IDs are NOT sorted (209 of 222 files): the order is the landb storage order. Never reorder records. | [100%] |
| Most records have 1 text line (184 900), but 2 645 have 2–103 lines (credits, codex, location cards, phone texts, dev notes). | [100%] |
| 4 064 records have an **empty** text line (`5) ` then an empty line). That empty line must stay. | [100%] |
| No text line in any English file starts with `digits) `. A translated line that does will be read as a new record. | [100%] |

**Hard translation rules derived from this:**
1. Do not touch header lines at all. Not the number, not the speaker, not the trailing space.
2. Keep **exactly the same number of text lines per record**. Then the total line count of the file is the same automatically.
3. Empty text lines stay empty. Non-empty lines stay non-empty (in multi-line credits/codex, empty lines are layout).
4. A translated line must never start with `<digits>) `. If a translation would, reword it (for example, put a word before the number).
5. Save as UTF-8 with BOM + CRLF. Run `scripts/validate.py` after every editing session.

## 2. Record types and what the player sees

| Record kind | How to recognise | Visible? | Action |
|---|---|---|---|
| Subtitle | header has speaker (`BRUCE`, `HARVEY`, …) | yes, without `{}`/`[]` parts | translate |
| Choice option / UI string | empty speaker (`17) `) | yes | translate |
| Speaker name in header | `43) VICKI` | no [LIKELY] — subtitles in this game show no names | never change |
| Writers'/director notes | speaker `DIR…`, `STUB…`, `NOTE(S)`, `QUESTION`, `GAMEPLAY`, `CHANGED`, `WRITING`, `VFX`, `QTE`, or text starting `(Name, Thu Jul 14 01:41:54 2016)` (~470 records) | no | leave in English (harmless to translate) |
| Cut/placeholder | `<<Insert Image Here: …>>`, URLs (`HTTPS` speaker + `//docs.google…`), `<<id:…>>` junk | no | leave untouched |
| Leftovers from other games / other platforms | `chapters_english.txt` ("Dave Goes Camping"), iOS/iCloud/PlayStation boot strings | probably not on PC | low priority, translate last |

Weird speaker names such as `HTTPS`, `16`, `1 20`, `ANOTHER SECURITY CAM FEED CATCHES HIS EYE` come from Telltale's script tool cutting text at the first `:`. So `https://…` became speaker `HTTPS` + text `//…`, and `…Jul 21 20:14:13 2016)` became speaker `1 20` + text `14:13 2016) …`. They are notes, not dialogue. [100% for the split pattern]

## 3. Markup reference

| Markup | Example | Rendered? | Rule | Confidence |
|---|---|---|---|---|
| `{Emotion}` / `{body-…}` / `{FaceAccent}` / `{BodyAccent}` / `{Intensity-…}` | `{ConcernedB}It sounds…finally{SmugA} putting…` | no — animation/emotion cues | keep every tag, character for character. Keep it at the start if it was at the start. Put mid-line tags at roughly the same point in the sentence. | keep: [100%] / exact position matters: [LIKELY no — animations are baked] |
| Runtime placeholders `{percent}` `{EPISODE NUMBER}` `{SAVE FILE NAME}` `{VIDEO NAME}` `{SPEED}` `{RoomCode}` `{RoomPopulation}` `{BUILD_VERSION}` `{ENGINE_VERSION}` | `You and {percent}% of players…` | **replaced with a value** | keep exactly, keep the `%` after `{percent}`, move as a unit if the word order needs it | [100% keep] |
| `[direction]` inside a **subtitle** | `[pickup]`, `[ALT]`, `[V.O.]`, `[laughs]`, `[beat]` (3 400+ kinds) | no | keep. Translating it is optional; keeping English is safest and saves time | [LIKELY] |
| Bracket-only **choice** (empty speaker) | `[Ignore]`, `[Ignore Them]`, `[Read text]`, `[Punch him]` (966 records) | **yes** — shown as a choice option | **translate the words inside, keep the brackets** | [CONFIRMED by user] |
| `[ALT]` (any case, also `[ALT; coverage]`, `[alt]`) | `[ALT]Violence breeds violence.` | **no** | **never touch `[ALT]` itself**; translate the text after it. The validator reports any change as an error | [CONFIRMED by user] |
| Other bracket prefixes on a choice | `[lie]A yatch salesman.`, `[play dumb]…` | prefix probably not shown | keep the prefix untouched, translate the rest | [TEST IN GAME] |
| Bracket-only subtitle | `VICKI` → `[sighs]` (1 529 records) | effort sound, no visible text | leave as is | [LIKELY] |
| `^font:Name^` `^color:#hex^` `^glyphScale:n^` `^imageScale:n^` | `^glyphScale:1.25^City Hall` | no — styling | keep exactly. Text after a tag gets that style | [100%] |
| `^^` | `^^KENT MUDLE`, `…{percent}%^^ of players` | no — "reset style" | keep. If it closes a coloured span, the translated words that should be coloured must stay **between** the opening tag and `^^` | [100%] |
| `<image.d3dtx:-15>` | `Press ^imageScale:0.8^<ui_boot_facebuttonDown.d3dtx:-15> to Begin` | shows a button icon (number = vertical offset) | keep exactly, including the spaces on both sides. You may move the whole `^imageScale^<icon>` group if the word order needs it | [100% keep] |
| `<<…>>` | `<<id:377679995>>`, `<<guid:{…}>>` | no | never touch | [100%] |
| `*word*` | `No one has *ever* managed…` (1 152 lines) | probably shown literally or as emphasis | keep the asterisk convention on the matching translated word | [TEST IN GAME] |
| Tabs | `[O.S.]\t...the whole city…` (38 lines) | no | keep. The Noir build removed some of them; either way works | [VERIFIED] |
| Double spaces, leading/trailing spaces | `Navigate  <icon> Scan`, `Cobblepot Park `, `' Vicki.'` | layout or typo | keep spacing next to tags. Elsewhere it does not matter | [VERIFIED] |

**Tag sanity in the English source** — don't "fix" these, just keep them as they are:
- `{AngryA{body-A}}`, `{FaceAccent{AngryA}}`, `{{callback}}` — nested braces (3 places).
- 55 lines with unbalanced `[` / `]` (truncated notes, e.g. `[pick`, `[confiBut they…`).
- `<ui_notification_facebuttonRight:-20>` without `.d3dtx` (ui_episode 105 Noir).
- `PlayStation®Store` (default) vs `PlayStation™Store` (Noir).

## 4. English writing conventions

**Decision (user):** the inconsistencies below are NOT normalised. Mirror each line as it is:
`...` stays three dots (and `…` stays `…`, `....` stays `....`), `--` stays `--` (and `–`/`—`/`-` stay as they are),
and a line keeps its own ending punctuation (or lack of it). Don't "fix" anything to make it consistent.

| Convention | Count | Confidence |
|---|---|---|
| Only typographic apostrophes `’` — **zero** straight `'` in all files | 89 434 vs 0 | [100%] |
| Only typographic double quotes `“ ”` — **zero** straight `"` | 3 239 vs 0 | [100%] |
| Trailing off / hesitation = three dots `...` (the `…` character is rare) | 19 034 vs 296 | [VERIFIED + exceptions: 382 cases of 4+ dots, 296 `…`] |
| Interrupted speech = double hyphen `--` at the end or start | 14 217 | [VERIFIED + exceptions: 64 `–`, 8 `—`, 474 lines ending in a single `-`] |
| Subtitles end with punctuation: `.` 108k, `?` 19k, `!` 8k, `...` 7k, `--` 2k | ~98% | [VERIFIED + exceptions: ~2 600 end in a letter] |
| Choice options: about 2/3 end with `.`, about 1/3 have no final punctuation (short actions, UI labels) | — | [VERIFIED, inconsistent] |
| Choice capitalisation is inconsistent (`[Ignore Them]` vs `[Read text]`) | — | not a rule |
| UI headers are often ALL CAPS (`COMPLETE`, `CONNECTING`) | — | keep the case style |
| Same English line repeated under many IDs (choice text + spoken version, recaps "Previously on"/"Next time on" repeat scene lines) | 185k records → 43.6k unique | translate once, reuse the same translation (watch for context, e.g. gender) |

The translation must use the target language's own typography (for example Ukrainian/Russian `«…»` and `’`). The game font must contain those glyphs. Check that in game early, because font patching is a separate task.

## 5. Default (BM_*) vs Shadows/Noir (BAT_*)

Noir is **not** a lightly edited copy. It is a re-export from the later LCG Entertainment (2019) build. Facts [100%]:

- Record IDs are the same between the two modes. **Same ID + same English text ⇒ same translation.**
- 91 of 110 Noir files are byte-identical to their default counterparts; 19 differ.
- The differences:
  - typo fixes: `Copplepot` → `Cobblepot` (2 lines, ep. 103 `env_gothamwayneenterprisesexterior`);
  - removed tabs (`env_gothamrooftops` id 452, credits);
  - new UI prompts: about 10 in `ui_episode` (e.g. `… to exit.`, `Go as Bruce/Batman`, scan/filter prompts);
  - new LCG/"Shadows Mode" credits: 68 records in each `ui_credits10x`;
  - new menu strings and new legal text in `ui_menu` (26 new, id 658 changed);
  - some lines **blanked** in Noir (`env_skylineclub102_batman` id 2425, `env_batcave` 105 ids 898–900, `env_previouslyonbat105`) and some blank default lines **filled in** (`env_gothamexteriormontage_constructionsite` 103, 17 ids). The blank records also moved in the file order. Don't reorder anything yourself.
- Present only in default: `env_previouslyonbat104`, `env_policelobbyinfirmary105`, `BM_pc_Project_data/*` (stats, ui_media, ui_text).
- Noir duplicates: `BAT_pc_PC_Noir_Batman10x_compressed/*` and `BAT_pc_BatmanNoir10x_data/*` contain the same files. Translate them identically.

**Workflow:** translate BM_* only. Then run `scripts/sync_noir.py`. It fills ~95 000 Noir records automatically and lists the ~383 that need work (mostly LCG credits).

## 6. Known corrupt characters in the source

- `U+FFFD` (`�`) is stored in the source files themselves (6 lines in each of 4 ep. 103 files, e.g. `He�s a voter like anyone else`). It was an apostrophe. Just translate the line normally.
- `U+00AD` soft hyphens in `env_gothamskyrailwarehouse_action` (`you promised\xad\xad`, used as an interruption dash).

## 7. Things to test in game (cannot be decided from the files)

1. (Resolved: bracket-only choices are visible and get translated; `[ALT]` is hidden and stays untouched.)
2. Are other prefixes like `[lie]` / `[play dumb]` on choice text hidden?
3. Are `*asterisks*` shown literally?
4. Does changing the speaker name in a header have any effect? (Keep it unchanged anyway; the validator treats it as an error.)
5. Length limits: choice buttons and UI labels have fixed widths, so long translations may be cut off or overflow. Check the choice wheel and menus.
6. Font coverage for your alphabet.

## 8. Tools (`scripts/`, Python 3, no dependencies)

Validate a translation against the English originals (single file or whole folder tree):
```
python .claude/skills/telltale-batman-localization/scripts/validate.py  EN_FOLDER  TRANSLATED_FOLDER
python .claude/skills/telltale-batman-localization/scripts/validate.py  en/file.txt  tr/file.txt  --untranslated
```
Errors: BOM/CRLF, line count, changed or shifted headers, **the first broken record** (the exact record where a line was added or removed), a text line that looks like a header, filled/emptied lines, and lost or changed `{}` `^^` `<>` `<<>>` `[ALT…]` markup. Warnings: markup order, whitespace/tab changes, straight `"`. The exit code is 1 when there are errors.

Generate translated Noir files from a finished default translation:
```
python .claude/skills/telltale-batman-localization/scripts/sync_noir.py --en EN_ROOT --tr TRANSLATED_ROOT --out OUT_ROOT
```
It writes BAT_* files using the English BAT structure (headers, line counts, BOM, CRLF) plus your translations, and creates `noir_todo.txt` listing every record still in English.

## 9. Checklist when translating a file

- [ ] Header lines untouched (copy them; translate only text lines).
- [ ] Same number of text lines in every record; empty lines stay empty.
- [ ] Every `{…}`, `^…^`, `^^`, `<…>`, `<<…>>` present and unchanged; `{percent}%` intact.
- [ ] Spaces around icon tags preserved.
- [ ] Bracket-only choices (`[Ignore Them]`) translated inside the brackets; `[ALT]` untouched.
- [ ] `...`, `--` and end punctuation mirrored from the English line, not normalised.
- [ ] No translated line starts with `number) `.
- [ ] Notes (`DIR`, `STUB`, timestamped `(Name, Day Mon …)`) left alone.
- [ ] Saved as UTF-8 with BOM, CRLF.
- [ ] `validate.py` reports 0 errors.
