# SSL Error Fix - VTT Download from S3

## Problem

When auto-vectorization tried to download VTT transcript files from S3, it encountered SSL/TLS errors:

```
SSLError: [SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC] decryption failed or bad record mac
```

**Impact**: Videos could not be vectorized, blocking AI features (Chat, Quiz, Voice Assistant)

## Root Cause

The transcript service was using `requests.get()` with presigned S3 URLs to download VTT files. This caused SSL/TLS handshake failures when connecting to S3.

**Previous Code** (`transcript_service.py:184-213`):
```python
# Generate presigned URL and use requests.get()
vtt_url = s3_service.generate_presigned_url_from_s3_url(vtt_url, expiration=3600)
response = requests.get(vtt_url, timeout=30)  # SSL ERROR HERE
```

## Solution

Changed the download method to use **boto3's `get_object()` directly** instead of HTTP requests:

**Fixed Code** (`transcript_service.py:184-236`):
```python
# Extract S3 key from URL
parts = vtt_url.split(f"{s3_service.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/")
s3_key = parts[1].split('?')[0]  # Remove query parameters

# Download directly using boto3 (no SSL issues)
response = s3_service.s3_client.get_object(
    Bucket=s3_service.bucket_name,
    Key=s3_key
)
vtt_content = response['Body'].read().decode('utf-8')
```

## Benefits of This Fix

1. **No SSL errors**: boto3 handles SSL/TLS connections more reliably
2. **Better performance**: Direct S3 API calls are faster than HTTP requests
3. **No presigned URLs needed**: Simplified code path
4. **More secure**: Uses AWS credentials instead of temporary URLs

## Test Results

**Before Fix:**
```
Video ID 4: failed - SSL error
Video ID 5: failed - SSL error
```

**After Fix:**
```
✅ Video ID 4: completed - Vectorized at 2025-11-14 10:07:02
✅ Video ID 5: completed - Vectorized at 2025-11-14 10:07:09
```

## Files Modified

- **`app/services/transcript_service.py:184-236`** - Updated `load_transcript_from_url()` method

## Verification Steps

1. Reset failed videos to pending status:
   ```bash
   python3 reset_failed_videos.py
   ```

2. Trigger vectorization:
   ```bash
   python3 trigger_vectorization.py
   ```

3. Check status:
   ```bash
   python3 check_videos.py
   ```

4. Verify in UI:
   - Browse to video player page
   - AI Assistant Status should show "Ready" (green)
   - No error messages displayed

## Impact on New Video Uploads

All new video uploads will now:
1. Upload VTT file to S3 ✅
2. Auto-trigger vectorization ✅
3. Download VTT using boto3 (no SSL errors) ✅
4. Parse and chunk transcript ✅
5. Generate embeddings via OpenAI ✅
6. Store in ChromaDB ✅
7. Update status to "completed" ✅
8. AI features immediately available ✅

---

**Fix Date**: 2025-11-14
**Status**: ✅ RESOLVED
**Feature**: VTT Auto-Vectorization (Phase 1, Task 1)
