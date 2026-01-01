import streamlit as st

st.set_page_config(
    page_title="Home – Il nostro matrimonio",
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

st.markdown('<div class="card">', unsafe_allow_html=True)
st.write("Benvenuti! Qui trovate tutte le informazioni e potete confermare la presenza.")
st.write("📅 Data: …")
st.write("📍 Luogo: …")
st.write("🕒 Orari indicativi: …")
st.markdown("</div>", unsafe_allow_html=True)

st.divider()
st.subheader("Come navigare")
st.write("- Nel menu a sinistra trovi tutte le sezioni. Se usi il telefono, tocca l’icona in alto a sinistra per aprirlo.")
st.write("- Vai su **RSVP** per inserire il codice invito e confermare chi partecipa (puoi modificare in seguito).")
st.write("- In **Dettagli e FAQ** trovi indicazioni pratiche, orari e contatti.")
st.write("- Se sei uno degli organizzatori, usa **Restricted Area** con la password per vedere il pannello admin.")

st.divider()
st.subheader("Vai subito alla sezione che ti serve")
c1, c2 = st.columns(2)
with c1:
    st.page_link("pages/3_RSVP.py", label="✅ Conferma RSVP", icon="✅")
with c2:
    st.page_link("pages/2_Dettagli.py", label="🗺️ Dettagli e FAQ", icon="🗺️")

st.markdown('<p class="small-muted">Suggerimento: se hai un QR, il codice invito si compila da solo aprendo RSVP.</p>', unsafe_allow_html=True)
