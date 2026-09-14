"""Run via streamlit for Phase 1 browser checks. No database or secrets imports."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from i18n import initialize_language, render_language_switcher, t

st.set_page_config(page_title=t('ui.language_draft_check'))
language = initialize_language(7)
with st.sidebar:
    render_language_switcher()
st.session_state.setdefault("onboarding_7_step", "accounts")
st.session_state.setdefault("onboarding_7_highest_step", 2)
st.session_state.setdefault("product_tour_7_active", True)
st.session_state.setdefault("product_tour_7_component_1", {"step": 2})
st.title(t("product.promise"))
st.text_input(t("accounts.name"), key="probe_normal")
with st.form("probe_unsaved_form"):
    st.text_input(t("accounts.name"), key="probe_form_name")
    st.number_input(t("accounts.current_balance"), key="probe_form_balance", min_value=0.0)
    st.selectbox(t('ui.type'), ["BANK", "CASH"], key="probe_form_type",
                 format_func=lambda value: t("accounts.cash" if value == "CASH" else "accounts.bank", language=language))
    if st.form_submit_button(t("actions.save")):
        st.session_state["probe_submissions"] = st.session_state.get("probe_submissions", 0) + 1
with st.expander(t('ui.dashboard_edit'), expanded=True):
    st.text_input(t("accounts.name"), value=t('ui.existing_account'), key="account_name_17")
    st.number_input(t("accounts.current_balance"), value=50.0, key="account_balance_17")
st.caption(t('ui.test_page_only_no_financial_data_is_saved_do_not'))
