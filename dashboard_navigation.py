"""Same-page dashboard links and an optional prototype tour."""

import streamlit as st
from i18n import t


from dashboard_tour import start_tour


def render_section_links():
    for heading, links in (
        (t('metrics.financial_picture'), ((t('ui.overview'), "overview"),)),
        (t('ui.your_money'), ((t('ui.accounts'), "accounts"), (t('ui.assets'), "assets"), (t('ui.debts'), "debts"))),
        (t('ui.your_plan'), ((t('buckets.plural'), "funds"), (t('plan.title'), "monthly-plan"),
                       (t('ui.monthly_check_in'), "monthly-check-in"))),
    ):
        st.caption(heading)
        for label, anchor in links:
            st.markdown(f"[{label}](#{anchor})")


def render_guide_action(user_id):
    if st.button(t('ui.product_tour'), key="dashboard_guide", type="tertiary",
                 help=t('ui.see_how_everything_fits_together')):
        start_tour(user_id)
