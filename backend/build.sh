#!/bin/bash
set -e

echo "▶ Installing Python dependencies..."
pip install -r requirements.txt

echo "▶ Initialising database tables..."
python -c "
from database import init_db
from database import SessionLocal
from database.models import User
import bcrypt

init_db()

db = SessionLocal()
try:
    if not db.query(User).filter(User.id == 1).first():
        from database.crud import create_user
        pw_hash = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
        create_user(db, email='admin@acrs.com', password_hash=pw_hash, full_name='Admin')
        print('Default user seeded.')
    else:
        print('Default user already exists.')
finally:
    db.close()
"

echo "✅ Build complete."
