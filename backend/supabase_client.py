import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# ---------------------------------------------------
# Load environment variables from project root
# ---------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"

load_dotenv(env_path, override=True)

# ---------------------------------------------------
# Read Supabase credentials
# ---------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("Supabase URL:", SUPABASE_URL)
print("Supabase Key Loaded:", "YES" if SUPABASE_KEY else "NO")

# ---------------------------------------------------
# Validate credentials
# ---------------------------------------------------
if not SUPABASE_URL or not SUPABASE_KEY:
    print("WARNING: Supabase credentials not found. Database functionality will be disabled.")
    supabase = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client created successfully.")
    except Exception as e:
        print(f"ERROR: Could not create Supabase client: {e}")
        supabase = None