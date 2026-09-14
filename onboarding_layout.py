"""Shared presentation for onboarding; no financial or routing logic."""

from contextlib import contextmanager
from html import escape

import streamlit as st
from i18n import t
from visual_styles import PALETTE_CSS, BUTTON_CSS, FORM_CSS, LAYOUT_CSS


# Scope styles to Streamlit's public container-key class. Dashboard styles
# and authentication controls are intentionally outside this container.
ONBOARDING_CSS = """
<style>
.st-key-onboarding_shell {
    box-sizing: border-box;
    max-width: 920px;
    margin: 1rem auto 3rem;
    padding: clamp(1.25rem, 4vw, 3.5rem);
    background: var(--finance-background);
    color: var(--finance-text);
    border: 1px solid #e7e7dc;
    border-radius: 28px;
    font-family: ui-sans-serif, system-ui, sans-serif;
    color-scheme: light;
}
.st-key-onboarding_shell p { color: var(--finance-muted); line-height: 1.65; }
.st-key-onboarding_shell h1 {
    color: var(--finance-text);
    font-size: clamp(2rem, 5vw, 3.35rem);
    font-weight: 650;
    letter-spacing: -0.045em;
    line-height: 1.12;
    max-width: 650px;
    padding: 0;
    margin: 1.35rem 0 .75rem;
}
.st-key-onboarding_shell .onboarding-eyebrow {
    color: var(--finance-accent);
    font-size: .75rem;
    font-weight: 650;
    letter-spacing: .12em;
    text-transform: uppercase;
}
.st-key-onboarding_shell .onboarding-progress-label {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: .5rem;
    color: var(--finance-muted);
    font-size: .85rem;
    margin: .8rem 0;
}
.st-key-onboarding_shell .onboarding-track {
    height: 6px;
    border-radius: 10px;
    overflow: hidden;
    background: #e1e6dc;
}
.st-key-onboarding_shell .onboarding-fill {
    height: 100%;
    background: #59785f;
    border-radius: inherit;
}
.st-key-onboarding_shell .onboarding-lead {
    font-size: 1.1rem;
    max-width: 540px;
    margin-bottom: 1.6rem;
}
.st-key-onboarding_shell .onboarding-cards {
    display: grid;
    grid-template-columns: 1.1fr 1fr;
    gap: 1rem;
    margin: .5rem 0 1.5rem;
}
.st-key-onboarding_shell .onboarding-card {
    background: var(--finance-surface);
    border: 1px solid var(--finance-border);
    border-radius: 20px;
    padding: 1.5rem;
}
.st-key-onboarding_shell .onboarding-card h2 {
    color: var(--finance-text);
    font-size: 1rem;
    font-weight: 650;
    margin: 0 0 1.1rem;
    padding: 0;
}
.st-key-onboarding_shell .onboarding-card ul {
    margin: 0;
    padding-left: 1.1rem;
    color: var(--finance-muted);
    font-size: .95rem;
}
.st-key-onboarding_shell .onboarding-card li { margin: 0 0 .8rem; }
.st-key-onboarding_shell .onboarding-card li::marker { color: #59785f; }
.st-key-onboarding_shell .onboarding-path {
    background: #edf1e7;
}
.st-key-onboarding_shell .onboarding-path-row {
    display: flex;
    align-items: center;
    gap: .8rem;
    padding: .7rem 0;
    color: #405847;
    font-size: .95rem;
}
.st-key-onboarding_shell .onboarding-dot {
    display: inline-grid;
    place-items: center;
    width: 2rem;
    height: 2rem;
    border-radius: 50%;
    background: #dbe5d5;
    font-size: .8rem;
    flex-shrink: 0;
}
@media (max-width: 640px) {
    .st-key-onboarding_shell { margin: 0 auto 1.5rem; padding: 1rem; border-radius: 20px; }
    .st-key-onboarding_shell h1 { font-size: 1.85rem; }
    .st-key-onboarding_shell .onboarding-cards { grid-template-columns: 1fr; }
}
</style>
"""


@contextmanager
def onboarding_shell(step=None, encouragement=None, complete=False):
    """Wrap a screen; pass step=1..5 when guided steps are implemented.

    Welcome has no step number; complete=True displays the finished setup state.
    """
    if step is not None and (isinstance(step, bool) or not isinstance(step, int) or not 1 <= step <= 5):
        raise ValueError("Onboarding step must be an integer from 1 to 5.")
    st.html(PALETTE_CSS + LAYOUT_CSS + ONBOARDING_CSS + BUTTON_CSS + FORM_CSS)
    with st.container(key="onboarding_shell"):
        label = t('ui.setup_complete') if complete else t('ui.your_financial_plan') if step is None else t("onboarding.step", step=step)
        if encouragement is None:
            encouragement = t('ui.a_little_clarity_starts_here')
        # The bar represents steps completed before the current screen.
        completed = 5 if complete else 0 if step is None else step - 1
        st.html(
            f'<div class="onboarding-eyebrow">{escape(t("onboarding.eyebrow"))}</div>'
            '<div class="onboarding-progress-label">'
            f'<span>{label}</span><span>{escape(encouragement)}</span></div>'
            f'<div class="onboarding-track" role="progressbar" '
            f'aria-label="{escape(t("onboarding.progress_label"))}" aria-valuemin="0" '
            f'aria-valuemax="5" aria-valuenow="{completed}">'
            f'<div class="onboarding-fill" style="width:{completed * 20}%"></div></div>'
        )
        yield


def render_welcome_content():
    """Static, illustrative content: no sample balances or financial claims."""
    st.html(f"""
        <h1>{escape(t("product.promise"))}</h1>
        <p class="onboarding-lead">{escape(t("product.support"))}</p>
        <div class="onboarding-cards">
            <section class="onboarding-card">
                <h2>{escape(t("welcome.have.title"))}</h2>
                <ul>
                    <li>{escape(t("welcome.have.cash"))}</li>
                    <li>{escape(t("welcome.have.debts"))}</li>
                    <li>{escape(t("welcome.have.worth"))}</li>
                </ul>
            </section>
            <section class="onboarding-card onboarding-path">
                <h2>{escape(t("welcome.purpose.title"))}</h2>
                <ul>
                    <li>{escape(t("welcome.purpose.reserve"))}</li>
                    <li>{escape(t("welcome.purpose.free"))}</li>
                    <li>{escape(t("welcome.purpose.plan"))}</li>
                </ul>
            </section>
        </div>
    """)
    st.caption(
        t('ui.setup_takes_only_a_few_minutes_you_enter_and_update')
    )
