#!/usr/bin/env python3
"""Reset failed videos to pending status for re-vectorization."""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.video import Video
from app.models.material import VideoMaterial


def main():
    db = SessionLocal()
    try:
        # Find all videos with failed vectorization status
        failed_videos = db.query(Video).filter(
            Video.vectorization_status == "failed"
        ).all()

        if not failed_videos:
            print("No videos with failed vectorization status found.")
            return

        print(f"Found {len(failed_videos)} video(s) with failed vectorization:\n")

        for video in failed_videos:
            print(f"Resetting Video ID: {video.id} - {video.title}")
            video.vectorization_status = "pending"
            video.vectorization_error = None
            video.vectorized_at = None

        db.commit()
        print(f"\n✅ Reset {len(failed_videos)} video(s) to pending status.")

    finally:
        db.close()


if __name__ == '__main__':
    main()
