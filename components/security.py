import bcrypt
import streamlit as st

def admin_login_ok() -> bool:
    """
    Login admin "semplice ma decente":
    - password inserita in sidebar
    - confronto con hash bcrypt salvato in secrets

    Ritorna True se ok, False altrimenti.
    """
    st.sidebar.subheader("Admin")
    pwd = st.sidebar.text_input("Password admin", type="password")

    if not pwd:
        return False

    stored_hash = st.secrets["ADMIN_PASSWORD_HASH"].encode()
    ok = bcrypt.checkpw(pwd.encode(), stored_hash)

    if not ok:
        st.sidebar.error("Password errata")

    return ok
