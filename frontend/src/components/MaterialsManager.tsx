import React, { useState } from 'react';
import { materialsAPI } from '../services/api';
import type { Material } from '../types';

interface MaterialsManagerProps {
  videoId: number;
  materials: Material[];
  onMaterialAdded: () => void;
  onMaterialDeleted: () => void;
}

const MaterialsManager: React.FC<MaterialsManagerProps> = ({
  videoId,
  materials,
  onMaterialAdded,
  onMaterialDeleted,
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [uploadData, setUploadData] = useState({
    title: '',
    description: '',
    file: null as File | null,
  });
  const [error, setError] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setUploadData({ ...uploadData, file: e.target.files[0] });
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadData.file) {
      setError('Please select a file');
      return;
    }

    setIsUploading(true);
    setError('');

    try {
      await materialsAPI.upload(videoId, {
        title: uploadData.title || undefined,
        description: uploadData.description || undefined,
        material_file: uploadData.file,
      });

      // Reset form
      setUploadData({ title: '', description: '', file: null });
      setShowUploadForm(false);
      onMaterialAdded();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload material');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (materialId: number, filename: string) => {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
      return;
    }

    try {
      await materialsAPI.delete(materialId);
      onMaterialDeleted();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete material');
    }
  };

  const getFileIcon = (fileTypeOrName: string): string => {
    const type = fileTypeOrName.toLowerCase();
    if (type.includes('pdf')) return '📄';
    if (type.includes('word') || type.includes('doc')) return '📝';
    if (type.includes('powerpoint') || type.includes('presentation') || type.includes('ppt')) return '📊';
    if (type.includes('excel') || type.includes('spreadsheet') || type.includes('xls')) return '📈';
    if (type.includes('zip') || type.includes('rar') || type.includes('archive')) return '📦';
    if (type.includes('image') || type.includes('png') || type.includes('jpg') || type.includes('jpeg')) return '🖼️';
    return '📎';
  };

  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return 'Unknown size';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold">📚 Training Materials</h2>
        <button
          onClick={() => setShowUploadForm(!showUploadForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm font-medium"
        >
          {showUploadForm ? 'Cancel' : '+ Add Material'}
        </button>
      </div>

      {/* Upload Form */}
      {showUploadForm && (
        <form onSubmit={handleUpload} className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-semibold mb-3">Upload New Material</h3>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                File *
              </label>
              <input
                type="file"
                onChange={handleFileChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              {uploadData.file && (
                <p className="mt-1 text-sm text-gray-500">
                  Selected: {uploadData.file.name} ({formatFileSize(uploadData.file.size)})
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title (optional)
              </label>
              <input
                type="text"
                value={uploadData.title}
                onChange={(e) => setUploadData({ ...uploadData, title: e.target.value })}
                placeholder="Custom display name"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description (optional)
              </label>
              <textarea
                value={uploadData.description}
                onChange={(e) => setUploadData({ ...uploadData, description: e.target.value })}
                placeholder="Brief description of this material"
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <button
              type="submit"
              disabled={isUploading || !uploadData.file}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition font-medium"
            >
              {isUploading ? 'Uploading...' : 'Upload Material'}
            </button>
          </div>
        </form>
      )}

      {/* Materials List */}
      {materials.length === 0 ? (
        <p className="text-gray-500 text-center py-8">
          No materials uploaded yet. Click "Add Material" to upload files.
        </p>
      ) : (
        <div className="space-y-3">
          {materials.map((material) => (
            <div
              key={material.id}
              className="flex items-start justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-2xl">
                    {getFileIcon(material.file_type || material.original_filename)}
                  </span>
                  <h3 className="font-semibold text-gray-900">
                    {material.title || material.original_filename}
                  </h3>
                </div>
                {material.description && (
                  <p className="text-sm text-gray-600 mb-2 ml-8">{material.description}</p>
                )}
                <div className="flex items-center gap-4 text-xs text-gray-500 ml-8">
                  <span>{formatFileSize(material.file_size)}</span>
                  <span>•</span>
                  <span>
                    Uploaded {new Date(material.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
              <div className="flex gap-2 ml-4">
                <a
                  href={material.file_url}
                  download={material.original_filename}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm font-medium"
                >
                  Download
                </a>
                <button
                  onClick={() => handleDelete(material.id, material.title || material.original_filename)}
                  className="px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition text-sm font-medium"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MaterialsManager;
