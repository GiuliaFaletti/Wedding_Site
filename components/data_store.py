import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

INVITES_HEADERS = ["id", "code", "label", "max_guests", "allow_plus_one", "created_at", "updated_at"]
GUESTS_HEADERS = ["id", "invite_id", "full_name", "is_child"]
RSVPS_HEADERS = ["guest_id", "attending", "meal_choice", "allergies", "notes", "updated_at"]
MEAL_HEADERS = ["code", "label", "active"]


def _to_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    s = str(val).strip().lower()
    return s in ("true", "1", "yes", "y", "ok", "x", "si", "sì")


def _to_opt_bool(val: Any) -> Optional[bool]:
    if val in ("", None):
        return None
    return _to_bool(val)


def _to_int(val: Any, default: int = 0) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


@st.cache_resource
def _get_spreadsheet():
    """
    Restituisce l'oggetto Spreadsheet autenticato con il service account.
    Richiede:
      - st.secrets["gcp_service_account"] (dict del JSON)
      - st.secrets["GSPREAD_SHEET_ID"] (stringa)
    """
    info = st.secrets["gcp_service_account"]
    sheet_id = st.secrets["GSPREAD_SHEET_ID"]

    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id)


def _worksheet_and_rows(name: str) -> Tuple[gspread.Worksheet, List[Dict[str, Any]]]:
    ws = _get_spreadsheet().worksheet(name)
    return ws, ws.get_all_records()


@st.cache_data(ttl=30)
def load_all_data() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    invites = load_invites()
    guests = load_guests()
    rsvps = load_rsvps()
    meals = load_meal_options()
    return invites, guests, rsvps, meals


def refresh_cache():
    load_all_data.clear()


def load_invites() -> List[Dict[str, Any]]:
    _, rows = _worksheet_and_rows("invites")
    data = []
    for r in rows:
        data.append(
            {
                "id": str(r.get("id") or "").strip(),
                "code": str(r.get("code") or "").strip(),
                "label": r.get("label") or "",
                "max_guests": _to_int(r.get("max_guests"), 1),
                "allow_plus_one": _to_bool(r.get("allow_plus_one")),
                "created_at": r.get("created_at") or "",
                "updated_at": r.get("updated_at") or "",
            }
        )
    return data


def load_guests() -> List[Dict[str, Any]]:
    _, rows = _worksheet_and_rows("guests")
    data = []
    for r in rows:
        data.append(
            {
                "id": str(r.get("id") or "").strip(),
                "invite_id": str(r.get("invite_id") or "").strip(),
                "full_name": r.get("full_name") or "",
                "is_child": _to_bool(r.get("is_child")),
            }
        )
    return data


def load_rsvps() -> List[Dict[str, Any]]:
    _, rows = _worksheet_and_rows("rsvps")
    data = []
    for r in rows:
        data.append(
            {
                "guest_id": str(r.get("guest_id") or "").strip(),
                "attending": _to_opt_bool(r.get("attending")),
                "meal_choice": r.get("meal_choice") or None,
                "allergies": r.get("allergies") or None,
                "notes": r.get("notes") or None,
                "updated_at": r.get("updated_at") or "",
            }
        )
    return data


def load_meal_options() -> List[Dict[str, Any]]:
    _, rows = _worksheet_and_rows("meal_options")
    data = []
    for r in rows:
        data.append(
            {
                "code": str(r.get("code") or "").strip(),
                "label": r.get("label") or "",
                "active": _to_bool(r.get("active")),
            }
        )
    return data


def _find_row_index(rows: List[Dict[str, Any]], key: str, value: str) -> Optional[int]:
    for idx, r in enumerate(rows, start=2):  # dati partono dalla riga 2
        if str(r.get(key) or "") == str(value):
            return idx
    return None


def update_invite(invite: Dict[str, Any]) -> None:
    ws, rows = _worksheet_and_rows("invites")
    idx = _find_row_index(rows, "id", invite["id"])
    if idx is None:
        return

    now = datetime.utcnow().isoformat()
    values = [
        invite["id"],
        invite["code"],
        invite.get("label", ""),
        _to_int(invite.get("max_guests"), 1),
        _to_bool(invite.get("allow_plus_one")),
        invite.get("created_at", ""),
        now,
    ]
    ws.update(f"A{idx}:G{idx}", [values])


def create_invite(label: str, code: str, max_guests: int = 1, allow_plus_one: bool = False) -> Dict[str, Any]:
    ws, _ = _worksheet_and_rows("invites")
    now = datetime.utcnow().isoformat()
    invite_id = str(uuid.uuid4())
    values = [invite_id, code, label, int(max_guests), _to_bool(allow_plus_one), now, now]
    ws.append_row(values, value_input_option="USER_ENTERED")
    refresh_cache()
    return {
        "id": invite_id,
        "code": code,
        "label": label,
        "max_guests": int(max_guests),
        "allow_plus_one": _to_bool(allow_plus_one),
        "created_at": now,
        "updated_at": now,
    }


def find_invite_by_label(label: str) -> Optional[Dict[str, Any]]:
    invites = load_invites()
    return next((i for i in invites if (i.get("label") or "").strip() == label.strip()), None)


def upsert_rsvp(row: Dict[str, Any]) -> None:
    ws, rows = _worksheet_and_rows("rsvps")
    idx = _find_row_index(rows, "guest_id", row["guest_id"])
    now = datetime.utcnow().isoformat()
    values = [
        row["guest_id"],
        row.get("attending"),
        row.get("meal_choice"),
        row.get("allergies"),
        row.get("notes"),
        now,
    ]
    if idx:
        ws.update(f"A{idx}:F{idx}", [values])
    else:
        ws.append_row(values, value_input_option="USER_ENTERED")


def add_guest(invite_id: str, full_name: str, is_child: bool = False) -> Dict[str, Any]:
    ws, _ = _worksheet_and_rows("guests")
    guest_id = str(uuid.uuid4())
    values = [guest_id, invite_id, full_name, is_child]
    ws.append_row(values, value_input_option="USER_ENTERED")
    return {"id": guest_id, "invite_id": invite_id, "full_name": full_name, "is_child": is_child}
