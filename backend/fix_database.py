#!/usr/bin/env python3
"""
Fix database schema - drop and recreate all tables.
"""

from app.db.session import engine, Base
from app.models import User, Video, VideoCategory, LearningProgress

def fix_database():
    """Drop all tables and recreate them."""
    print("⚠️  WARNING: This will DROP all existing tables and data!")
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped")

    print("\nCreating new tables with correct schema...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")

    print("\nCreated tables:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")
        for column in table.columns:
            print(f"    • {column.name}: {column.type}")

if __name__ == "__main__":
    fix_database()
