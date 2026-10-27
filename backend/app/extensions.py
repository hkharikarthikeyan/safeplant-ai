import os
from supabase import create_client, Client
from flask_cors import CORS

cors = CORS()
_supabase_client: Client = None


def get_supabase() -> Client:
    global _supabase_client
    if _supabase_client is None:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_ANON_KEY", "")
        _supabase_client = create_client(url, key)
    return _supabase_client
