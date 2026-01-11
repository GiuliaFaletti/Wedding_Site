# Wedding Site (Streamlit + Google Sheets)

Applicazione Streamlit per gestire inviti e RSVP di un matrimonio, con raccolta menù/allergie e dashboard amministrativa. I dati ora sono salvati su **Google Sheets** (niente limiti temporali di Supabase).

## Funzionalità
- Home e pagina dettagli con info logistiche per gli invitati.
- Flusso RSVP con codice invito, scelta menù, note/allergie, aggiunta +1 se consentito.
- Dashboard admin con login, KPI, grafici, filtri, export CSV, modifica inviti e generazione QR dei link RSVP.
- Script CLI per creare l'hash bcrypt della password admin.

## Requisiti
- Python 3.10+ consigliato.
- Foglio Google con i worksheet: `invites`, `guests`, `rsvps`, `meal_options`.
- Variabili/segreti Streamlit configurati.

## Installazione
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configurazione Google Sheets
Inserisci in `.streamlit/secrets.toml` (non committare valori reali):
```toml
BASE_URL = "http://localhost:8501"                # cambia con il dominio pubblico in prod
ADMIN_PASSWORD_HASH = "<hash bcrypt da scripts/make_admin_hash.py>"

# JSON del service account Google copiato come oggetto TOML
[gcp_service_account]
type = "service_account"
project_id = "..."
# ...resto dei campi del JSON...

GSPREAD_SHEET_ID = "<id del foglio>"
```
> Condividi il foglio con l'email del service account (campo `client_email` nel JSON).

### Schema worksheet (intestazioni)
- `invites`: `id`, `code`, `label`, `max_guests`, `allow_plus_one`, `created_at`, `updated_at`
- `guests`: `id`, `invite_id`, `full_name`, `is_child`
- `rsvps`: `guest_id`, `attending`, `meal_choice`, `allergies`, `notes`, `updated_at`
- `meal_options`: `code`, `label`, `active`

## Avvio locale
```bash
streamlit run app.py
```
Interfaccia:
- Menu laterale con pagine: Home, Dettagli, RSVP, Admin.
- Per testare il flusso RSVP, passa `?code=<CODICE>` nell'URL (da QR o manualmente).

## Dashboard Admin
- Accesso tramite password (bcrypt) definita in `ADMIN_PASSWORD_HASH`.
- KPI su presenze, grafici plotly per stato e menù.
- Filtri per stato presenza e menù.
- Export CSV completo e filtrato.
- Editor inviti (label, max_guests, allow_plus_one) e generazione link/QR per ogni invito.

## Import da CSV + QR
Lo script Supabase è stato rimosso. Se ti serve un import da CSV verso Google Sheets, possiamo aggiungerlo con gspread (simile a quanto già fatto).

## Creazione hash password admin
```bash
python scripts/make_admin_hash.py
# incolla l'hash in ADMIN_PASSWORD_HASH dentro secrets.toml
```

## Note operative
- Popola `meal_options` nel worksheet dedicato prima di aprire le RSVP (campi `label`, `code`, `active`).
- Per la distribuzione, imposta `BASE_URL` al dominio pubblico così i QR puntano all'host corretto.
- Streamlit usa cache per il client Sheets (`@st.cache_resource`) e per i dati (`@st.cache_data` ttl 30s).
- `requirements.txt` include: streamlit, pandas, plotly, qrcode, Pillow, bcrypt, python-dotenv, gspread, google-auth.

## Struttura del repo
- `app.py`: layout base e routing delle pagine.
- `pages/`: Home, Dettagli/FAQ, RSVP, Admin dashboard.
- `components/`: client Google Sheets, utilità (normalizzazione codice), login admin.
- `scripts/`: generazione hash admin, seed demo placeholder.
- `scripts/generate_admin_qr.py`: genera link/QR per la pagina Admin includendo l'eventuale token.
- `data/`: CSV template inviti.
