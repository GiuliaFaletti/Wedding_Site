import streamlit as st
import pandas as pd

from components.supabase_client import get_supabase
from components.utils import normalize_code

st.title("✅ RSVP – Conferma presenza")

supabase = get_supabase()

# -----------------------------
# 1) Leggo il code dall'URL (QR)
# -----------------------------
qp = st.query_params
prefill = qp.get("code", "")
if isinstance(prefill, list):
    prefill = prefill[0] if prefill else ""

# -----------------------------
# 2) Session state: memorizzo invito e dati
# -----------------------------
if "invite_loaded" not in st.session_state:
    st.session_state.invite_loaded = False
    st.session_state.invite = None
    st.session_state.guests = []
    st.session_state.rsvps_by_guest = {}
    st.session_state.go_summary = False

# Input codice invito
code = st.text_input("Codice invito", value=prefill, help="Lo trovi nel QR o sul cartoncino.")
code = normalize_code(code)

def fetch_invite_bundle(invite_code: str):
    """
    Carica:
      - invito (invites)
      - ospiti collegati (guests)
      - eventuali rsvp (rsvps)

    Ritorna (inv, guests, rsvps_by_guest).
    """
    inv_res = supabase.table("invites").select("*").eq("code", invite_code).limit(1).execute()
    inv_list = inv_res.data or []
    if not inv_list:
        return None, [], {}

    inv = inv_list[0]

    g_res = supabase.table("guests").select("id, full_name, is_child").eq("invite_id", inv["id"]).execute()
    guests = g_res.data or []

    rsvps = []
    if guests:
        ids = [g["id"] for g in guests]
        r_res = supabase.table("rsvps").select("*").in_("guest_id", ids).execute()
        rsvps = r_res.data or []

    rsvps_by_guest = {r["guest_id"]: r for r in rsvps}
    return inv, guests, rsvps_by_guest

def reload_bundle():
    """Ricarica da DB e salva tutto in session_state."""
    inv, guests, rsvps_by_guest = fetch_invite_bundle(code)
    st.session_state.invite = inv
    st.session_state.guests = guests
    st.session_state.rsvps_by_guest = rsvps_by_guest
    st.session_state.invite_loaded = inv is not None

# -----------------------------
# 3) UI: carica invito
# -----------------------------
c_load, c_help = st.columns([1, 1])

with c_load:
    if st.button("Carica invito", type="primary", disabled=not bool(code)):
        reload_bundle()

with c_help:
    if st.button("Ho problemi col codice"):
        st.info("Scrivici su WhatsApp/telefono 🙂 (metti qui i contatti)")

# Autoload se arrivo da QR
if code and not st.session_state.invite_loaded and prefill:
    reload_bundle()

if not st.session_state.invite_loaded:
    st.markdown('<p class="small-muted">Suggerimento: se hai un QR, il codice si compila automaticamente.</p>', unsafe_allow_html=True)
    st.stop()

inv = st.session_state.invite
guests = st.session_state.guests
rsvps_by_guest = st.session_state.rsvps_by_guest

st.success(f"Invito trovato ✅ — **{inv.get('label', 'Il tuo invito')}**")
st.caption("Puoi salvare ora e modificare più tardi riaprendo lo stesso link/QR.")

# -----------------------------
# 4) Carico opzioni menù
# -----------------------------
meal_opts = supabase.table("meal_options").select("*").eq("active", True).execute().data or []
meal_label_to_code = {m["label"]: m["code"] for m in meal_opts}
meal_code_to_label = {m["code"]: m["label"] for m in meal_opts}
meal_labels = list(meal_label_to_code.keys()) if meal_label_to_code else ["Menù unico"]


def render_summary():
    """Riepilogo presenze/menù in formato tabellare."""
    rows = []
    for g in guests:
        prev = rsvps_by_guest.get(g["id"], {})
        att = prev.get("attending")
        att_txt = "In attesa" if att is None else ("Sì" if att else "No")
        meal_txt = meal_code_to_label.get(prev.get("meal_choice"), "") if att is True else ""

        rows.append({
            "Nome": g["full_name"],
            "Presenza": att_txt,
            "Menù": meal_txt,
            "Allergie": prev.get("allergies") or "",
            "Note": prev.get("notes") or ""
        })

    st.subheader("Riepilogo")
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
    st.info("Vuoi modificare? Torna su **Conferma**, cambia e premi **Salva**.")

# -----------------------------
# 5) Azioni rapide (UX nuclei)
# -----------------------------
st.divider()
st.subheader("Azioni rapide")

a1, a2, a3 = st.columns(3)

with a1:
    if st.button("Imposta tutti: Sì"):
        for g in guests:
            st.session_state[f"att_{g['id']}"] = "Sì"

with a2:
    if st.button("Imposta tutti: No"):
        for g in guests:
            st.session_state[f"att_{g['id']}"] = "No"

with a3:
    if st.button("Copia menù sul gruppo"):
        # copia il menù dal primo "Sì" trovato agli altri "Sì"
        first_meal = None
        for g in guests:
            if st.session_state.get(f"att_{g['id']}") == "Sì":
                first_meal = st.session_state.get(f"meal_{g['id']}")
                break
        if first_meal:
            for g in guests:
                if st.session_state.get(f"att_{g['id']}") == "Sì":
                    st.session_state[f"meal_{g['id']}"] = first_meal
        else:
            st.warning("Seleziona prima almeno un 'Sì' e un menù per qualcuno.")

st.divider()

# -----------------------------
# 6) Tabs: Conferma / Riepilogo
# -----------------------------
tab1, tab2 = st.tabs(["📝 Conferma", "📌 Riepilogo"])

updated_rows = []

with tab1:
    st.write("Conferma per ogni persona e premi **Salva** in fondo.")
    completed = 0

    for g in guests:
        prev = rsvps_by_guest.get(g["id"], {})

        st.markdown(f"### {g['full_name']}" + (" 👶" if g.get("is_child") else ""))

        # default radio da DB
        default_att = "Non so ancora"
        if prev.get("attending") is True:
            default_att = "Sì"
        elif prev.get("attending") is False:
            default_att = "No"

        attending = st.radio(
            "Presenza",
            ["Non so ancora", "Sì", "No"],
            index=["Non so ancora","Sì","No"].index(st.session_state.get(f"att_{g['id']}", default_att)),
            key=f"att_{g['id']}",
            horizontal=True
        )

        meal = None
        if attending == "Sì":
            # preselezione menù precedente
            prev_code = prev.get("meal_choice")
            prev_label = meal_code_to_label.get(prev_code)

            meal = st.selectbox(
                "Scelta menù",
                meal_labels,
                index=meal_labels.index(prev_label) if prev_label in meal_labels else 0,
                key=f"meal_{g['id']}"
            )

        allergies = st.text_area(
            "Allergie / Intolleranze (se nessuna, lascia vuoto)",
            value=st.session_state.get(f"all_{g['id']}", prev.get("allergies") or ""),
            key=f"all_{g['id']}",
            height=70
        )

        notes = st.text_area(
            "Note (accessibilità, passeggini, ecc.)",
            value=st.session_state.get(f"notes_{g['id']}", prev.get("notes") or ""),
            key=f"notes_{g['id']}",
            height=70
        )

        if attending != "Non so ancora":
            completed += 1

        updated_rows.append({
            "guest_id": g["id"],
            "attending": None if attending == "Non so ancora" else (attending == "Sì"),
            "meal_choice": meal_label_to_code.get(meal) if (attending == "Sì" and meal) else None,
            "allergies": allergies.strip() or None,
            "notes": notes.strip() or None
        })

        st.divider()

    st.progress(completed / max(len(guests), 1))
    st.caption(f"Completati: {completed}/{len(guests)}")

    # +1: consentito solo se allow_plus_one = True e non si supera max_guests
    if inv.get("allow_plus_one"):
        st.subheader("➕ Aggiungi accompagnatore")
        st.caption("Questa opzione appare solo se prevista dal tuo invito.")
        new_name = st.text_input("Nome e cognome accompagnatore")

        if st.button("Aggiungi", disabled=not bool(new_name.strip())):
            current = len(guests)
            if current >= int(inv.get("max_guests", 1)):
                st.error("Hai già raggiunto il numero massimo di persone per questo invito.")
            else:
                supabase.table("guests").insert({
                    "invite_id": inv["id"],
                    "full_name": new_name.strip(),
                    "is_child": False
                }).execute()
                st.success("Accompagnatore aggiunto ✅ Ricarico invito…")
                reload_bundle()
                st.rerun()

    # Bottoni salva
    c1, c2, c3 = st.columns([1, 1, 1])

    with c1:
        if st.button("Salva", type="primary"):
            for row in updated_rows:
                supabase.table("rsvps").upsert(row, on_conflict="guest_id").execute()
            st.success("RSVP salvata ✅")
            reload_bundle()
            st.rerun()

    with c2:
        if st.button("Salva e mostra il riepilogo"):
            for row in updated_rows:
                supabase.table("rsvps").upsert(row, on_conflict="guest_id").execute()
            st.success("Salvato ✅")
            reload_bundle()
            st.session_state.go_summary = True
            st.rerun()

    with c3:
        if st.button("Ricarica dati"):
            reload_bundle()
            st.info("Dati ricaricati.")

    # Mostra subito il riepilogo dopo l'azione "Salva e vai al riepilogo"
    if st.session_state.get("go_summary"):
        st.session_state.go_summary = False
        st.divider()
        st.success("Ecco il riepilogo aggiornato ✅")
        render_summary()

with tab2:
    render_summary()
