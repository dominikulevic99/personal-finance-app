"""Step 2 presentation using existing asset types and liquidity classes."""

import streamlit as st
from i18n import t, TranslatedLabels, month_period

from assets import add_asset, get_assets


# Display labels only: keys are the existing values used by the dashboard.
ASSET_TYPES = TranslatedLabels({
    "INVESTMENT": 'ui.investments_such_as_stocks_or_etfs',
    "REAL_ESTATE": 'ui.property',
    "CAR": 'ui.car',
    "PRIVATE_PROJECT": 'ui.private_project',
    "MONEY_OWED_TO_ME": 'ui.money_owed_to_me',
    "OTHER": 'ui.other_valuable_asset',
})
LIQUIDITY_CLASSES = TranslatedLabels({
    "LIQUID_INVESTMENT": 'ui.liquid_investment',
    "SEMI_LIQUID": 'ui.semi_liquid',
    "NON_LIQUID": 'ui.non_liquid',
})
LIQUIDITY_EXPLANATIONS = TranslatedLabels({
    "LIQUID_INVESTMENT": 'ui.usually_can_be_converted_to_cash_within_a_few_days',
    "SEMI_LIQUID": 'ui.has_value_but_may_take_more_time_or_effort_to',
    "NON_LIQUID": 'ui.usually_takes_longer_to_sell_or_convert_into_usable_cash',
})


def render_assets_step(user_id):
    """Render inside onboarding_shell(step=2); all draft state belongs to this user."""
    prefix = f"onboarding_{user_id}_"
    form_open_key = prefix + "asset_form_open"
    form_version_key = prefix + "asset_form_version"

    st.title(t('ui.now_add_what_you_own_beyond_cash'))
    st.write(
        t('ui.investments_property_and_other_assets_complete_the_picture_of_what')
    )
    st.caption(t('ui.use_a_name_and_estimated_value_leave_out_money_already'))

    with st.expander(t('ui.how_readily_available_is_this_money')):
        st.write(t('ui.this_classification_helps_calculate_how_much_of_your_wealth_is'))
        for value, label in LIQUIDITY_CLASSES.items():
            st.write(f"**{label}:** {LIQUIDITY_EXPLANATIONS[value]}")
        st.caption(t('ui.choose_separately_from_the_kind_of_asset_for_example_a'))

    try:
        assets = get_assets(user_id)
    except Exception:
        st.error(t('ui.we_couldn_t_load_your_assets_please_try_again'))
        if st.button(t('ui.retry'), key=prefix + "assets_retry"):
            st.rerun()
        return

    if st.session_state.pop(prefix + "asset_saved", False):
        st.success(t('ui.asset_added_your_financial_picture_is_taking_shape'))

    if assets:
        st.subheader(t('ui.your_assets'))
        for asset in assets:
            with st.container(border=True):
                st.text(asset.name)
                st.caption(
                    f"{asset.current_value:,.2f} {asset.currency} · "
                    f"{ASSET_TYPES.get(asset.asset_type, t('ui.asset'))} · "
                    f"{LIQUIDITY_CLASSES.get(asset.liquidity_class, t('ui.availability_not_specified'))}"
                )

    form_open = st.session_state.get(form_open_key, not assets)
    if form_open:
        draft_prefix = prefix + f"asset_draft_{st.session_state.get(form_version_key, 0)}_"
        with st.form(draft_prefix + "form"):
            name = st.text_input(
                t('ui.asset_name'), placeholder=t('ui.e_g_my_investment_portfolio'), key=draft_prefix + "name"
            )
            current_value = st.number_input(
                t('ui.current_value_eur'),
                min_value=0.0,
                value=None,
                step=100.0,
                placeholder=t('ui.e_g_5000'),
                help=t('ui.use_your_best_estimate_of_what_it_is_worth_today'),
                key=draft_prefix + "value",
            )
            asset_type = st.selectbox(
                t('ui.what_kind_of_asset_is_it'),
                options=list(ASSET_TYPES),
                index=None,
                placeholder=t('ui.choose_a_kind_of_asset'),
                format_func=ASSET_TYPES.formatter(),
                key=draft_prefix + "type",
            )
            liquidity_class = st.selectbox(
                t('ui.how_quickly_could_you_access_this_money'),
                options=list(LIQUIDITY_CLASSES),
                index=None,
                placeholder=t('ui.choose_how_readily_available_it_is'),
                format_func=LIQUIDITY_CLASSES.formatter(),
                help="\n\n".join(
                    f"{LIQUIDITY_CLASSES[value]}: {explanation}"
                    for value, explanation in LIQUIDITY_EXPLANATIONS.items()
                ),
                key=draft_prefix + "liquidity",
            )
            submitted = st.form_submit_button(t('ui.add_asset'), type="primary")

        if submitted:
            if not name.strip():
                st.error(t('ui.please_enter_an_asset_name'))
            elif current_value is None:
                st.error(t('ui.please_enter_the_current_value_you_can_enter_0'))
            elif current_value < 0:
                st.error(t('ui.the_value_must_be_0_or_more'))
            elif asset_type not in ASSET_TYPES:
                st.error(t('ui.please_choose_what_kind_of_asset_this_is'))
            elif liquidity_class not in LIQUIDITY_CLASSES:
                st.error(t('ui.please_choose_how_readily_available_this_money_is'))
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
                t('ui.we_couldn_t_confirm_that_the_asset_was_saved_check')
            )
            if st.button(t('ui.refresh_asset_list'), key=prefix + "assets_refresh"):
                st.session_state.pop(prefix + "asset_save_uncertain", None)
                st.rerun()

        if assets and st.button(t('ui.cancel'), type="tertiary", key=prefix + "asset_cancel"):
            st.session_state[form_open_key] = False
            st.rerun()
    elif assets:
        if st.button(t('actions.continue'), type="primary", key=prefix + "assets_continue"):
            st.session_state[prefix + "step"] = "debts"
            st.rerun()
        if st.button(t('ui.add_another'), key=prefix + "asset_another"):
            st.session_state[form_open_key] = True
            st.rerun()

    if form_open:
        st.caption(t('ui.only_saved_assets_will_be_included_you_can_add_more'))
        if st.button(
            t('ui.i_don_t_have_any_yet') if not assets else t('ui.skip_for_now'),
            type="tertiary",
            key=prefix + "assets_skip",
        ):
            # Skipping never creates or modifies an asset, including a draft.
            st.session_state[prefix + "step"] = "debts"
            st.rerun()

    if st.button(t('ui.back_to_accounts'), type="tertiary", key=prefix + "assets_back"):
        st.session_state[prefix + "step"] = "accounts"
        st.rerun()
