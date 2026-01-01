import bcrypt

"""
Script utilità:
- Chiede una password admin
- Stampa un hash bcrypt da copiare in secrets.toml

Uso:
  python scripts/make_admin_hash.py
"""

pwd = input("Inserisci password admin: ").encode()
hashed = bcrypt.hashpw(pwd, bcrypt.gensalt()).decode()

print("\nADMIN_PASSWORD_HASH (copia questo in secrets.toml):\n")
print(hashed)
