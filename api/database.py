# /api/database.py
from supabase import create_client, Client
from config import Config

# Esta é a sua "conexão" com o banco, que será importada pelos controllers
supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)