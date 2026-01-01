# Wedding Site (Streamlit + Supabase)

Applicazione Streamlit per gestire inviti e RSVP di un matrimonio, con raccolta menù/allergie e dashboard amministrativa collegata a Supabase.

## Funzionalità
- Home e pagina dettagli con info logistiche per gli invitati.
- Flusso RSVP con codice invito, scelta menù, note/allergie, aggiunta +1 se consentito.
- Dashboard admin con login, KPI, grafici, filtri, export CSV, modifica inviti e generazione QR dei link RSVP.
- Script CLI per importare nuclei da CSV e generare QR, e per creare l'hash bcrypt della password admin.

## Requisiti
- Python 3.10+ consigliato.
- Account Supabase con le tabelle `invites`, `guests`, `rsvps`, `meal_options`.
- Variabili/segreti Streamlit configurati.

## Installazione
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configurazione Supabase
Inserisci in `.streamlit/secrets.toml` (non committare valori reali):
```toml
SUPABASE_URL = "<url del progetto>"
SUPABASE_SERVICE_KEY = "<service role key>"
BASE_URL = "http://localhost:8501"   # cambia con il dominio pubblico in prod
ADMIN_PASSWORD_HASH = "<hash bcrypt da scripts/make_admin_hash.py>"
```
> Nota: viene usata la **service role key** lato server Streamlit; non esporla mai client-side.

### Schema tabelle (essenziale)
- `invites`: `id`, `label` (unique), `code` (unique), `max_guests`, `allow_plus_one`.
- `guests`: `id`, `invite_id` (FK), `full_name`, `is_child`, unique su (`invite_id`, `full_name`).
- `rsvps`: `id`, `guest_id` (FK, unique), `attending` (bool/null), `meal_choice`, `allergies`, `notes`, `updated_at`.
- `meal_options`: `id`, `label`, `code` (es. `STANDARD`, `VEG`), `active` (bool).

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
Usa il template `data/invites_template.csv` (colonne: `invite_label,max_guests,allow_plus_one,guest_full_name,is_child`).
```bash
export SUPABASE_URL="..."
export SUPABASE_SERVICE_KEY="..."
export BASE_URL="http://localhost:8501"   # o dominio prod
python scripts/import_from_csv.py data/invites_template.csv
```
Lo script:
- crea/aggiorna inviti per ogni `invite_label`,
- inserisce gli ospiti,
- genera QR e `out_qr/invites_mapping.csv` con mapping label/code/url.

## Creazione hash password admin
```bash
python scripts/make_admin_hash.py
# incolla l'hash in ADMIN_PASSWORD_HASH dentro secrets.toml
```

## Note operative
- Popola `meal_options` in Supabase prima di aprire le RSVP (campi `label`, `code`, `active`).
- Per la distribuzione, imposta `BASE_URL` al dominio pubblico così i QR puntano all'host corretto.
- Streamlit userà la cache per il client Supabase (`@st.cache_resource`) e per i dati admin (`@st.cache_data` ttl 30s).
- `requirements.txt` include: streamlit, supabase, pandas, plotly, qrcode, Pillow, bcrypt, python-dotenv.

## Struttura del repo
- `app.py`: layout base e routing delle pagine.
- `pages/`: Home, Dettagli/FAQ, RSVP, Admin dashboard.
- `components/`: client Supabase, utilità (normalizzazione codice), login admin.
- `scripts/`: import CSV + QR, generazione hash admin, seed demo placeholder.
- `data/`: CSV template inviti.
