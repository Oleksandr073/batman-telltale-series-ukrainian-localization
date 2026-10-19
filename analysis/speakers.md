# Speakers, gender and ти/ви — Batman S1 (Ukrainian)

Files in `analysis/`:
- `speaker_genders.tsv` — gender of every speaker ID (M/F/?). **Edit it**, then rebuild the translation table.
- `speaker_stats.tsv` — lines per speaker, and how many need the speaker’s / listener’s gender in Ukrainian.
- `pairs.tsv` — every speaker → listener pair with line counts and examples.
- `translation_table.tsv` — one row per unique text to translate.
- `scenes/` — read-only views of every file sorted by record number (conversation order).

How the listener is guessed: a `[to Alfred]` note, else a name used in direct address ("Alfred, …"), else the
most frequent other speaker within 3 records. Only about 10% of lines are found by note or name; the rest are
from neighbours, so treat it as a strong hint. Choice options are spoken by Bruce/Batman.

## Speakers whose gender is unknown but matters

Number = lines where their gender changes the Ukrainian text. Listen in game, then set M/F in
`speaker_genders.tsv` and rebuild the table (existing translations are kept, marked "check gender forms"):

REPORTER04 (8), REPORTER03 (8), ASSISTANT (28), SPENCER (1), ENFORCER01 (9), ORDERLY02 (8), ORDERLY01 (7), GCPD01 (6), COA01 (3), COA02 (2), COP02 (2), COA03 (2), BOUNCER (2), ORDERLY1 (6), COA04 (3), PROTESTER01 (1), PATRON (1), INMATE02 (1), POLICE OFFICER (2), GCPD02 (3), INMATE03 (1), PROTESTER02 (2), ORDERLY2 (1), RIOTER02 (1), CAFEPATRON2 (1), ATTORNEY (1), DOCTOR (1), ORDERLY 2 (1)

## ти/ви (suggestions — confirm or change in the last column)

General rules: **talking to several people = ви** (plural), whatever the table says. Strangers, staff, police,
reporters, nurses ↔ Bruce: ви. Batman ↔ thugs and criminals: ти. Batman → ordinary adults (hostages,
workers): ви; → children: ти. Wayne parents ↔ young Bruce: ти.

| Speaker → listener | lines | suggested | Reverse | lines | suggested | Notes | Your decision |
|---|---|---|---|---|---|---|---|
| Alfred → Bruce | 6455 | **ви** | Bruce → Alfred | 6898 | **ти** | butler who raised him: "Master Bruce", "sir" one way; family the other way | |
| Alfred → Batman | 585 | **ви** | Batman → Alfred | 716 | **ти** | same as above | |
| Harvey → Bruce | 6742 | **ти** | Bruce → Harvey | 6140 | **ти** | best friends; keep ти when Two-Face turns on Bruce (ep. 4–5) | |
| Harvey → Batman | 792 | **ви** | Batman → Harvey | 458 | **ви** | strangers; Two-Face → Batman may switch to ти (hostile) | |
| Selina → Bruce | 1938 | **ти** | Bruce → Selina | 1600 | **ти** | optional ви in their very first meeting (ep. 1); close and flirty after | |
| Catwoman → Batman | 171 | **ти** | Batman → Catwoman | 125 | **ти** | rivals, then partners | |
| Gordon → Bruce | 1894 | **ви** | Bruce → Gordon | 1882 | **ви** | "Mr. Wayne" / "Lieutenant" | |
| Gordon → Batman | 817 | **ти** | Batman → Gordon | 608 | **ти** | gruff cop and vigilante, allies; ви also works if you want Gordon formal | |
| Lucius → Bruce | 1060 | **ви** | Bruce → Lucius | 1136 | **ви** | older employee, mutual respect | |
| Lucius → Batman | 850 | **ви** | Batman → Lucius | 944 | **ви** |  | |
| Vicki → Bruce | 913 | **ви** | Bruce → Vicki | 1241 | **ви** | ви in public (press conference); ти in private once they get close — decide per scene | |
| Vicki → Batman | 498 | **ви** | Batman → Vicki | 329 | **ви** | reporter and vigilante | |
| Lady Arkham → Batman | 649 | **ти** | Batman → Lady Arkham | 386 | **ти** | enemies | |
| Oswald → Bruce | 556 | **ти** | Bruce → Oswald | 623 | **ти** | childhood friends ("mate", "Oz"); stays ти when they become enemies | |
| Oswald → Batman | 637 | **ти** | Batman → Oswald | 382 | **ти** | enemies | |
| Penguin → Batman | 501 | **ти** | Batman → Penguin | 289 | **ти** |  | |
| John Doe / Joker → Bruce | 1193 | **ти** | Bruce → John Doe / Joker | 762 | **ти** | John is over-familiar ("Brucie", "pal") | |
| Mayor Hill → Bruce | 825 | **ви** | Bruce → Mayor Hill | 561 | **ви** | Hill may drop to ти when he gets nasty | |
| Mayor Hill → Batman | 284 | **ви** | Batman → Mayor Hill | 212 | **ти** | terrified mayor; Batman interrogates him | |
| Falcone → Bruce | 162 | **ти** | Bruce → Falcone | 165 | **ви** | old mob boss patronises "the kid"; Bruce stays polite | |
| Montoya → Bruce | 125 | **ви** | Bruce → Montoya | 219 | **ви** |  | |
| Montoya → Batman | 164 | **ти** | Batman → Montoya | 133 | **ви** | she arrests him; he stays cold-polite | |
| Dr. Leland → Bruce | 413 | **ви** | Bruce → Dr. Leland | 307 | **ви** | doctor and patient | |
| Regina → Bruce | 184 | **ви** | Bruce → Regina | 151 | **ви** | high society | |
| reporters → Bruce | 835 | **ви** | Bruce → reporters | 1163 | **ви** | REPORTER01–05, RAMARQUE, SPENCER | |
| Harvey → Vicki | 573 | **ви** | Vicki → Harvey | 485 | **ви** |  | |
| Harvey → Selina | 232 | **ти** | Selina → Harvey | 204 | **ти** | they date | |
| Harvey → Gordon | 244 | **ви** | Gordon → Harvey | 314 | **ви** | D.A. and lieutenant | |
| Harvey → Alfred | 240 | **ви** | Alfred → Harvey | 214 | **ви** |  | |
| Gordon → Montoya | 117 | **ти** | Montoya → Gordon | 111 | **ви** | boss and officer | |
| Lady Arkham → Catwoman | 128 | **ти** | Catwoman → Lady Arkham | 112 | **ти** |  | |
| Oswald → Regina | 113 | **ви** | Regina → Oswald | 108 | **ви** | business | |
