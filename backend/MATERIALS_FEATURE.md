# Training Materials Feature

## Overview
The Training Materials feature allows admins to attach supplementary files (slides, PDFs, documents, etc.) to training videos. Users can view and download these materials when watching videos.

## Database Schema

### New Table: `video_materials`

```sql
CREATE TABLE video_materials (
    id SERIAL PRIMARY KEY,
    video_id INTEGER REFERENCES videos(id) ON DELETE CASCADE,
    file_url VARCHAR NOT NULL,              -- S3 URL
    original_filename VARCHAR NOT NULL,     -- Original file name
    file_type VARCHAR,                       -- MIME type
    file_size BIGINT,                        -- File size in bytes
    title VARCHAR,                           -- Optional custom title
    description VARCHAR,                     -- Optional description
    uploaded_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

### Relationships
- **Video → Materials**: One-to-Many (cascade delete)
- **User → Materials**: Many-to-One (uploaded_by)

## API Endpoints

### 1. Upload Material for a Video
**POST** `/api/v1/videos/{video_id}/materials`

**Auth**: Admin only

**Form Data**:
- `material_file`: File (required)
- `title`: String (optional) - Custom display title
- `description`: String (optional) - Description of the material

**Response**: 201 Created
```json
{
  "id": 1,
  "video_id": 4,
  "file_url": "https://emmatestbucket.s3.ap-southeast-1.amazonaws.com/materials/uuid.pdf",
  "original_filename": "slides.pdf",
  "file_type": "application/pdf",
  "file_size": 1024000,
  "title": "Training Slides",
  "description": "PowerPoint slides for this session",
  "uploaded_by": 1,
  "created_at": "2025-11-12T10:00:00Z",
  "updated_at": null
}
```

**Example with curl**:
```bash
curl -X POST "http://localhost:8000/api/v1/videos/4/materials" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "material_file=@slides.pdf" \
  -F "title=Training Slides" \
  -F "description=PowerPoint slides for this session"
```

### 2. List Materials for a Video
**GET** `/api/v1/videos/{video_id}/materials`

**Auth**: Required (any authenticated user)

**Response**: 200 OK
```json
{
  "total": 2,
  "materials": [
    {
      "id": 1,
      "video_id": 4,
      "file_url": "https://emmatestbucket.s3.ap-southeast-1.amazonaws.com/materials/uuid.pdf",
      "original_filename": "slides.pdf",
      "file_type": "application/pdf",
      "file_size": 1024000,
      "title": "Training Slides",
      "description": "PowerPoint slides",
      "uploaded_by": 1,
      "created_at": "2025-11-12T10:00:00Z"
    },
    {
      "id": 2,
      "video_id": 4,
      "file_url": "https://emmatestbucket.s3.ap-southeast-1.amazonaws.com/materials/uuid.docx",
      "original_filename": "notes.docx",
      "file_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "file_size": 512000,
      "title": "Session Notes",
      "description": null,
      "uploaded_by": 1,
      "created_at": "2025-11-12T10:05:00Z"
    }
  ]
}
```

### 3. Get Single Material
**GET** `/api/v1/materials/{material_id}`

**Auth**: Required (any authenticated user)

**Response**: 200 OK (same as individual material object above)

### 4. Update Material Metadata
**PUT** `/api/v1/materials/{material_id}`

**Auth**: Admin only

**Body**:
```json
{
  "title": "Updated Title",
  "description": "Updated description"
}
```

**Response**: 200 OK (updated material object)

### 5. Delete Material
**DELETE** `/api/v1/materials/{material_id}`

**Auth**: Admin only

**Response**: 204 No Content

**Note**: This deletes both the database record and the S3 file.

## Video API Updates

### Get Video Details
**GET** `/api/v1/videos/{video_id}`

Now includes `materials` array:
```json
{
  "id": 4,
  "title": "convoai",
  "description": "Training video",
  "video_url": "...",
  "transcript_url": "...",
  "materials": [
    {
      "id": 1,
      "video_id": 4,
      "file_url": "https://emmatestbucket.s3.ap-southeast-1.amazonaws.com/materials/uuid.pdf",
      "original_filename": "slides.pdf",
      "file_type": "application/pdf",
      "file_size": 1024000,
      "title": "Training Slides",
      "uploaded_by": 1,
      "created_at": "2025-11-12T10:00:00Z"
    }
  ],
  "created_at": "2025-11-12T09:00:00Z"
}
```

## S3 Storage Structure

Materials are stored in a dedicated S3 folder:
```
emmatestbucket/
├── videos/          # Video MP4 files
├── transcripts/     # VTT subtitle files
└── materials/       # Training materials (NEW)
    ├── uuid-1.pdf
    ├── uuid-2.pptx
    ├── uuid-3.docx
    └── uuid-4.zip
```

Each file is renamed with a UUID to prevent conflicts and ensure uniqueness.

## File Type Support

The API accepts any file type. Common types include:
- **PDFs**: `application/pdf`
- **PowerPoint**: `application/vnd.ms-powerpoint`, `application/vnd.openxmlformats-officedocument.presentationml.presentation`
- **Word**: `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Excel**: `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Archives**: `application/zip`, `application/x-rar-compressed`
- **Images**: `image/jpeg`, `image/png`

## Backend Implementation

### Models
- `app/models/material.py` - VideoMaterial SQLAlchemy model

### Schemas
- `app/schemas/material.py` - Pydantic schemas for validation

### Services
- `app/services/material_service.py` - Business logic for CRUD operations

### Routes
- `app/api/routes/materials.py` - API endpoints

### Features
- ✅ Upload materials to S3
- ✅ Store metadata in PostgreSQL
- ✅ Associate materials with videos
- ✅ List materials per video
- ✅ Update material metadata
- ✅ Delete materials (with S3 cleanup)
- ✅ Cascade delete (materials deleted when video is deleted)
- ✅ Admin-only upload/update/delete
- ✅ Public read access for authenticated users

## Frontend Integration (To Be Implemented)

### Upload Page
Add a section to upload materials when creating a new video or editing an existing one.

### Video Player Page
Display a list of materials below the video player with:
- File name
- File type icon
- Download button
- Optional description

### Example UI:
```
📹 Video Player
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 Training Materials:
  📊 Training Slides.pdf (1.2 MB)
     PowerPoint slides for this session
     [Download]

  📝 Session Notes.docx (512 KB)
     [Download]

  📦 Additional Resources.zip (5.4 MB)
     Code examples and practice files
     [Download]
```

## Testing

### 1. Test Material Upload
```bash
# Create a test file
echo "This is a test material" > test-material.txt

# Get admin token (login first)
TOKEN="your_jwt_token_here"

# Upload material for video ID 4
curl -X POST "http://localhost:8000/api/v1/videos/4/materials" \
  -H "Authorization: Bearer $TOKEN" \
  -F "material_file=@test-material.txt" \
  -F "title=Test Material" \
  -F "description=This is a test file"
```

### 2. Test List Materials
```bash
curl "http://localhost:8000/api/v1/videos/4/materials" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Check Backend Logs
```bash
tail -f backend.log
```

Look for:
```
=== Material Upload Request ===
User: admin (ID: 1)
Video ID: 4
Material file: test-material.txt
Video found, uploading material...
Starting material upload for video ID: 4
...
Material upload completed successfully - Material ID: 1
```

## Security Considerations

1. **Authentication**: All endpoints require authentication
2. **Authorization**: Upload/Update/Delete are admin-only
3. **File Storage**: Files stored in S3 with UUID names (prevents guessing)
4. **Public Access**: Materials are publicly readable once uploaded (same as videos)
5. **Cascade Delete**: Materials are automatically deleted when parent video is deleted
6. **S3 Cleanup**: S3 files are deleted when material records are deleted

## Future Enhancements

- [ ] File size limits configuration
- [ ] File type restrictions
- [ ] Thumbnail generation for images/PDFs
- [ ] Download tracking/analytics
- [ ] Bulk upload of materials
- [ ] Material versioning
- [ ] Preview functionality for PDFs/images
- [ ] Search within materials

## Troubleshooting

### Materials not appearing in video response
- Check if materials are properly associated with the video
- Verify the VideoResponse schema includes materials field
- Check database relationships are properly configured

### Upload fails with 500 error
- Check backend logs: `tail -f backend.log`
- Verify S3 credentials are correct
- Ensure bucket policy allows uploads
- Check disk space on server

### Materials not publicly accessible (403 error)
- Apply the S3 bucket policy for public read access
- Verify bucket policy includes `materials/*` path
- Check if "Block Public Access" settings are correct

## API Documentation

Full interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Look for the "Materials" section in the API documentation.
