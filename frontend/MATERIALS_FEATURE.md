# Training Materials Feature - Frontend

## Overview
The Training Materials feature allows users to view and download supplementary files (slides, PDFs, documents, etc.) attached to training videos. Admins can upload, manage, and delete materials for any video.

## Features Implemented

### ✅ For All Users
- View materials attached to videos in the video player page
- Download materials with a single click
- See material details (title, description, file size, type)
- Beautiful file type icons (PDF, PowerPoint, Word, Excel, etc.)
- Clean, modern UI with hover effects

### ✅ For Admin Users
- Upload new materials to existing videos
- Add optional title and description for materials
- View all materials with management controls
- Delete materials
- Real-time updates after upload/delete

## Files Created/Modified

### New Files
```
frontend/src/
├── components/MaterialsManager.tsx    (NEW) - Admin materials management UI
└── MATERIALS_FEATURE.md               (NEW) - This documentation
```

### Modified Files
```
frontend/src/
├── types/index.ts                     - Added Material, MaterialUploadData, MaterialListResponse types
├── services/api.ts                    - Added materialsAPI with CRUD functions
└── pages/VideoPlayerPage.tsx          - Integrated materials display and management
```

## TypeScript Types

### Material Interface
```typescript
export interface Material {
  id: number;
  video_id: number;
  file_url: string;
  original_filename: string;
  file_type?: string;
  file_size?: number;
  title?: string;
  description?: string;
  uploaded_by?: number;
  created_at: string;
  updated_at?: string;
}
```

### Video Interface (Updated)
```typescript
export interface Video {
  // ... existing fields ...
  materials?: Material[];  // NEW: Array of materials
}
```

## API Functions

### materialsAPI Object
```typescript
export const materialsAPI = {
  // List all materials for a video
  list: async (videoId: number): Promise<MaterialListResponse>

  // Get single material by ID
  get: async (materialId: number): Promise<Material>

  // Upload new material
  upload: async (videoId: number, data: MaterialUploadData): Promise<Material>

  // Update material metadata (title, description)
  update: async (materialId: number, data: { title?: string; description?: string }): Promise<Material>

  // Delete material
  delete: async (materialId: number): Promise<void>
}
```

## Components

### MaterialsManager Component

**Location**: `src/components/MaterialsManager.tsx`

**Props**:
```typescript
interface MaterialsManagerProps {
  videoId: number;              // ID of the video
  materials: Material[];        // Current materials list
  onMaterialAdded: () => void;  // Callback after upload
  onMaterialDeleted: () => void; // Callback after delete
}
```

**Features**:
- Toggle upload form with "Add Material" button
- File selection with validation
- Optional title and description fields
- Real-time file size display
- Upload progress indication
- Materials list with delete buttons
- Beautiful file type icons
- Responsive design

**Usage**:
```tsx
<MaterialsManager
  videoId={video.id}
  materials={video.materials || []}
  onMaterialAdded={() => loadVideo()}
  onMaterialDeleted={() => loadVideo()}
/>
```

### VideoPlayerPage Updates

**Admin View**:
- Shows `MaterialsManager` component with full CRUD controls
- Can upload new materials
- Can delete existing materials
- Real-time updates after changes

**Regular User View**:
- Shows read-only materials list
- Download buttons for each material
- Clean, card-based layout
- File information display

## User Interface

### Materials Display (Regular Users)

```
┌─────────────────────────────────────────────────────┐
│ 📚 Training Materials                               │
│                                                     │
│ ┌─────────────────────────────────────────────┐   │
│ │ 📄 Training Slides.pdf                      │ ⬇ │
│ │    PowerPoint slides for this session       │   │
│ │    1.2 MB • PDF                             │   │
│ └─────────────────────────────────────────────┘   │
│                                                     │
│ ┌─────────────────────────────────────────────┐   │
│ │ 📝 Session Notes.docx                       │ ⬇ │
│ │    512 KB • DOCX                            │   │
│ └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Materials Manager (Admin View)

```
┌─────────────────────────────────────────────────────┐
│ 📚 Training Materials           [+ Add Material]   │
│                                                     │
│ ┌─ Upload New Material ───────────────────────┐   │
│ │ File *:        [Choose File]                 │   │
│ │ Title:         [Custom display name]         │   │
│ │ Description:   [Brief description...]        │   │
│ │                [Upload Material]             │   │
│ └──────────────────────────────────────────────┘   │
│                                                     │
│ ┌─────────────────────────────────────────────┐   │
│ │ 📄 Training Slides.pdf               [Download] │
│ │    PowerPoint slides                  [Delete]  │
│ │    1.2 MB • Uploaded Nov 12, 2025            │   │
│ └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## File Type Icons

The system automatically detects file types and displays appropriate icons:

| File Type | Icon | Detected From |
|-----------|------|---------------|
| PDF | 📄 | .pdf, application/pdf |
| Word | 📝 | .doc, .docx, word |
| PowerPoint | 📊 | .ppt, .pptx, presentation |
| Excel | 📈 | .xls, .xlsx, spreadsheet |
| ZIP | 📦 | .zip, .rar, archive |
| Image | 🖼️ | .png, .jpg, .jpeg, image |
| Video | 🎥 | .mp4, video |
| Audio | 🎵 | .mp3, audio |
| Text | 📃 | .txt, text |
| Other | 📎 | default |

## Helper Functions

### getFileIcon(fileTypeOrName: string)
Returns appropriate emoji icon based on file type or filename.

### formatFileSize(bytes?: number)
Formats file size in human-readable format (B, KB, MB, GB).

### getFileExtension(filename: string)
Extracts and returns file extension in uppercase.

## Workflow

### Admin Uploading Material

1. Admin views video player page
2. Sees `MaterialsManager` component
3. Clicks "Add Material" button
4. Upload form appears
5. Selects file, adds optional title/description
6. Clicks "Upload Material"
7. File uploads to S3, record saved to database
8. Materials list refreshes automatically
9. Success! Material is now visible to all users

### User Downloading Material

1. User views video player page
2. Scrolls to "Training Materials" section
3. Sees list of available materials
4. Clicks "Download" button
5. File downloads from S3
6. User can now access the material offline

## Error Handling

### Upload Errors
- Missing file: "Please select a file"
- Upload failure: "Failed to upload material" (with server error details)
- Network errors: Displayed in red alert box

### Delete Errors
- Confirmation dialog before deletion
- Error alert if deletion fails
- Automatic refresh after successful deletion

## Responsive Design

The materials UI is fully responsive:

### Desktop (1024px+)
- Materials displayed in full-width cards
- Side-by-side buttons (Download + Delete)
- Detailed information visible

### Tablet (768px - 1023px)
- Cards adjust to available width
- Buttons remain horizontal
- Icons and text properly sized

### Mobile (< 768px)
- Single column layout
- Buttons stack vertically
- Touch-friendly targets
- Responsive padding and spacing

## Security Considerations

### Authentication
- All material API calls require authentication
- Tokens automatically added by axios interceptor
- 401 errors trigger automatic logout

### Authorization
- Upload/Delete restricted to admin users
- Regular users can only view and download
- Frontend checks `user.is_admin` flag
- Backend enforces permissions

### File Access
- Materials stored in S3 with UUID filenames
- Public read access via bucket policy
- Original filenames preserved in metadata
- Download attributes prevent XSS

## Testing

### Test Upload Flow
1. Login as admin
2. Navigate to any video
3. Click "Add Material"
4. Upload test file
5. Verify file appears in list
6. Download and verify file integrity

### Test Download Flow
1. Login as regular user
2. Navigate to video with materials
3. Click download on each material
4. Verify files download correctly

### Test Delete Flow
1. Login as admin
2. Click delete on a material
3. Confirm deletion
4. Verify material removed from list
5. Check S3 bucket (file should be deleted)

## Browser Compatibility

✅ Chrome/Edge (Chromium) 90+
✅ Firefox 88+
✅ Safari 14+
✅ Mobile Safari (iOS 14+)
✅ Chrome Mobile (Android 10+)

## Performance Considerations

### Optimizations
- Materials loaded with video data (single request)
- HMR (Hot Module Replacement) for dev updates
- Lazy loading of MaterialsManager component
- Efficient re-renders with React hooks

### File Size Limits
- Frontend accepts any file size
- Backend enforces S3 upload limits
- Progress indication for large uploads
- Error handling for failed uploads

## Future Enhancements

Possible improvements for future versions:

- [ ] Drag-and-drop file upload
- [ ] Multiple file upload at once
- [ ] Material preview (PDF, images)
- [ ] Download all materials as ZIP
- [ ] Material categories/tags
- [ ] Search/filter materials
- [ ] Material download tracking
- [ ] Thumbnail generation
- [ ] Version history for materials
- [ ] Material comments/feedback

## Troubleshooting

### Materials not showing
**Problem**: Materials uploaded but not visible
**Solution**:
- Check if video was reloaded after upload
- Verify backend returns materials in video response
- Check browser console for errors
- Refresh page

### Upload fails silently
**Problem**: Upload button doesn't work
**Solution**:
- Check if user is admin
- Verify file is selected
- Check network tab for API errors
- Check backend logs

### Download returns 403
**Problem**: Download button shows 403 Forbidden
**Solution**:
- Apply S3 bucket policy for public read
- Update bucket policy to include `materials/*`
- Verify bucket settings in AWS console

### TypeScript errors
**Problem**: Type errors in IDE
**Solution**:
- Ensure types are imported correctly
- Run `npm run build` to check for errors
- Restart TypeScript server in IDE

## API Endpoints Used

- `GET /api/v1/videos/{id}` - Includes materials in response
- `GET /api/v1/videos/{video_id}/materials` - List materials
- `POST /api/v1/videos/{video_id}/materials` - Upload material
- `DELETE /api/v1/materials/{material_id}` - Delete material

## Summary

The Training Materials feature is now fully integrated into the frontend with:
- ✅ Beautiful, responsive UI
- ✅ Admin management controls
- ✅ User-friendly download experience
- ✅ Full TypeScript type safety
- ✅ Proper error handling
- ✅ Real-time updates
- ✅ File type detection with icons
- ✅ Clean, modern design

Users can now easily access training materials alongside videos, and admins have full control to manage these resources.
