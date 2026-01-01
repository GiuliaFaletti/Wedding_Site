import streamlit as st
from supabase import create_client

@st.cache_resource
def get_supabase():
    """
    Crea (una sola volta) un client Supabase riutilizzabile.

    Perché cache_resource?
    - Streamlit fa rerun spesso: questo evita di ricreare il client a ogni rerun.

    SICUREZZA:
    - Usiamo SERVICE_ROLE_KEY => privilegi elevati.
    - Deve stare SOLO in st.secrets (mai nel repo).
    - Streamlit gira server-side: la key non finisce nel browser dell'ospite.
    """
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)
