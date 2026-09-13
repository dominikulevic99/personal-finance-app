"""Same-page dashboard links and an optional prototype tour."""

import streamlit as st


from dashboard_tour import start_tour


def render_section_links():
    for heading, links in (
        ("Financial picture", (("Overview", "overview"),)),
        ("Your money", (("Accounts", "accounts"), ("Assets", "assets"), ("Debts", "debts"))),
        ("Your plan", (("Funds", "funds"), ("Monthly Plan", "monthly-plan"),
                       ("Monthly Check-in", "monthly-check-in"))),
    ):
        st.caption(heading)
        for label, anchor in links:
            st.markdown(f"[{label}](#{anchor})")


def render_guide_action(user_id):
    if st.button("Product tour", key="dashboard_guide", type="tertiary",
                 help="See how everything fits together."):
        start_tour(user_id)
