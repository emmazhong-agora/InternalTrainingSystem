import re
import requests
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class TranscriptChunk:
    """Represents a chunk of transcript with metadata."""

    def __init__(self, text: str, start_time: float, end_time: float, index: int):
        self.text = text
        self.start_time = start_time
        self.end_time = end_time
        self.index = index
        self.metadata = {
            "start_time": start_time,
            "end_time": end_time,
            "index": index,
            "duration": end_time - start_time
        }

    def __repr__(self):
        return f"<TranscriptChunk(index={self.index}, {self.start_time:.2f}s-{self.end_time:.2f}s)>"


class TranscriptService:
    """Service for processing and chunking video transcripts."""

    @staticmethod
    def parse_vtt(vtt_content: str) -> List[Dict]:
        """
        Parse VTT (WebVTT) format transcript.

        Args:
            vtt_content: Raw VTT file content

        Returns:
            List of transcript entries with timestamps
        """
        entries = []

        logger.info(f"Starting VTT parsing, content length: {len(vtt_content)}")

        # Normalize line endings first (convert \r\n to \n)
        vtt_content = vtt_content.replace('\r\n', '\n').replace('\r', '\n')

        # Remove WEBVTT header
        vtt_content = re.sub(r'^WEBVTT[^\n]*\n+', '', vtt_content, flags=re.MULTILINE)

        # Remove NOTE sections
        vtt_content = re.sub(r'NOTE[^\n]*\n+', '', vtt_content, flags=re.MULTILINE)

        # Split into cues (separated by blank lines)
        cues = re.split(r'\n\n+', vtt_content.strip())
        logger.info(f"Found {len(cues)} cues in VTT file")

        for cue in cues:
            if not cue.strip():
                continue

            lines = cue.strip().split('\n')

            if len(lines) < 2:
                continue

            # Parse timestamp line (format: 00:00:00.000 --> 00:00:05.000)
            timestamp_line = lines[0] if '-->' in lines[0] else (lines[1] if len(lines) > 1 and '-->' in lines[1] else None)

            if not timestamp_line:
                continue

            try:
                times = timestamp_line.split('-->')
                start_time = TranscriptService._parse_timestamp(times[0].strip())
                end_time = TranscriptService._parse_timestamp(times[1].strip())

                # Get text (skip timestamp line and cue identifiers)
                # Cue identifiers are typically UUIDs or sequential numbers on the first line
                text_lines = []
                for i, line in enumerate(lines):
                    # Skip timestamp lines
                    if '-->' in line:
                        continue
                    # Skip first line if it looks like a cue identifier (contains UUID pattern or is just digits)
                    if i == 0 and (re.match(r'^[\w-]+-\d+$', line) or line.isdigit()):
                        continue
                    # Skip purely numeric lines
                    if line.isdigit():
                        continue
                    # Keep actual text content
                    text_lines.append(line)

                text = ' '.join(text_lines).strip()

                if text:
                    entry = {
                        'start_time': start_time,
                        'end_time': end_time,
                        'text': text
                    }
                    entries.append(entry)
            except Exception as e:
                logger.warning(f"Error parsing VTT cue: {e}")
                continue

        logger.info(f"Successfully parsed {len(entries)} VTT entries")
        if entries:
            logger.debug(f"First entry: {entries[0]}")
        else:
            logger.warning("No entries were parsed from VTT file!")

        return entries

    @staticmethod
    def _parse_timestamp(timestamp: str) -> float:
        """Convert VTT timestamp to seconds."""
        # Format: HH:MM:SS.mmm or MM:SS.mmm
        parts = timestamp.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = parts
        elif len(parts) == 2:
            hours = '0'
            minutes, seconds = parts
        else:
            return 0.0

        seconds_parts = seconds.split('.')
        secs = float(seconds_parts[0])
        millisecs = float(seconds_parts[1]) / 1000 if len(seconds_parts) > 1 else 0

        total_seconds = int(hours) * 3600 + int(minutes) * 60 + secs + millisecs
        return total_seconds

    @staticmethod
    def chunk_transcript(entries: List[Dict], chunk_size: int = 5, overlap: int = 1) -> List[TranscriptChunk]:
        """
        Chunk transcript entries into larger segments for better context.

        Args:
            entries: List of transcript entries from parse_vtt()
            chunk_size: Number of entries per chunk
            overlap: Number of overlapping entries between chunks

        Returns:
            List of TranscriptChunk objects
        """
        logger.info(f"Chunking {len(entries)} entries with chunk_size={chunk_size}, overlap={overlap}")
        chunks = []
        index = 0

        for i in range(0, len(entries), chunk_size - overlap):
            chunk_entries = entries[i:i + chunk_size]
            if not chunk_entries:
                continue

            # Combine text
            text = ' '.join([entry['text'] for entry in chunk_entries])
            logger.debug(f"Chunk {index}: text length={len(text)}, entries={len(chunk_entries)}")

            # Get time range
            start_time = chunk_entries[0]['start_time']
            end_time = chunk_entries[-1]['end_time']

            chunk = TranscriptChunk(
                text=text,
                start_time=start_time,
                end_time=end_time,
                index=index
            )
            chunks.append(chunk)
            index += 1

        logger.info(f"Created {len(chunks)} transcript chunks")
        if chunks:
            logger.debug(f"First chunk text (first 200 chars): {chunks[0].text[:200]}")
        else:
            logger.warning("No chunks were created!")

        return chunks

    @staticmethod
    def load_transcript_from_url(vtt_url: str) -> str:
        """
        Load VTT transcript from S3 URL using boto3 (avoids SSL issues).

        Args:
            vtt_url: S3 URL of the VTT file

        Returns:
            Raw VTT content as string
        """
        try:
            from app.services.s3_service import s3_service
            from app.core.config import settings

            # Check if this is an S3 URL
            if 's3.' in vtt_url and 'amazonaws.com' in vtt_url:
                logger.info(f"Downloading VTT from S3 using boto3: {vtt_url}")

                # Extract S3 key from URL
                # Format: https://bucket.s3.region.amazonaws.com/folder/file.ext
                parts = vtt_url.split(f"{s3_service.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/")
                if len(parts) < 2:
                    logger.error(f"Invalid S3 URL format: {vtt_url}")
                    raise ValueError(f"Invalid S3 URL format: {vtt_url}")

                s3_key = parts[1].split('?')[0]  # Remove query parameters if present
                logger.info(f"Extracted S3 key: {s3_key}")

                # Download directly from S3 using boto3 (no SSL issues)
                try:
                    response = s3_service.s3_client.get_object(
                        Bucket=s3_service.bucket_name,
                        Key=s3_key
                    )
                    vtt_content = response['Body'].read().decode('utf-8')
                    logger.info(f"Successfully downloaded VTT from S3: {len(vtt_content)} characters")
                    logger.debug(f"First 500 characters: {vtt_content[:500]}")
                    return vtt_content
                except Exception as boto_error:
                    logger.error(f"Boto3 download failed: {boto_error}")
                    raise
            else:
                # For non-S3 URLs, use requests (with SSL verification disabled as fallback)
                logger.info(f"Downloading VTT from external URL: {vtt_url[:100]}...")
                response = requests.get(vtt_url, timeout=30, verify=False)
                logger.info(f"Response status code: {response.status_code}")
                response.raise_for_status()
                logger.info(f"Transcript content length: {len(response.text)} characters")
                return response.text

        except Exception as e:
            logger.error(f"Error loading transcript from {vtt_url}: {e}")
            raise

    @staticmethod
    def process_video_transcript(vtt_url: str, chunk_size: int = 5) -> List[TranscriptChunk]:
        """
        Complete pipeline: Load, parse, and chunk a video transcript.

        Args:
            vtt_url: S3 URL of the VTT file
            chunk_size: Number of entries per chunk

        Returns:
            List of transcript chunks ready for embedding
        """
        logger.info(f"Processing transcript from {vtt_url}")

        # Load transcript
        vtt_content = TranscriptService.load_transcript_from_url(vtt_url)

        # Parse VTT
        entries = TranscriptService.parse_vtt(vtt_content)
        logger.info(f"Parsed {len(entries)} transcript entries")

        # Chunk transcript
        chunks = TranscriptService.chunk_transcript(entries, chunk_size=chunk_size)
        logger.info(f"Created {len(chunks)} transcript chunks")

        return chunks


transcript_service = TranscriptService()
