"""
Genera il link e il QR per la pagina Admin includendo il token (se impostato).

Uso:
  # con valori in .env
  python scripts/generate_admin_qr.py

  # oppure passando il token via argomento
  python scripts/generate_admin_qr.py <token>

Output:
  - Stampa il link completo (BASE_URL/Admin?token=...)
  - Salva il QR in out_qr/admin_access.png
"""

import os
from pathlib import Path

import qrcode
from dotenv import load_dotenv


def main():
    load_dotenv()

    base_url = os.environ.get("BASE_URL", "http://localhost:8501").rstrip("/")
    token = None

    # Token da argv se presente, altrimenti da env
    import sys
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        token = os.environ.get("ADMIN_PAGE_TOKEN")

    if token:
        url = f"{base_url}/Admin?token={token}"
    else:
        url = f"{base_url}/Admin"
        print("⚠️  ADMIN_PAGE_TOKEN non impostato: il link non include token.")

    out_dir = Path("out_qr")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "admin_access.png"

    img = qrcode.make(url)
    img.save(out_file)

    print("\nLink Admin:")
    print(url)
    print(f"\nQR salvato in: {out_file.resolve()}")


if __name__ == "__main__":
    main()
