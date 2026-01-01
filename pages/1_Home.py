import streamlit as st

st.title("Home")

st.markdown('<div class="card">', unsafe_allow_html=True)
st.write("Benvenuti! Qui trovate tutti i dettagli e potete confermare la presenza.")
st.write("📅 Data: …")
st.write("📍 Luogo: …")
st.write("🕒 Orari indicativi: …")
st.markdown("</div>", unsafe_allow_html=True)

st.divider()

st.subheader("Cosa ti serve?")
c1, c2 = st.columns(2)
with c1:
    st.page_link("pages/3_RSVP.py", label="✅ Conferma RSVP", icon="✅")
with c2:
    st.page_link("pages/2_Dettagli.py", label="🗺️ Dettagli e FAQ", icon="🗺️")
