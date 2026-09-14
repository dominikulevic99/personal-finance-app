"""One optional, localized feedback dialog; no financial data is read."""

import streamlit as st
from feedback import FEEDBACK_OPTIONS, add_feedback, get_user_feedback
from i18n import t, get_language, set_language


def open_feedback(user_id, source, *, automatic=False):
    if source not in ("sidebar", "product_tour"):
        raise ValueError("Invalid feedback source.")
    prefix = f"feedback_{user_id}_"
    st.session_state[prefix + "source"] = source
    st.session_state[prefix + "open"] = True
    st.session_state[prefix + "submitted"] = False
    st.session_state[prefix + "automatic"] = automatic
    st.session_state[prefix + "offered"] = True
    st.session_state[prefix + "pending"] = False


def select_option(user_id, option):
    prefix = f"feedback_{user_id}_option_"
    if st.session_state.get(prefix + option, False):
        for other in FEEDBACK_OPTIONS:
            if other != option and (option == "nothing_missing" or other == "nothing_missing"):
                st.session_state[prefix + other] = False


def offer_tour_feedback(user_id):
    prefix = f"feedback_{user_id}_"
    if st.session_state.get(prefix + "offered") or st.session_state.get(prefix + "has_submitted"):
        return False
    if prefix + "has_submitted" not in st.session_state:
        try:
            st.session_state[prefix + "has_submitted"] = bool(get_user_feedback(user_id))
        except Exception:
            return False  # Feedback must never prevent using the product.
    return not st.session_state[prefix + "has_submitted"]


def render_feedback(user_id):
    prefix = f"feedback_{user_id}_"
    if not st.session_state.get(prefix + "open", False):
        return

    def close():
        st.session_state[prefix + "open"] = False

    automatic = st.session_state.get(prefix + "automatic", False)
    @st.dialog(t("feedback.intro") if automatic else t("feedback.question"), on_dismiss=close)
    def dialog():
        language_key = prefix + "language"
        # Keep the dialog's selector in sync when reopened from the sidebar.
        if language_key not in st.session_state:
            st.session_state[language_key] = get_language()

        def change_language():
            selected = st.session_state.get(language_key)
            if selected not in ("lt", "en"):
                st.session_state[language_key] = get_language()
                return
            set_language(selected)
            scope = st.session_state.get("_i18n_scope", f"user_{user_id}")
            st.session_state[f"_i18n_{scope}_switch"] = get_language()
            st.session_state[prefix + "language_changed"] = True

        st.segmented_control(t("feedback.language"), options=("lt", "en"), format_func=str.upper,
                             key=language_key, on_change=change_language, label_visibility="collapsed")
        if st.session_state.get(prefix + "submitted", False):
            st.success(t("feedback.success"))
        else:
            if automatic:
                st.write(t("feedback.question"))
            if st.button(t("feedback.not_now"), key=prefix + "not_now", type="tertiary"):
                close()
                st.rerun()
            st.caption(t("feedback.support"))
            for option in FEEDBACK_OPTIONS:
                st.checkbox(t(f"feedback.option.{option}"), key=prefix + "option_" + option,
                            on_change=select_option, args=(user_id, option))
            if st.session_state.get(prefix + "option_other"):
                st.caption(t("feedback.other_help"))
            message = st.text_area(t("feedback.comment"), placeholder=t("feedback.placeholder"),
                                   key=prefix + "comment")
            st.caption(t("feedback.comment_help"))
            if st.button(t("feedback.submit"), type="primary", key=prefix + "submit"):
                options = [option for option in FEEDBACK_OPTIONS if st.session_state.get(prefix + "option_" + option)]
                if not options and not message.strip():
                    st.info(t("feedback.empty"))
                else:
                    try:
                        add_feedback(user_id, message, options, st.session_state[prefix + "source"])
                    except Exception:
                        st.error(t("feedback.error"))
                    else:
                        st.session_state[prefix + "submitted"] = True
                        st.session_state[prefix + "has_submitted"] = True
                        st.session_state.pop(prefix + "comment", None)
                        # Fresh widget keys are not needed: clear only on the next opening.
                        st.session_state[prefix + "clear_draft"] = True
                        st.rerun()
        if st.session_state.get(prefix + "submitted", False) and st.button(
            t("feedback.return"), key=prefix + "return", type="tertiary"
        ):
            close()
            st.rerun()
        # Render draft widgets before the app rerun, so Streamlit retains their
        # keys while updating the dialog title and the sidebar language selector.
        if st.session_state.pop(prefix + "language_changed", False):
            st.rerun()

    if st.session_state.pop(prefix + "clear_draft", False):
        for option in FEEDBACK_OPTIONS:
            st.session_state.pop(prefix + "option_" + option, None)
    st.session_state[prefix + "language"] = get_language()
    dialog()
