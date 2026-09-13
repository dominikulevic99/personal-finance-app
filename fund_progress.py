"""Display-only goal progress; never changes balances or targets."""

from decimal import Decimal, InvalidOperation
from contextlib import contextmanager
import re

import streamlit as st
from visual_styles import fund_card_style


def _number(value):
    try:
        number = Decimal(str(value))
        return number if number.is_finite() else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def goal_progress_copy(balance, target):
    current = _number(balance)
    goal = _number(target)
    amount = f"€{current:,.2f}" if current is not None else "Balance unavailable"
    if target is None or goal == 0:
        return amount, "No target set"
    target_text = f"€{goal:,.2f}" if goal is not None else "Target unavailable"
    amounts = f"{amount} / {target_text}"
    if current is None or goal is None or current < 0 or goal < 0:
        return amounts, "Progress unavailable. Check the saved balance and target."
    percentage = current / goal * 100
    if current >= goal:
        return amounts, f"{percentage:,.1f}% · Target reached"
    return amounts, f"{percentage:,.1f}% · €{goal - current:,.2f} to go"


def render_fund_progress(balance, target):
    amounts, detail = goal_progress_copy(balance, target)
    st.write(amounts)
    st.caption(detail)


@contextmanager
def fund_progress_card(user_id, fund):
    """One native reveal control containing the saved goal summary and edits."""
    _, detail = goal_progress_copy(fund.current_balance, fund.target_amount)
    current, goal = _number(fund.current_balance), _number(fund.target_amount)
    fraction = None
    if current is not None and goal is not None and current >= 0 and goal > 0:
        fraction = float(min(current / goal, Decimal(1)))
    # Fund names are user text, not Markdown formatting or links.
    name = re.sub(r'([\\`*_{}\[\]()#+.!|>~-])', r'\\\1', ' '.join(fund.name.split()))
    status = "No target set" if fund.target_amount is None or goal == 0 else "Progress unavailable"
    if ' · ' in detail:
        status, detail = detail.split(' · ', 1)
    saved = f"€{current:,.2f} saved" if current is not None else "Balance unavailable"
    label = f"**{name}** *{status}*  \n{saved}"
    key = f"fund_goal_{int(user_id)}_{int(fund.id)}"
    st.html(fund_card_style(key, fraction))
    with st.container(key=key):
        with st.expander(label):
            if fraction is not None:
                st.caption(detail)
            yield
