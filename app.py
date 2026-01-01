import streamlit as st

st.set_page_config(
    page_title="Il nostro matrimonio",
    page_icon="💍",
    layout="centered"
)

# CSS minimale per card e testi secondari
st.markdown("""
<style>
.small-muted {opacity:0.7; font-size:0.9rem;}
.card {padding: 1rem; border: 1px solid rgba(0,0,0,0.08); border-radius: 14px;}
hr {margin: 1.2rem 0;}
</style>
""", unsafe_allow_html=True)

st.title("💍 Il nostro matrimonio")
st.write("Usa il menu a sinistra per navigare tra le pagine.")
st.info("Se sei un ospite, vai su **RSVP** per confermare la presenza.")
