#!/usr/bin/env python3
"""Manually trigger vectorization for existing videos."""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.video import Video
from app.models.material import VideoMaterial
from app.services.video_service import VideoService


def main():
    db = SessionLocal()
    try:
        # Find all videos with pending vectorization status
        pending_videos = db.query(Video).filter(
            Video.vectorization_status == "pending"
        ).all()

        if not pending_videos:
            print("No videos with pending vectorization status found.")
            return

        print(f"Found {len(pending_videos)} video(s) with pending vectorization:\n")

        for video in pending_videos:
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"Processing Video ID: {video.id}")
            print(f"Title: {video.title}")
            print(f"Current Status: {video.vectorization_status}")
            print()

            # Trigger vectorization
            print("Triggering vectorization...")
            VideoService._vectorize_transcript(db, video)

            # Refresh to get updated status
            db.refresh(video)

            print(f"New Status: {video.vectorization_status}")
            if video.vectorization_error:
                print(f"Error: {video.vectorization_error}")
            if video.vectorized_at:
                print(f"Vectorized At: {video.vectorized_at}")
            print()

        print("✅ Vectorization triggered for all pending videos.")

    finally:
        db.close()


if __name__ == '__main__':
    main()
