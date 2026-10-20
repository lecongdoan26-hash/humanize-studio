import sys
import os

# Fix Windows console encoding for Unicode & Emoji
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import uvicorn
from core.database import init_db

if __name__ == "__main__":
    print("=" * 60)
    print("      🚀 KHOI DONG HE THONG KLARO AI (AGENT OS)")
    print("=" * 60)
    print("1. Khoi tao co so du lieu SQLite...")
    init_db()
    print("2. May chu Web API san sang tai: http://127.0.0.1:8000")
    print("3. Bam Ctrl + C de dung may chu.")
    print("=" * 60)
    
    # Start web server
    uvicorn.run("web.app:app", host="127.0.0.1", port=8000, reload=False)
