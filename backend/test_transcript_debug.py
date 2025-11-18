#!/usr/bin/env python3
"""Test transcript processing with debugging."""

import sys
sys.path.insert(0, '/Users/zhonghuang/Documents/InternalTrainingSystem-Fresh/backend')

from app.services.transcript_service import TranscriptService

# Test with the actual VTT URL from video 5
vtt_url = "https://emmatestbucket.s3.ap-southeast-1.amazonaws.com/transcripts/eab6810c-f3f1-450a-96bd-b568acd41009.vtt"

print("=" * 80)
print("Testing Transcript Processing with Debug Output")
print("=" * 80)

# Step 1: Load transcript
print("\n1. Loading transcript from URL...")
vtt_content = TranscriptService.load_transcript_from_url(vtt_url)
print(f"   Downloaded {len(vtt_content)} characters")

# Step 2: Parse VTT (this will show all our debug output)
print("\n2. Parsing VTT content...")
entries = TranscriptService.parse_vtt(vtt_content)

print("\n" + "=" * 80)
print(f"RESULT: Parsed {len(entries)} entries")
if entries:
    print(f"First entry: {entries[0]}")
    print(f"Last entry: {entries[-1]}")
print("=" * 80)
