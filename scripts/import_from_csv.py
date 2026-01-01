import os
import csv
import secrets
from pathlib import Path

import qrcode
from supabase import create_client

"""
Import da CSV "a nucleo" + generazione QR.

Cosa fa:
1) Legge il CSV con colonne:
   invite_label,max_guests,allow_plus_one,guest_full_name,is_child
2) Raggruppa per invite_label (nucleo)
3) Per ogni nucleo:
   - se invito esiste (label UNIQUE) -> lo aggiorna (max_guests, allow_plus_one)
   - altrimenti crea invito nuovo con code casuale
   - inserisce i guests (evita duplicati grazie al vincolo unique(invite_id, full_name))
4) Genera QR per ogni invito e salva un CSV di mapping (label->code->url)

Uso:
  export SUPABASE_URL="..."
  export SUPABASE_SERVICE_KEY="..."
  export BASE_URL="http://localhost:8501"   # o dominio in produzione
  python scripts/import_from_csv.py data/invites_template.csv
"""

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

def make_code(n=10):
    """Codice invito robusto (10 char, non ambigui)."""
    return "".join(secrets.choice(ALPHABET) for _ in range(n))

def parse_bool(x: str) -> bool:
    return str(x).strip().lower() in ["true", "1", "yes", "y"]

def main(csv_path: str):
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    base_url = os.environ.get("BASE_URL", "http://localhost:8501")

    supabase = create_client(url, key)

    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV non trovato: {csv_path}")

    # 1) Leggo righe CSV
    rows = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    # 2) Raggruppo per invite_label
    grouped = {}
    for r in rows:
        label = (r.get("invite_label") or "").strip()
        if not label:
            raise ValueError("Trovata riga senza invite_label.")
        grouped.setdefault(label, []).append(r)

    out_dir = Path("out_qr")
    out_dir.mkdir(exist_ok=True)

    mapping_rows = []

    for label, members in grouped.items():
        # Prendo config nucleo dalla prima riga (ripetuta nel CSV)
        max_guests = int(members[0].get("max_guests") or 1)
        allow_plus_one = parse_bool(members[0].get("allow_plus_one") or "false")

        # 3) Controllo se invito esiste già (label è UNIQUE)
        inv_res = supabase.table("invites").select("*").eq("label", label).limit(1).execute()
        inv_list = inv_res.data or []

        if inv_list:
            inv = inv_list[0]
            code = inv["code"]

            # Aggiorno parametri (così puoi re-importare e aggiornare da CSV)
            supabase.table("invites").update({
                "max_guests": max_guests,
                "allow_plus_one": allow_plus_one
            }).eq("id", inv["id"]).execute()
        else:
            code = make_code(10)
            inv = supabase.table("invites").insert({
                "label": label,
                "code": code,
                "max_guests": max_guests,
                "allow_plus_one": allow_plus_one
            }).execute().data[0]

        # 4) Inserisco i guests (se già esistono, il vincolo unique impedirà il duplicato)
        for m in members:
            full_name = (m.get("guest_full_name") or "").strip()
            if not full_name:
                continue
            is_child = parse_bool(m.get("is_child") or "false")

            # Insert semplice: se è duplicato, Supabase ritorna errore.
            # Per robustezza, potresti gestire l'errore; qui facciamo check preventivo.
            existing = supabase.table("guests").select("id").eq("invite_id", inv["id"]).eq("full_name", full_name).limit(1).execute().data
            if existing:
                continue

            supabase.table("guests").insert({
                "invite_id": inv["id"],
                "full_name": full_name,
                "is_child": is_child
            }).execute()

        # 5) Genero link e QR
        rsvp_url = f"{base_url}/RSVP?code={code}"
        img = qrcode.make(rsvp_url)
        img_path = out_dir / f"{label.replace(' ', '_')}_{code}.png"
        img.save(img_path)

        mapping_rows.append({
            "invite_label": label,
            "code": code,
            "max_guests": max_guests,
            "allow_plus_one": allow_plus_one,
            "rsvp_url": rsvp_url,
            "qr_file": str(img_path)
        })

        print(f"[OK] {label} -> {rsvp_url}")

    # 6) Salvo mapping CSV (utile per stampa / invio)
    mapping_csv = out_dir / "invites_mapping.csv"
    with mapping_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=mapping_rows[0].keys())
        w.writeheader()
        w.writerows(mapping_rows)

    print(f"\nFatto ✅ QR in {out_dir}/ e mapping: {mapping_csv}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python scripts/import_from_csv.py <path_csv>")
        raise SystemExit(1)
    main(sys.argv[1])
