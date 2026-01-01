import streamlit as st

st.title("Dettagli e FAQ")

with st.expander("📍 Location e come arrivare", expanded=True):
    st.write("- Indirizzo: …")
    st.write("- Parcheggio: …")
    st.write("- Google Maps: …")

with st.expander("🕒 Timeline indicativa"):
    st.write("- Cerimonia: …")
    st.write("- Aperitivo: …")
    st.write("- Pranzo/Cena: …")
    st.write("- Festa: …")

with st.expander("👗 Dress code"):
    st.write("…")

with st.expander("🎁 Regali"):
    st.write("…")

with st.expander("❓ FAQ"):
    st.write("- Posso cambiare risposta? Sì: riapri il link/QR e modifica.")
    st.write("- Allergie? Inseriscile nell’RSVP 🙂")

st.divider()
st.caption("Privacy: raccogliamo solo dati necessari (presenza, menù, allergie).")
