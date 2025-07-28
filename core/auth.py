# core/auth.py

import streamlit as st
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# 🔐 Carrega variáveis de ambiente (coloque sua chave e URL no .env)
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Inicializa Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
def login():
    st.title("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.user is not None:
            st.session_state.user = response.user
            st.success("Login realizado com sucesso.")
            st.rerun()
        else:
            st.error("Falha no login. Verifique email/senha.")

def check_auth():
    return "user" in st.session_state and st.session_state.user is not None

def get_current_user():
    return st.session_state.get("user")

def logout():
    st.session_state.user = None
    st.rerun()
