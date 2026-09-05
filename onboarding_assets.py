"""Step 2 presentation using existing asset types and liquidity classes."""

import streamlit as st

from assets import add_asset, get_assets


# Display labels only: keys are the existing values used by the dashboard.
ASSET_TYPES = {
    "INVESTMENT": "Investments (such as stocks or ETFs)",
    "REAL_ESTATE": "Property",
    "CAR": "Car",
    "PRIVATE_PROJECT": "Private project",
    "MONEY_OWED_TO_ME": "Money owed to me",
    "OTHER": "Other valuable asset",
}
LIQUIDITY_CLASSES = {
    "LIQUID_INVESTMENT": "Liquid investment",
    "SEMI_LIQUID": "Semi-liquid",
    "NON_LIQUID": "Non-liquid",
}
LIQUIDITY_EXPLANATIONS = {
    "LIQUID_INVESTMENT": "Usually can be converted to cash within a few days.",
    "SEMI_LIQUID": "Has value, but may take more time or effort to access.",
    "NON_LIQUID": "Usually takes longer to sell or convert into usable cash, such as property.",
}


def render_assets_step(user_id):
    """Render inside onboarding_shell(step=2); all draft state belongs to this user."""
    prefix = f"onboarding_{user_id}_"
    form_open_key = prefix + "asset_form_open"
    form_version_key = prefix + "asset_form_version"

    st.title("Do you own any investments or other assets?")
    st.write(
        "This could be investments, property or other valuable assets "
        "you want included in your financial picture."
    )
    st.caption("Use a name and estimated value. Leave out money already listed in your accounts.")

    with st.expander("How readily available is this money?"):
        st.write("This classification helps calculate how much of your wealth is readily available.")
        for value, label in LIQUIDITY_CLASSES.items():
            st.write(f"**{label}:** {LIQUIDITY_EXPLANATIONS[value]}")
        st.caption("Choose separately from the kind of asset. For example, a property is usually non-liquid.")

    try:
        assets = get_assets(user_id)
    except Exception:
        st.error("We couldn't load your assets. Please try again.")
        if st.button("Retry", key=prefix + "assets_retry"):
            st.rerun()
        return

    if st.session_state.pop(prefix + "asset_saved", False):
        st.success("Asset added. Your financial picture is taking shape.")

    if assets:
        st.subheader("Your assets")
        for asset in assets:
            with st.container(border=True):
                st.text(asset.name)
                st.caption(
                    f"{asset.current_value:,.2f} {asset.currency} · "
                    f"{ASSET_TYPES.get(asset.asset_type, 'Asset')} · "
                    f"{LIQUIDITY_CLASSES.get(asset.liquidity_class, 'Availability not specified')}"
                )

    form_open = st.session_state.get(form_open_key, not assets)
    if form_open:
        draft_prefix = prefix + f"asset_draft_{st.session_state.get(form_version_key, 0)}_"
        with st.form(draft_prefix + "form"):
            name = st.text_input(
                "Asset name", placeholder="e.g. My investment portfolio", key=draft_prefix + "name"
            )
            current_value = st.number_input(
                "Current value (EUR)",
                min_value=0.0,
                value=None,
                step=100.0,
                placeholder="e.g. 5000",
                help="Use your best estimate of what it is worth today.",
                key=draft_prefix + "value",
            )
            asset_type = st.selectbox(
                "What kind of asset is it?",
                options=list(ASSET_TYPES),
                index=None,
                placeholder="Choose a kind of asset",
                format_func=ASSET_TYPES.get,
                key=draft_prefix + "type",
            )
            liquidity_class = st.selectbox(
                "How quickly could you access this money?",
                options=list(LIQUIDITY_CLASSES),
                index=None,
                placeholder="Choose how readily available it is",
                format_func=LIQUIDITY_CLASSES.get,
                help="\n\n".join(
                    f"{LIQUIDITY_CLASSES[value]}: {explanation}"
                    for value, explanation in LIQUIDITY_EXPLANATIONS.items()
                ),
                key=draft_prefix + "liquidity",
            )
            submitted = st.form_submit_button("Add asset", type="primary")

        if submitted:
            if not name.strip():
                st.error("Please enter an asset name.")
            elif current_value is None:
                st.error("Please enter the current value. You can enter 0.")
            elif current_value < 0:
                st.error("The value must be 0 or more.")
            elif asset_type not in ASSET_TYPES:
                st.error("Please choose what kind of asset this is.")
            elif liquidity_class not in LIQUIDITY_CLASSES:
                st.error("Please choose how readily available this money is.")
            else:
                try:
                    add_asset(user_id, name, asset_type, liquidity_class, current_value)
                except Exception:
                    st.session_state[prefix + "asset_save_uncertain"] = True
                else:
                    st.session_state[form_open_key] = False
                    st.session_state[form_version_key] = st.session_state.get(form_version_key, 0) + 1
                    st.session_state[prefix + "asset_saved"] = True
                    st.session_state.pop(prefix + "asset_save_uncertain", None)
                    st.rerun()

        if st.session_state.get(prefix + "asset_save_uncertain", False):
            st.error(
                "We couldn't confirm that the asset was saved. "
                "Check the asset list before trying again."
            )
            if st.button("Refresh asset list", key=prefix + "assets_refresh"):
                st.session_state.pop(prefix + "asset_save_uncertain", None)
                st.rerun()

        if assets and st.button("Cancel", key=prefix + "asset_cancel"):
            st.session_state[form_open_key] = False
            st.rerun()
    elif assets:
        if st.button("Continue", type="primary", key=prefix + "assets_continue"):
            st.session_state[prefix + "step"] = "debts"
            st.rerun()
        if st.button("Add another", key=prefix + "asset_another"):
            st.session_state[form_open_key] = True
            st.rerun()

    if form_open:
        st.caption("Only saved assets will be included. You can add more later.")
        if st.button(
            "I don't have any yet" if not assets else "Skip for now",
            key=prefix + "assets_skip",
        ):
            # Skipping never creates or modifies an asset, including a draft.
            st.session_state[prefix + "step"] = "debts"
            st.rerun()

    if st.button("Back to Accounts", key=prefix + "assets_back"):
        st.session_state[prefix + "step"] = "accounts"
        st.rerun()
