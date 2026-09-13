# Phase 1 spotlight prototype — not approved for Phase 2

Four real targets: Financial Summary, Funds introduction, Monthly Plan introduction,
and Monthly Check-in. The Monthly Plan explanation was added after the initial prototype.
Product tour is manual; no financial data is passed to the component. No financial action
should be performed during these checks. Use a development/test account.

## Offline results

- Python syntax/imports: passed.
- Existing suite plus tour session/payload tests: 103 passed.
- Streamlit AppTest component mount and Python rerun smoke check: passed.
- JavaScript syntax: passed. Browser JavaScript execution was not tested.

## Browser gate — all pending (no connected browser available)

Run on desktop (1440 x 900), mobile portrait (390 x 844 and 320 x 568),
and mobile landscape. A fallback is safe degradation, NOT a positioning pass.

1. Click Product tour. Exactly one modal appears; Summary is visible through the spotlight.
2. Next scrolls to Funds, Monthly Plan, then back to Monthly Check-in. Back revisits each target.
   The guide card must not cover the target or extend beyond the viewport.
3. Repeat with the sidebar initially open and closed. Confirm it does not obscure
   highlighted content. Sidebar and dashboard controls are intentionally inactive
   during the tour; close the tour before changing the sidebar.
4. At each step, separately test Close, Skip, Escape, and Finish. After each exit,
   confirm scrolling, links, form focus, and keyboard navigation work normally.
5. While the spotlight is active, attempt to focus/click/type into background
   inputs, including via Tab. No input or financial action may be triggered.
6. Trigger a Streamlit rerun from the development runner while the tour is on its
   second step. Verify one overlay, retained step, correct position, no inert
   screen left behind, and normal closing. Repeat while resizing.
7. Temporarily omit the component mount in a development run to force unmount.
   Verify no open tour dialog, spotlight, listener-driven repositioning, or blocked
   interface remains. Restore the mount afterward.
8. Temporarily remove a target's `tour_*` container key in a development run.
   Verify a clear missing-target message, working Next/Skip/Close, and no error loop.
   Restore the key afterward. Also test browser zoom and oversized target fallback.
9. Reopen Product tour after completion; it starts at the first target. Verify another
   authenticated user's session does not inherit tour state.

Known limit requiring a decision after testing: a tall Summary on a small screen
may not fit with a guide card. The prototype detects overlap and shows a fallback
instead of covering the target. That does not meet the full spotlight requirement;
do not expand the tour until positioning and sidebar behavior have been verified.
