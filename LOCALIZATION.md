# LT / EN localization

Lithuanian is the default. The sidebar switch and Product Tour LT / EN controls use
the same user-scoped, session-only preference. A deliberate pre-login choice carries
into the authenticated session once. No language preference is written to the database.

`i18n.py` loads matching English and Lithuanian JSON catalogs. Presentation code calls
`t(key, **values)` for labels, help/info-icon content, placeholders, messages and copy.
Enum formatters and month labels translate display text while returning the original
internal values. Labels are captured when creating enum formatters to keep them stable
outside a Streamlit script run. Data-entry widgets have language-independent keys.

`ui_errors.py` translates the existing, known domain validation failures at the
dashboard boundary. Calls and arguments remain unchanged. Rejected operations stop
before success messages; unexpected exceptions retain their diagnostic behavior.

## Terminology

| English UI | Lithuanian UI |
| --- | --- |
| Bucket / Buckets | Tikslas / Tikslai |
| Available Cash | Turimi pinigai |
| Set Aside | Atidėta tikslams |
| Free Cash | Laisvi pinigai |
| Net Worth | Grynasis turtas |
| Monthly Plan | Mėnesio planas |
| Actual contribution | Faktinis įnašas |

Free Cash means unassigned cash; it does not imply that it is safe to spend.
Internal `fund`, `fund_id`, enum values, analytics identifiers and user-entered text
remain unchanged. The deletion confirmation token is always `DELETE`.

## Changed localization files

- `i18n.py`
- `locales/en.json`
- `locales/lt.json`
- `ui_errors.py`
- `app.py`
- `dashboard_navigation.py`
- `dashboard_tour.py`
- `monthly_checkin.py`
- `fund_progress.py`
- `onboarding.py`
- `onboarding_layout.py`
- `onboarding_navigation.py`
- `onboarding_accounts.py`
- `onboarding_assets.py`
- `onboarding_debts.py`
- `onboarding_funds.py`
- `onboarding_monthly_plan.py`
- `onboarding_picture.py`
- `tour_assets/spotlight.js`
- `LOCALIZATION.md`

Test fixtures, checks and updated localized expectations:

- `tests/language_probe.py`
- `tests/dashboard_language_probe.py`
- `tests/run_offline.py`
- `tests/test_i18n.py`
- `tests/test_language_switching.py`
- `tests/test_localization_coverage.py`
- `tests/test_dashboard_tour.py`
- `tests/test_fund_progress.py`
- `tests/test_onboarding_accounts.py`
- `tests/test_onboarding_assets.py`
- `tests/test_onboarding_debts.py`
- `tests/test_onboarding_funds.py`
- `tests/test_onboarding_monthly_plan.py`
- `tests/test_onboarding_navigation.py`
- `tests/test_onboarding_picture.py`
- `tests/test_onboarding_replay.py`
- `tests/spotlight_lifecycle.mjs`

The pre-existing `visual_styles.py` changes and tour cleanup fixes were retained.
`auth_only.py`, domain/database modules and schemas were not modified.
Structured feedback is a separate proposal, not implemented by this localization task.

## Automated checks

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe tests/run_offline.py
```

This runs syntax checks, imports UI against a stub database, runs the complete suite,
then repeats the existing regression cases in EN. The full dashboard fixture uses
mock records and rejects any attempt to write financial data. It checks translated
tooltips, original internal category values, and draft preservation through LT → EN → LT.

The JavaScript lifecycle test in `tests/spotlight_lifecycle.mjs` exports `runTests()`.
It checks repeated renders, stale cleanup, Back, Close, Skip, Escape, Finish, language
switch notifications and step preservation, missing targets, and unmount cleanup.
It is an offline DOM simulation, not a browser layout test.

## Desktop and mobile manual check

1. Start the app normally with `streamlit run app.py`. A fresh session defaults to LT;
   EN remains selectable before login and in the authenticated sidebar.
2. Complete or replay every onboarding screen in LT, then EN. Inspect titles,
   examples, expandable explanations, category options, errors and success messages.
3. Before saving, change language with drafts in Accounts, Assets and Monthly Plan.
   Verify names, amounts, category selections and the current step remain intact.
4. On the dashboard, inspect each info/help icon. Edit a name, amount and category,
   switch language, and verify no draft was reset or automatically saved.
5. Inspect Bucket cards with and without targets, and contribution history/edit
   controls. Saved names and descriptions must retain their original language.
6. Choose another year and month. Verify localized month names describe that chosen
   period and changing language does not change the selected period.
7. Start the Product Tour. Change LT / EN midway: one overlay remains at the same
   step. Verify Back, Next, Close, Skip, Escape and Finish still work.
8. Check the existing feedback form and deletion confirmation. Their copy translates,
   but deletion still requires the existing checkbox and exact `DELETE` token.
9. On a narrow mobile screen, check sidebar access, long Lithuanian labels, expanded
   help, form controls and tour buttons. No extra horizontal scrolling should appear.
10. Verify normal existing-user routing and voluntary setup replay remain unchanged.

## Limits

- Streamlit/browser-owned wording, including “Press Enter to submit form”, is unchanged.
  No CSS or JavaScript translation hacks or form-submit behavior changes were added.
- Currency/number formatting retains the existing conventions. This task localizes
  copy and month names, not financial calculations or currency behavior.
- User-supplied names, comments and descriptions are never translated.
- Session preference does not persist after the Streamlit session ends.
- Phase 1 browser draft preservation was confirmed by the user. Phase 2 automated
  checks pass; desktop/mobile visual review remains a manual check.
