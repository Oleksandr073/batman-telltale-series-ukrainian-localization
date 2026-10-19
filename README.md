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
| `speaker_genders.xlsx` | Gender of each speaker (M / F / ?). It fills the *Speaker gender* / *Listener gender* columns of the translation table. Fill in the orange cells, then rebuild the table (command 3). |
| `data/original_data/` | English game text (222 files). **Never edit.** `BM_*` = normal mode, `BAT_*` = Shadows/Noir mode. |
| `data/localized_data/` | The same 222 files with Ukrainian text — the final result for the game. Written only by the script below — don't edit by hand. |
| `data/unique_original_data/` | Every unique English text once (~43 900), in files named like the game files, built from `data/original_data/` only, never from the gender file. Each entry shows who speaks → to whom (guessed from the scene) and how many times the text is used. Read-only: the import only checks it. |
| `data/unique_localized_data/` | The same entries with the Ukrainian from the table (untranslated texts stay English). Written by the script. The ~230 texts that need separate male/female Ukrainian versions appear once per version, marked e.g. `listener: female`. |
| `ai_context/style_guide.md` | Translation style decisions: quotes, apostrophe, punctuation, swearing, tone. |
| `ai_context/speakers.md` | Who talks to whom, with the confirmed ти/ви decisions. |
| `ai_context/scenes/` | Read-only copies of every game file in conversation order (all lines, with repeats) — for reading the context around a line. Not in git; see command 4. |
| `ai_context/glossary.md` | Names of characters, places and gadgets — translate them the same way everywhere. |
| `ai_context/` (other files) | Statistics behind the tables above (`pairs.tsv`, `speaker_stats.tsv`). |
| `.claude/skills/telltale-batman-localization/` | Format rules (`SKILL.md`) and the scripts. |

## Setup (once)

Python 3, plus the package for Excel files:

```
python -m pip install openpyxl
```

Run all commands from this folder (the repo root). **Close the Excel files before running them.**

## Commands

**1. Put the translations into the files** (after editing `translation_table.xlsx`):

```
python .claude/skills/telltale-batman-localization/scripts/apply_translations.py data/original_data speaker_genders.xlsx translation_table.xlsx data/localized_data --unique data/unique_original_data data/unique_localized_data
```

It checks that `data/unique_original_data/` still matches `data/original_data/` (it never writes it), then writes the Ukrainian from the
table into `data/unique_localized_data/` (each unique text once) and into all 222 files in `data/localized_data/`. Rows with an empty Ukrainian cell stay English. Then it checks itself, and the end of the output
must say `0 error(s)` and `0 mismatch(es)`:
- **Validation:** every final file has the same structure as the English one (line count, header lines, tags,
  encoding).
- **Consistency:** every text in the 222 final files is exactly the text from `data/unique_localized_data/` (with the
  original tags put back), and every text that is not in the unique folder is unchanged English.

Safe to run any time; the English folders are never changed.

**2. Review the changes in git:**

```
git diff --word-diff=plain data/unique_localized_data
```

This shows only the new or changed translations, each once (like the table), with who speaks and how many times it
is used. You don't need to read the `data/localized_data` diff — the consistency check already proved it matches. If you
want to see it anyway: `git diff --word-diff=plain data/localized_data`.

**Check the folders again later** (for example after a merge or a hand edit), without changing anything:

```
python .claude/skills/telltale-batman-localization/scripts/check_consistency.py data/original_data speaker_genders.xlsx data/unique_localized_data data/localized_data
```

**3. After changing `speaker_genders.xlsx`, rebuild the table** (your translations are kept):

```
python .claude/skills/telltale-batman-localization/scripts/build_tm.py data/original_data speaker_genders.xlsx translation_table.xlsx
```

A gender change can split a text into separate male/female rows. Then run command 1 again;
`data/unique_localized_data/` shows the new versions. `data/unique_original_data/` never changes because of genders.

(`data/unique_original_data/` is created from the English files with
`build_tm.py ... --unique-original data/unique_original_data`. This only needs to run again if `data/original_data/` itself
changes.)

**4. Create the context views in `ai_context/scenes/`:**

```
python .claude/skills/telltale-batman-localization/scripts/scene_view.py data/original_data ai_context/scenes
```

**Optional: give one record its own translation** (when the same English line needs different Ukrainian in one
scene). Make a tab-separated file with columns `file`, `id`, `ukrainian`, `comment` (for example,
`BM_pc_Batman101_data/env_asylumconstructionsite_english.txt`, `11`, `Далі!`, `why`) and add
`--overrides overrides.tsv` to command 1.

**Check any translated files** made another way (by hand or with another tool):

```
python .claude/skills/telltale-batman-localization/scripts/validate.py data/original_data data/localized_data
```

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
