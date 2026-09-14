# Structured product feedback

One optional dialog is shared by the sidebar, Product Tour and post-setup invitation. No schema changes.

## Automatic invitation timing

Leaving a successfully rendered final Financial Picture for the dashboard, or choosing
the dashboard action at the end of the Product Tour, arms a user-scoped session flag.
Ordinary login does not arm this invitation. Completing setup replay can qualify too,
provided the user has not submitted feedback and has not already been prompted this session. Onboarding completion,
eligibility and its analytics remain unchanged.

A local component waits until the dashboard summary is in the active tab's viewport
for three uninterrupted seconds. It then reports only a visibility signal; it never
reads or sends financial text or form values. The existing feedback history is checked
again before opening the shared dialog. Existing submissions or a failed lookup suppress
the invitation. The attempt is consumed before opening, so reruns and dismissals cannot
show it again in the session.

The automatic dialog starts with **Quick question before you continue** /
**Trumpas klausimas prieš tęsiant**, followed by the unchanged feedback question.
**Not now** / **Ne dabar** is available near the top. Closing, Escape and Not now return
to normal use; the sidebar action remains available. Immediate clicks/typing during
the delay cancel the invitation instead of interrupting the user. Missing targets time
out safely; timers and listeners are disposed on rerenders/unmount.

Normal later logins have no handoff flag and do not auto-prompt. Without a new persistent
dismissal field, an explicit new tour completion in a later session can qualify again
if the user has never submitted feedback. No prompt is launched by login itself.
Guided-journey automatic feedback retains the existing `product_tour` source value;
no additional source values or schema fields were introduced.

Development exception: authenticated `dominic.work310@gmail.com` can test the prompt
after every completed setup-guide or Product Tour visit, including replay and despite prior feedback.
Setup visits must render Financial Picture and then enter the dashboard; Product Tour
visits must finish with the dashboard action. Both use the same tester override. The readiness
flag is consumed once, so dashboard reruns and ordinary logins do not reopen the prompt.
This changes feedback eligibility only; existing financial data is never reset and the
account is not reclassified in the database. All other users retain submission/session suppression.

Timing files: `feedback_prompt.py`, `tour_assets/feedback_ready.js`, `feedback_ui.py`,
`dashboard_tour.py`, `onboarding_picture.py`, `app.py`, both locale catalogs,
`tests/test_feedback_prompt.py`, `tests/feedback_ready.mjs`,
`tests/test_feedback_dialog.py`, `tests/test_dashboard_tour.py`,
`tests/test_onboarding_picture.py`, and `FEEDBACK.md`.

Timing tests cover login/replay suppression, successful reveal readiness, delayed
opening, prior submissions, failed history reads, user/session isolation, LT/EN Not now,
hidden tabs/modal overlays, narrow viewport geometry, partially clipped summaries,
tester Product Tour replays, interaction cancellation and cleanup.
Browser layout/paint verification remains a manual check.

## Final copy

| Element / internal option | English | Lithuanian |
| --- | --- | --- |
| language | Language | Kalba |
| question | What would make this more useful for you? | Kas padarytų šį įrankį tau naudingesnį? |
| support | Choose everything that matters. This helps us decide what to improve next. | Pažymėk viską, kas tau aktualu. Tai padės nuspręsti, ką tobulinti toliau. |
| comment | Anything else? | Dar kažkas? |
| placeholder | What felt confusing, unnecessary, or missing? | Kas buvo neaišku, nereikalinga arba ko pritrūko? |
| comment_help | Optional — even one sentence helps. | Neprivaloma – padės net vienas sakinys. |
| other_help | If you’d like, tell us what else would help. | Jei nori, parašyk, kas dar padėtų. |
| empty | Choose an option or write a short comment. | Pasirink bent vieną variantą arba parašyk trumpą komentarą. |
| submit | Send feedback | Siųsti atsiliepimą |
| success | Thanks — this helps decide what we improve next. | Ačiū – tai padės nuspręsti, ką tobulinti toliau. |
| return | Back to my financial picture | Grįžti į finansinį vaizdą |
| tour_dashboard | Go to my financial picture | Eiti į mano finansinį vaizdą |
| tour_action | Leave quick feedback | Palikti trumpą atsiliepimą |
| sidebar_help | Tell us what's missing or confusing. | Pasidalink, ko trūksta ar kas neaišku. |
| error | We couldn't confirm your feedback was saved. Please check your previous feedback before trying again. | Nepavyko patvirtinti, ar atsiliepimas išsaugotas. Prieš bandydamas dar kartą patikrink ankstesnius atsiliepimus. |
| option.easier_data_entry | Easier way to add my existing data | Lengvesnis turimų duomenų įkėlimas |
| option.bank_connection | Automatic bank connection | Automatinis banko sąskaitų prijungimas |
| option.investment_tracking | Better investment tracking | Patogesnis investicijų stebėjimas |
| option.spending_analysis | Spending and transaction analysis | Išlaidų ir operacijų analizė |
| option.progress_over_time | See my progress over time | Finansų progreso stebėjimas laikui bėgant |
| option.better_monthly_planning | Better monthly planning | Patogesnis mėnesio planavimas |
| option.navigation_clarity | Easier navigation and clearer guidance | Aiškesnė navigacija ir pagalba |
| option.nothing_missing | Nothing important is missing for me yet | Kol kas nieko svarbaus netrūksta |
| option.other | Something else | Kažkas kita |

## Storage and behavior

- `selected_options`: allowed language-independent IDs only, stored as a PostgreSQL text array.
- `message`: trimmed comment, or an empty string for structured-only submissions. Never NULL.
- `source`: `product_tour` or `sidebar` for new submissions. Historical NULL values remain untouched.
- `user_id`: the authenticated user. The existing user-existence check and parameterized SQL are retained.
- `created_at`: the existing database default. No timestamp or schema changes.
- Selecting `nothing_missing` clears the other options; selecting another option clears it. Storage rejects conflicting combinations too.
- No financial fields are collected automatically. No feedback analytics payload is added.
- A successful submission switches to a success state, preventing writes on reruns. Further intentional feedback remains possible from the sidebar.
- Automatic invitations are consumed once per session and suppressed for users with existing feedback. This is not persistent first-ever-tour tracking.
- Close, Skip and Escape do not open feedback. The tour overlay is removed before opening the dialog.
- On storage failure the draft remains, raw database details are hidden, and no automatic retry occurs. Check previous feedback before retrying an uncertain save.

## Verification

Run `.\.venv\Scripts\python.exe tests/run_offline.py` from the repository root. Database access is stubbed.

Manual desktop/mobile checks:

1. In LT and EN, finish a Product Tour and select the feedback action. Verify a single feedback dialog opens. The primary dashboard action must close the tour without requiring feedback.
2. Open sidebar feedback in both languages. Verify the same question, options and comment field.
3. Select several options, then nothing missing. Verify others clear. Select another option and verify nothing missing clears.
4. Submit options without a comment; verify success and an empty stored message. Submit a comment without options separately.
5. Submit nothing; verify the inline prompt. Select Something else without a comment; submission should succeed.
6. Switch LT to EN and back with an unsaved comment and selected options. Drafts and selections must remain.
7. After success, rerun/change language; verify no duplicate submission. Return to the dashboard and verify a new intentional submission starts empty.
8. Close with the dialog close control/Escape and verify the dashboard is usable. No financial edits should occur from feedback interactions.
9. On mobile, verify checkbox labels wrap, the dialog scrolls, and submit/return controls remain reachable.
10. Inspect Neon using the read-only queries below. Historical messages and NULL sources must remain intact.

Browser layout remains a manual check; automated Streamlit tests verify dialog behavior and draft retention.

## Read-only Neon queries

Option counts (distinct users and submissions):

```sql
SELECT option_id,
       COUNT(DISTINCT f.user_id) AS users,
       COUNT(DISTINCT f.id) AS submissions
FROM feedback AS f
CROSS JOIN LATERAL unnest(f.selected_options) AS choices(option_id)
GROUP BY option_id
ORDER BY users DESC, option_id;
```

Recent feedback (timestamps retain the existing timestamp-without-time-zone meaning):

```sql
SELECT id, user_id, selected_options, message, source, created_at
FROM feedback
ORDER BY created_at DESC NULLS LAST, id DESC
LIMIT 50;
```

## Files changed in this task

`feedback.py`, `feedback_ui.py`, `app.py`, `dashboard_tour.py`, `tour_assets/spotlight.js`,
`i18n.py` (avoid a duplicate widget-default warning when synchronizing the dialog language),
`locales/en.json`, `locales/lt.json`, `tests/test_feedback.py`, `tests/test_feedback_dialog.py`,
`tests/test_dashboard_tour.py`, `tests/spotlight_lifecycle.mjs`, `tests/run_offline.py`, `FEEDBACK.md`.

Financial calculations, financial database records, authentication, ownership rules, onboarding eligibility,
Bucket behavior, contribution/reversal behavior and analytics schema are unchanged.
