import re

def normalize_code(code: str) -> str:
    """
    Normalizza il codice invito per ridurre errori:
    - trim
    - uppercase
    - rimuove caratteri non alfanumerici
    """
    if not code:
        return ""
    code = code.strip().upper()
    code = re.sub(r"[^A-Z0-9]", "", code)
    return code

