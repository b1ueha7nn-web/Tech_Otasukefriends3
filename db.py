#create/db-login 追加

import os
#categoriesを文字列にするためにjason必要
import json
from dotenv import load_dotenv
#.envを読み込ませる
load_dotenv()
from supabase import create_client, Client


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
