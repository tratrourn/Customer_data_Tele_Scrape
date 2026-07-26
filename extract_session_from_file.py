#!/usr/bin/env python3
"""
Extract session string from existing geo_scraper.session file.
This converts the SQLite session to a portable StringSession format.
"""

import asyncio
import nest_asyncio
import sys
from pathlib import Path
from telethon import TelegramClient
from telethon.sessions import StringSession

# Apply nest_asyncio for Jupyter compatibility
nest_asyncio.apply()

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
SESSION_DIR = BASE_DIR / "tg_sessions"
SESSION_PATH = SESSION_DIR / "geo_scraper"

# Telegram API credentials (same as in scraper_backend.py)
API_ID = 22365302
API_HASH = "df22eea81948788953b28b8112ab926a"

async def extract_session_string():
    """Load SQLiteSession and convert to StringSession."""
    
    session_path = str(SESSION_PATH)
    
    try:
        print(f"📂 Loading existing session from: {session_path}")
        
        # Create a temporary client and copy session to StringSession
        string_session_temp = StringSession()
        
        # Load existing SQLite session
        client = TelegramClient(session_path, API_ID, API_HASH)
        async with client:
            # Check authorization
            is_authorized = await client.is_user_authorized()
            if not is_authorized:
                print("❌ Session is not authorized.")
                return None
            
            print("✅ SQLite session loaded and authorized")
            
            # Get the auth key from current session
            auth_key = client.session.auth_key
            if not auth_key:
                print("❌ No authentication key found.")
                return None
            
            # Manually build StringSession format
            # StringSession encodes: (dc_id, user_id, is_bot, auth_key) as pickle-like binary
            import struct
            import pickle
            import base64
            
            dc_id = getattr(client.session, 'dc_id', 2)
            user_id = getattr(client.session, 'user_id', None)
            is_bot = getattr(client.session, 'is_bot', False)
            
            # Build the session data as StringSession expects
            # Format: pack(dc_id:4, user_id:4, is_bot:1, auth_key:256)
            try:
                auth_key_bytes = auth_key.key if hasattr(auth_key, 'key') else bytes(auth_key)
            except:
                auth_key_bytes = bytes(auth_key)
            
            # Create binary session data
            session_data = struct.pack(
                '!IBB',  # Big-endian: int(4), int(4), bool(1)
                dc_id or 2,
                user_id or 0,
                1 if is_bot else 0
            ) + auth_key_bytes
            
            # Encode to base64
            session_str = base64.b64encode(session_data).decode('ascii')
            
            print(f"✅ Session string extracted successfully!")
            print(f"\n{'='*70}")
            print(f"📋 TELEGRAM_SESSION_STRING:\n")
            print(session_str)
            print(f"{'='*70}")
            print(f"\n📋 Length: {len(session_str)} characters")
            
            # Save to file
            output_file = BASE_DIR / "session_string_extracted.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(session_str)
            print(f"\n💾 Saved to: {output_file}")
            
            return session_str
        
    except Exception as e:
        print(f"❌ Error extracting session: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🔐 Telegram Session String Extractor")
    print("=" * 70)
    session_string = asyncio.run(extract_session_string())
    if session_string:
        print(f"\n✨ Ready to use in:")
        print(f"   1. .streamlit/secrets.toml (local development)")
        print(f"   2. Streamlit Cloud → App menu → Manage secrets (production)")
    else:
        print("\n❌ Failed to extract session string")
        sys.exit(1)
