import streamlit as st
import pandas as pd
import plotly.express as px
import qrcode
from io import BytesIO

from components.supabase_client import get_supabase
from components.security import admin_login_ok

st.title("🔒 Restricted Area")

if not admin_login_ok():
    st.info("Inserisci la password admin nella sidebar.")
    st.stop()

supabase = get_supabase()

@st.cache_data(ttl=30)
def load_all():
    """
    Carica tutte le tabelle principali con cache breve.
    """
    invites = supabase.table("invites").select("*").execute().data or []
    guests  = supabase.table("guests").select("*").execute().data or []
    rsvps   = supabase.table("rsvps").select("*").execute().data or []
    meals   = supabase.table("meal_options").select("*").execute().data or []
    return invites, guests, rsvps, meals

if st.sidebar.button("🔄 Refresh dati"):
    st.cache_data.clear()

invites, guests, rsvps, meals = load_all()

df_inv = pd.DataFrame(invites)
df_g   = pd.DataFrame(guests)
df_r   = pd.DataFrame(rsvps)
df_m   = pd.DataFrame(meals)

if df_inv.empty:
    st.warning("Nessun invito nel DB. Importa da CSV o usa seed_demo.")
    st.stop()

meal_map = dict(zip(df_m["code"], df_m["label"])) if not df_m.empty else {}

# Dataset “ospiti arricchito”
df = df_g.merge(df_inv, left_on="invite_id", right_on="id", suffixes=("_guest","_invite"))
if not df_r.empty:
    df = df.merge(df_r, left_on="id_guest", right_on="guest_id", how="left")
else:
    df["attending"] = None
    df["meal_choice"] = None
    df["allergies"] = None
    df["notes"] = None

df["meal_label"] = df["meal_choice"].map(meal_map)

# KPI
total = len(df)
yes = int((df["attending"] == True).sum())
no  = int((df["attending"] == False).sum())
unk = int(df["attending"].isna().sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Invitati", total)
c2.metric("Sì", yes)
c3.metric("No", no)
c4.metric("In attesa", unk)

st.divider()

# Filtri
st.sidebar.subheader("Filtri")
status = st.sidebar.multiselect("Presenza", ["Sì","No","In attesa"], default=["Sì","No","In attesa"])
meal_filter = st.sidebar.multiselect("Menù", sorted([m for m in df["meal_label"].dropna().unique()]))

df_f = df.copy()
map_status = {"Sì": True, "No": False, "In attesa": None}
allowed = [map_status[s] for s in status]

if None in allowed:
    df_f = df_f[df_f["attending"].isin([True, False]) | df_f["attending"].isna()]
else:
    df_f = df_f[df_f["attending"].isin(allowed)]

if meal_filter:
    df_f = df_f[df_f["meal_label"].isin(meal_filter)]

# Tabs admin
tab1, tab2, tab3 = st.tabs(["📊 Analytics", "📥 Export", "✉️ Inviti (modifica + QR)"])

with tab1:
    st.subheader("Analytics")

    s_counts = pd.Series({"Sì": yes, "No": no, "In attesa": unk}).reset_index()
    s_counts.columns = ["Stato", "Conteggio"]
    st.plotly_chart(px.bar(s_counts, x="Stato", y="Conteggio"), use_container_width=True)

    df_yes = df[df["attending"] == True].copy()
    meal_counts = df_yes["meal_label"].fillna("Non selezionato").value_counts().reset_index()
    meal_counts.columns = ["Menù", "Conteggio"]
    st.plotly_chart(px.bar(meal_counts, x="Menù", y="Conteggio"), use_container_width=True)

    missing_meal = df_yes[df_yes["meal_label"].isna()][["label","full_name"]]
    if len(missing_meal) > 0:
        st.warning(f"Presenti senza menù selezionato: {len(missing_meal)}")
        st.dataframe(missing_meal, use_container_width=True)

    st.subheader("Allergie – quick scan")
    txt = df_yes["allergies"].dropna().astype(str).str.lower()
    keywords = ["glutine","celiachia","lattosio","latte","frutta secca","noci","arachidi","uova","pesce","crostacei","soia"]
    rows = [{"Allergene": k, "Occorrenze": int(txt.str.contains(k).sum())} for k in keywords]
    st.dataframe(pd.DataFrame(rows).sort_values("Occorrenze", ascending=False), use_container_width=True)

with tab2:
    st.subheader("Export CSV")

    csv_all = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ CSV completo", data=csv_all, file_name="rsvp_export_completo.csv", mime="text/csv")

    csv_filtered = df_f.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ CSV filtrato", data=csv_filtered, file_name="rsvp_export_filtrato.csv", mime="text/csv")

    st.subheader("Vista tabellare (filtrata)")
    st.dataframe(
        df_f[["label","full_name","is_child","attending","meal_label","allergies","notes","updated_at"]],
        use_container_width=True
    )

with tab3:
    st.subheader("Gestione inviti")
    st.caption("Qui puoi modificare **max_guests** e **allow_plus_one** (e anche label se ti serve).")

    # Preparo un editor su invites
    editable = df_inv[["id","code","label","max_guests","allow_plus_one","created_at","updated_at"]].copy()

    edited = st.data_editor(
        editable,
        use_container_width=True,
        num_rows="fixed",
        disabled=["id","code","created_at","updated_at"],  # code NON va cambiato dopo la distribuzione
        column_config={
            "label": st.column_config.TextColumn("Label (nucleo)", required=True),
            "max_guests": st.column_config.NumberColumn("Max ospiti", min_value=1, step=1),
            "allow_plus_one": st.column_config.CheckboxColumn("+1 consentito")
        }
    )

    if st.button("💾 Salva modifiche inviti"):
        # Aggiorno riga per riga (semplice e robusto)
        for _, row in edited.iterrows():
            supabase.table("invites").update({
                "label": row["label"],
                "max_guests": int(row["max_guests"]),
                "allow_plus_one": bool(row["allow_plus_one"])
            }).eq("id", row["id"]).execute()

        st.success("Inviti aggiornati ✅ (premi Refresh dati in sidebar)")
        st.cache_data.clear()

    st.divider()
    st.subheader("Link RSVP + QR")

    base_url = st.secrets.get("BASE_URL", "http://localhost:8501")
    df_codes = edited[["label","code","max_guests","allow_plus_one"]].copy()
    df_codes["rsvp_url"] = df_codes["code"].apply(lambda c: f"{base_url}/RSVP?code={c}")

    st.dataframe(df_codes, use_container_width=True)

    labels = df_codes["label"].tolist()
    pick = st.selectbox("Seleziona invito per QR", labels)
    row = df_codes[df_codes["label"] == pick].iloc[0]
    url = row["rsvp_url"]

    st.code(url, language="text")

    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    st.image(buf.getvalue(), width=220)
    st.download_button(
        "⬇️ Scarica QR PNG",
        data=buf.getvalue(),
        file_name=f"QR_{row['code']}.png",
        mime="image/png"
    )
