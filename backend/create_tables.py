#!/usr/bin/env python3
"""
Create database tables directly using SQLAlchemy.
"""

from app.db.session import engine, Base
from app.models import User, Video, VideoCategory, LearningProgress

def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")

    print("\nCreated tables:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")

if __name__ == "__main__":
    create_tables()
