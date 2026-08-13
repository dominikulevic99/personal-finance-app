import streamlit as st


st.set_page_config(
    page_title="Auth Test"
)


if not st.user.is_logged_in:

    st.title("Not logged in")

    if st.button("Log in"):
        st.login()

    st.stop()


st.success("LOGIN WORKS")

st.write(
    f"Email: {st.user.email}"
)

st.write(
    f"Name: {st.user.get('name', '')}"
)

if st.button("Log out"):
    st.logout()
