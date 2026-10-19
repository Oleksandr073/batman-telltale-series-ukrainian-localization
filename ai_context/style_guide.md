# Style guide — Ukrainian translation of Batman: The Telltale Series

Decisions for everyone who translates (people and AI). Format rules for tags and lines are in
`.claude/skills/telltale-batman-localization/SKILL.md`; names are in `glossary.md`; ти/ви is in `speakers.md`.

## Confirmed (2026-10-19)

| Topic | Rule | Example |
|---|---|---|
| ти/ви | Exactly as in `speakers.md` (confirmed). Talking to several people = ви. | Alfred → Bruce: *Ви поранені, майстре Брюсе?* · Bruce → Alfred: *Ти мав рацію.* |
| Names | As in `glossary.md` (G and H → г: Готем, Гордон, Гарві). Inflect normally. | *Брюса, Брюсові, Брюсе; у Готемі* |
| Quotation marks | Same characters as the English: `“ ”` (and `‘ ’` inside). No «». | *Він назвав себе “Пінгвіном”.* |
| Apostrophe | The same `’` (U+2019) as the English, also inside Ukrainian words. Never `'`. | *п’ять, м’ята, комп’ютер, Брюсів* |
| Punctuation | Copy from the English line: `...` stays `...`, `--` stays `--`, `…` stays `…`, and the line ends the same way (or without punctuation if the English has none). | *I just-- → Я просто--* |
| Tags | Copy `{…}`, `^…^`, `<…>`, `{percent}` exactly; leading `{tags}`/`[ALT]` are added automatically. | *It sounds like an intern is finally{SmugA} putting… → Схоже, якийсь стажер нарешті{SmugA} знайшов…* |

## Swearing — strong, like the English (confirmed 2026-10-19)

Keep the same strength as the English word in **each line**. Don't soften it, don't censor it with `*`, and don't add
swearing where the English has none. Use the swearing that fits the character: thugs and Joker are cruder, Alfred
stays dry and posh even when he swears.

| English strength | English words (count) | Ukrainian to use |
|---|---|---|
| Mild | hell (402), damn (161), crap (41), piss (30) | чорт, в біса, дідько, трясця, к бісу, хрінь |
| Medium | shit (192), goddamn (64), bastard (52), asshole (46), son of a bitch, bitch (18) | лайно, срань, клятий, виродок, покидьок, засранець, сучий син, сука |
| Strong | fuck / fucking (68), cocksucker, motherfucker | бляха, блять, нахрін / нахуй, йобаний, курва |

Examples:
- *You’re fucking Batman!* → *Ти, бляха, Бетмен!*
- *I don’t know shit, man!* → *Ні хріна я не знаю, чуваче!*
- *Learn to knock, asshole.* → *Навчися стукати, засранцю.*
- *You’re the goddamn D.A., Harvey.* → *Ти ж, трясця, прокурор, Гарві.*

## Tone — natural Ukrainian (confirmed 2026-10-19)

Keep the meaning, the length, the joke and the character's voice, and say it the way a Ukrainian would. English
idioms become Ukrainian idioms when a literal version sounds odd. No word-for-word translation.

- *One on your left. Your other left.* → *Ліворуч від вас! Ні, з іншого боку.*
- *It’s on the house for you, girl.* → *Тобі — за рахунок закладу, сонечко.*
- *I’ll sleep like a goddamn baby. For once.* → *Спатиму, як убитий. Нарешті.*
- *I don’t think I’ll put an offer on the house.* → *Але купувати цей дім я не збираюся.*

## Always

- The voices stay English, so subtitles must match what is said: same meaning and about the same length.
  Don't add or drop information.
- Bracket-only choices like `[Ignore]` are visible: translate inside the brackets (`[Ігнорувати]`).
  Choice options are short: keep them about as short as the English.
- Gender forms follow the table's *Speaker gender* / *Listener gender* columns (`?` = decide from the scene).
