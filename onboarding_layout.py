"""Shared presentation for onboarding; no financial or routing logic."""

from contextlib import contextmanager
from html import escape

import streamlit as st
from visual_styles import PALETTE_CSS, BUTTON_CSS, FORM_CSS


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
    margin: 1.8rem 0 1rem;
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
    .st-key-onboarding_shell { margin-top: 0; border-radius: 20px; }
    .st-key-onboarding_shell .onboarding-cards { grid-template-columns: 1fr; }
}
</style>
"""


@contextmanager
def onboarding_shell(step=None, encouragement="A little clarity starts here."):
    """Wrap a screen; pass step=1..5 when guided steps are implemented.

    Welcome has no step number because it precedes the five setup steps.
    """
    if step is not None and (isinstance(step, bool) or not isinstance(step, int) or not 1 <= step <= 5):
        raise ValueError("Onboarding step must be an integer from 1 to 5.")
    st.html(PALETTE_CSS + ONBOARDING_CSS + BUTTON_CSS + FORM_CSS)
    with st.container(key="onboarding_shell"):
        label = "Your financial plan" if step is None else f"Step {step} of 5"
        # The bar represents steps completed before the current screen.
        completed = 0 if step is None else step - 1
        st.html(
            '<div class="onboarding-eyebrow">A little more peace of mind</div>'
            '<div class="onboarding-progress-label">'
            f'<span>{label}</span><span>{escape(encouragement)}</span></div>'
            f'<div class="onboarding-track" role="progressbar" '
            f'aria-label="Setup steps completed" aria-valuemin="0" '
            f'aria-valuemax="5" aria-valuenow="{completed}">'
            f'<div class="onboarding-fill" style="width:{completed * 20}%"></div></div>'
        )
        yield


def render_welcome_content():
    """Static, illustrative content: no sample balances or financial claims."""
    st.html("""
        <h1>Take control of your money.</h1>
        <p class="onboarding-lead">See what you own, what you owe and where your money should go next.</p>
        <div class="onboarding-cards">
            <section class="onboarding-card">
                <h2>A simple place to begin</h2>
                <ul>
                    <li>No bank connection required</li>
                    <li>Manual and private by design</li>
                    <li>Never enter card numbers, PINs or banking credentials</li>
                    <li>Takes only a few minutes to get started</li>
                </ul>
            </section>
            <section class="onboarding-card onboarding-path">
                <h2>Your money, with a little more clarity</h2>
                <div class="onboarding-path-row"><span class="onboarding-dot" aria-hidden="true">1</span>See where you are today</div>
                <div class="onboarding-path-row"><span class="onboarding-dot" aria-hidden="true">2</span>Make room for what matters</div>
                <div class="onboarding-path-row"><span class="onboarding-dot" aria-hidden="true">3</span>Plan your next month</div>
            </section>
        </div>
    """)
