# /config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "uma-chave-secreta-padrao-muito-segura")

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Erro: SUPABASE_URL e SUPABASE_KEY não encontradas no .env.")