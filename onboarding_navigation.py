"""Session-only step navigation; no eligibility or financial writes."""

import streamlit as st
from i18n import t

STEPS = ("accounts", "assets", "debts", "funds", "monthly_plan", "financial_picture")
LABELS = ('ui.accounts', 'ui.assets', 'ui.debts', 'buckets.plural', 'plan.title', 'metrics.financial_picture')


def render_step_navigation(user_id, *, unrestricted=False):
    prefix = f"onboarding_{user_id}_"
    current = STEPS.index(st.session_state.get(prefix + "step", "accounts"))
    replay = unrestricted or st.session_state.get(prefix + "replay_mode", False)
    highest = max(st.session_state.get(prefix + "highest_step", 0), current)
    if not replay:
        st.session_state[prefix + "highest_step"] = highest
    with st.expander(t('ui.navigate_setup'), expanded=False):
        st.caption(t('ui.save_form_changes_before_switching_steps'))
        for start in (0, 3):
            for index, column in zip(range(start, start + 3), st.columns(3)):
                allowed = replay or index <= highest
                status = t('ui.current') if index == current else (
                    t('ui.reached') if index <= highest and not replay else t('ui.open') if allowed else t('ui.locked')
                )
                with column:
                    if st.button(
                        f"{t(LABELS[index])} · {status}",
                        key=prefix + "nav_" + STEPS[index],
                        type="tertiary", disabled=index == current or not allowed,
                    ) and allowed and index != current:
                        st.session_state[prefix + "step"] = STEPS[index]
                        st.rerun()
