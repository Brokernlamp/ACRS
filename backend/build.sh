#!/bin/bash
set -e

echo "▶ Installing Python dependencies..."
pip install -r requirements.txt

echo "▶ Pre-downloading sentence-transformers model (all-MiniLM-L6-v2)..."
python -c "
from sentence_transformers import SentenceTransformer
print('Downloading all-MiniLM-L6-v2...')
SentenceTransformer('all-MiniLM-L6-v2')
print('Model cached successfully.')
"

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
