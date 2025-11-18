#!/usr/bin/env python3
"""
Database initialization script for Internal Training System.
Run this after setting up your .env file to create the database schema.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db.session import Base, engine
from app.models import User, Video, VideoCategory, LearningProgress
from app.core.config import settings

def init_db():
    """Initialize database tables."""
    print("🔧 Initializing database...")
    print(f"📍 Database URL: {settings.DATABASE_URL}")

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        print("\nCreated tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")

        print("\n✅ Database initialization complete!")
        print("\nNext steps:")
        print("1. Run: cd backend && alembic revision --autogenerate -m 'Initial migration'")
        print("2. Run: cd backend && alembic upgrade head")
        print("3. Start backend: uvicorn app.main:app --reload")
        print("4. Create admin user via API or frontend")

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        print("\nPlease check:")
        print("1. PostgreSQL is running")
        print("2. DATABASE_URL in backend/.env is correct")
        print("3. Database exists: psql -U postgres -c 'CREATE DATABASE training_system;'")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("Internal Training System - Database Initialization")
    print("=" * 60)
    init_db()
