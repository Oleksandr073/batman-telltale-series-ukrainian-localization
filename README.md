# Batman: The Telltale Series — Ukrainian localization

Ukrainian translation of the game text of *Batman: The Telltale Series* (season 1), for both the normal mode and
Shadows (Noir) mode. The English text was extracted from the game's `.ttarch` archives as `.landb` → `.txt` files
(`N) SPEAKER` header line + text lines). Translators work in one Excel table; one script then writes the translation into
`data/unique_localized_data/` (each unique text once, to review) and `data/localized_data/` (exact copies of the 222 game files
with the text replaced).

## Folders

| File / folder | What it is |
|---|---|
| `translation_table.xlsx` | **The translation table**: one row per unique text (~44 000 rows). Type Ukrainian in the yellow column. The *Help* sheet explains every column. |
| `speaker_genders.xlsx` | Gender of each speaker (M / F / ?). It fills the *Speaker gender* / *Listener gender* columns of the translation table. Fill in the orange cells, then run `npm run rebuild`. |
| `data/original_data/` | English game text (222 files). **Never edit.** `BM_*` = normal mode, `BAT_*` = Shadows/Noir mode. |
| `data/localized_data/` | The same 222 files with Ukrainian text — the final result for the game. Written only by the script below — don't edit by hand. |
| `data/unique_original_data/` | Every unique English text once (~43 900), in files named like the game files, built from `data/original_data/` only, never from the gender file. Each entry shows who speaks → to whom (guessed from the scene) and how many times the text is used. Read-only: the import only checks it. |
| `data/unique_localized_data/` | The same entries with the Ukrainian from the table (untranslated texts stay English). Written by the script. The ~230 texts that need separate male/female Ukrainian versions appear once per version, marked e.g. `listener: female`. |
| `ai_context/style_guide.md` | Translation style decisions: quotes, apostrophe, punctuation, swearing, tone. |
| `ai_context/speakers.md` | Who talks to whom, with the confirmed ти/ви decisions. |
| `ai_context/scenes/` | Read-only copies of every game file in conversation order (all lines, with repeats) — for reading the context around a line. Not in git; create with `npm run scenes`. |
| `ai_context/glossary.md` | Names of characters, places and gadgets — translate them the same way everywhere. |
| `.claude/skills/telltale-batman-localization/` | Format rules (`SKILL.md`) and the scripts. |

## Setup (once)

Needs Python 3, Node.js (only for the `npm run` shortcuts) and git. Then install the Excel package:

```
npm run setup
```

Run everything from this folder (the repo root). **Close the Excel files before running a command.**

## Commands

All shortcuts are defined in `package.json` (`scripts`), like in any Node project.

| Command | What it does | When |
|---|---|---|
| `npm run import` | Writes the translations from `translation_table.xlsx` into `data/unique_localized_data/` and all 222 files in `data/localized_data/`, then validates and cross-checks them. | **Every time** the table was edited |
| `npm run review` | Shows each new or changed translation once (git diff of `data/unique_localized_data/`). | After every import |
| `npm run review:all` | Shows every place in the 222 game files where the text was replaced. | Optional |
| `npm run check` | Checks again that the 222 files match the unique texts — changes nothing. | Optional, e.g. after a git merge |
| `npm run validate` | Checks the structure of the 222 files (line count, headers, tags, encoding) — changes nothing. | Optional |
| `npm run rebuild` | Rebuilds `translation_table.xlsx` from the English files and `speaker_genders.xlsx`. Translations are kept. | After editing `speaker_genders.xlsx` |
| `npm run scenes` | Creates `ai_context/scenes/` (conversation-order views, not in git). | After a fresh clone |
| `npm run unique-original` | Recreates `data/unique_original_data/` from the English files. | Only if `data/original_data/` changes |
| `npm run setup` | Installs the Excel package for Python. | Once per computer |

**The normal cycle:** edit the table → `npm run import` → `npm run review` → commit → pack `data/localized_data/` into
the game archives.

`npm run import` must end with `0 error(s)` and `0 mismatch(es)`:
- **Validation:** every final file has the same structure as the English one.
- **Consistency:** every text in the 222 final files is exactly the text from `data/unique_localized_data/` (with the
  original tags put back), and every text that is not in the unique folder is unchanged English.

It never changes `data/original_data/` or `data/unique_original_data/` (it only checks that they still match), so it
is safe to run any time.

**After `npm run rebuild`:** a gender change can split a text into separate male/female rows. Run `npm run import`
again; `data/unique_localized_data/` then shows the new versions. `data/unique_original_data/` never changes because
of genders.

**One record needs its own translation** (the same English line needs different Ukrainian in one scene): make a
tab-separated file with columns `file`, `id`, `ukrainian`, `comment` (for example,
`BM_pc_Batman101_data/env_asylumconstructionsite_english.txt`, `11`, `Далі!`, `why`) and run
`npm run import -- --overrides overrides.tsv`.

The full commands behind each shortcut are in `package.json`.

## Translation rules in short

- Translate only the yellow **Ukrainian** column. Never change *English* or *key*, and never delete rows.
- Copy tags inside the text unchanged: `{SmugA}`, `^font:…^`, `^^`, `<ui_…d3dtx:-15>`, `{percent}`. Tags at the
  start of a line (`{AngryA}`, `[pickup]`, `[ALT]`) are already removed and are put back automatically.
- Multi-line texts are joined with ` ¶ `. Keep the same number of `¶`.
- Choices like `[Ignore]` are shown in the game: translate inside the brackets and keep the brackets.
- Keep `...`, `--` and the ending punctuation as in the English text.
- Follow `ai_context/style_guide.md`. Names come from `ai_context/glossary.md`, ти/ви from `ai_context/speakers.md`, and gender forms follow the *Speaker gender* /
  *Listener gender* columns.

Full details: `.claude/skills/telltale-batman-localization/SKILL.md`.
