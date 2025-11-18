#!/usr/bin/env python3
"""Check videos and their vectorization status in the database."""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.video import Video
from app.models.material import VideoMaterial  # Import to resolve relationship


def main():
    db = SessionLocal()
    try:
        videos = db.query(Video).all()
        if videos:
            print(f'Found {len(videos)} video(s) in database:\n')
            for v in videos:
                print(f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
                print(f'ID: {v.id}')
                print(f'Title: {v.title}')
                print(f'Description: {v.description or "N/A"}')
                print(f'Vectorization Status: {v.vectorization_status}')
                if v.vectorization_error:
                    print(f'Error: {v.vectorization_error}')
                if v.vectorized_at:
                    print(f'Vectorized At: {v.vectorized_at}')
                print(f'Created At: {v.created_at}')
                print()
        else:
            print('No videos found in database.')
            print('\nTo test the VTT auto-vectorization feature:')
            print('1. Upload a video with VTT file through the frontend')
            print('2. Watch the vectorization_status change from pending → processing → completed')
            print('3. Verify AI features (Chat, Quiz, Voice) work with the vectorized content')
    finally:
        db.close()


if __name__ == '__main__':
    main()
