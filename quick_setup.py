#!/usr/bin/env python3
"""Quick setup - Initialize DB and create admin user"""

from database import init_db, SessionLocal
from database.crud import create_user, get_user_by_email
from config import config
import bcrypt

print("🚀 Initializing ACRS...")

# Initialize directories and database
config.init_app()
init_db()
print("✅ Database initialized")

# Create admin user
db = SessionLocal()
try:
    existing = get_user_by_email(db, "admin@acrs.com")
    if existing:
        print("⚠️  Admin user already exists")
    else:
        # Hash password directly with bcrypt
        password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = create_user(
            db, 
            email="admin@acrs.com",
            password_hash=password_hash,
            full_name="Admin User",
            agency_name="ACRS Agency"
        )
        print("✅ Admin user created")
    
    print("\n" + "="*50)
    print("LOGIN CREDENTIALS:")
    print("="*50)
    print("Email:    admin@acrs.com")
    print("Password: admin123")
    print("="*50)
    print("\nRun: python app.py")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
