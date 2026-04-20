#!/usr/bin/env python3
from database import init_db, SessionLocal
from database.models import User
from config import config

print("Setting up ACRS...")

config.init_app()
init_db()

db = SessionLocal()
try:
    existing = db.query(User).filter(User.id == 1).first()
    if not existing:
        user = User(
            id=1,
            email="default@acrs.com",
            password_hash="not_used",
            full_name="Default User",
            agency_name="ACRS",
            is_active=True
        )
        db.add(user)
        db.commit()
        print("Default user created")
    else:
        print("Default user exists")
    
    print("\nREADY! Run: python app.py")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
