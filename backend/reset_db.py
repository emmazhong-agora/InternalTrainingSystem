#!/usr/bin/env python3
"""
Reset database - drop all tables and recreate schema.
"""

from sqlalchemy import text
from app.db.session import engine, Base
from app.models import User, Video, VideoCategory, LearningProgress

def reset_database():
    """Drop schema and recreate all tables."""
    print("⚠️  WARNING: This will DROP all existing data!")

    with engine.connect() as conn:
        print("Dropping public schema...")
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.commit()

        print("Creating public schema...")
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO training"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        conn.commit()

    print("✅ Schema reset complete")

    print("\nCreating new tables with correct schema...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")

    print("\nCreated tables:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")

if __name__ == "__main__":
    reset_database()
