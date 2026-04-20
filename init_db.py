#!/usr/bin/env python3
"""
Initialize database tables
Run this once to create all tables in the database
"""

from database import init_db
from config import config

if __name__ == "__main__":
    print("Initializing database...")
    print(f"Database URL: {config.DATABASE_URL}")
    
    config.init_app()  # Create directories
    init_db()  # Create tables
    
    print("✅ Database initialized successfully!")
    print("Tables created:")
    print("  - users")
    print("  - clients")
    print("  - campaigns")
    print("  - campaign_data")
    print("  - api_connections")
    print("  - alerts")
    print("  - reports")
