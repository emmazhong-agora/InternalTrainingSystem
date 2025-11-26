import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Layout from '../../components/Layout';
import { categoriesAPI } from '../../services/api';
import { VideoCategory, VideoCategoryCreate, VideoCategoryUpdate } from '../../types';

// Common emoji icons for categories
const COMMON_ICONS = [
  '📁', '📂', '📚', '📖', '📝', '📊', '📈', '📉',
  '💼', '🎓', '🎯', '🚀', '💡', '🔧', '🛠️', '⚙️',
  '🎨', '🎬', '🎭', '🎪', '🎮', '🎲', '🎰', '🎳',
  '📱', '💻', '🖥️', '⌨️', '🖱️', '🖨️', '📷', '📹',
  '🌍', '🌎', '🌏', '🗺️', '🧭', '📍', '🏢', '🏭',
  '🔬', '🔭', '🔨', '⚡', '🔥', '💧', '🌱', '🌲',
];

const CategoryEditorPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEditMode = Boolean(id);

  const [loading, setLoading] = useState(isEditMode);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [parentId, setParentId] = useState<number | undefined>(undefined);
  const [icon, setIcon] = useState('📁');
  const [sortOrder, setSortOrder] = useState(0);
  const [isActive, setIsActive] = useState(true);
  const [customIcon, setCustomIcon] = useState('');
  const [showIconPicker, setShowIconPicker] = useState(false);

  // Available parent categories
  const [allCategories, setAllCategories] = useState<VideoCategory[]>([]);

  useEffect(() => {
    fetchAllCategories();
    if (isEditMode && id) {
      fetchCategory(parseInt(id));
    }
  }, [id, isEditMode]);

  const fetchAllCategories = async () => {
    try {
      const data = await categoriesAPI.list({ include_inactive: false });
      setAllCategories(data);
    } catch (err) {
      console.error('Error fetching categories:', err);
    }
  };

  const fetchCategory = async (categoryId: number) => {
    try {
      setLoading(true);
      setError(null);
      const category = await categoriesAPI.getById(categoryId);

      setName(category.name);
      setDescription(category.description || '');
      setParentId(category.parent_id);
      setIcon(category.icon || '📁');
      setSortOrder(category.sort_order);
      setIsActive(category.is_active);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load category');
      console.error('Error fetching category:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      setError('Category name is required');
      return;
    }

    try {
      setSaving(true);
      setError(null);

      const finalIcon = customIcon.trim() || icon;

      const categoryCreateData: VideoCategoryCreate = {
        name: name.trim(),
        description: description.trim() || undefined,
        parent_id: parentId,
        icon: finalIcon,
        sort_order: sortOrder,
        is_active: isActive,
      };

      if (isEditMode && id) {
        const updatePayload: VideoCategoryUpdate = { ...categoryCreateData };
        await categoriesAPI.update(parseInt(id), updatePayload);
      } else {
        await categoriesAPI.create(categoryCreateData);
      }

      navigate('/admin/categories');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save category');
      console.error('Error saving category:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleIconSelect = (selectedIcon: string) => {
    setIcon(selectedIcon);
    setCustomIcon('');
    setShowIconPicker(false);
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  // Filter out current category from parent options (can't be its own parent)
  const availableParents = allCategories.filter((cat) => {
    if (isEditMode && id) {
      return cat.id !== parseInt(id);
    }
    return true;
  });

  return (
    <Layout>
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {isEditMode ? 'Edit Category' : 'New Category'}
            </h1>
            <p className="text-gray-600 mt-1">
              {isEditMode ? 'Update category details' : 'Create a new video category'}
            </p>
          </div>
          <button
            onClick={() => navigate('/admin/categories')}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            Cancel
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-6">
          {/* Category Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              Category Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., Technical Training, Product Updates"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Brief description of this category..."
            />
          </div>

          {/* Parent Category */}
          <div>
            <label htmlFor="parent" className="block text-sm font-medium text-gray-700 mb-2">
              Parent Category
            </label>
            <select
              id="parent"
              value={parentId || ''}
              onChange={(e) => setParentId(e.target.value ? parseInt(e.target.value) : undefined)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">None (Top Level)</option>
              {availableParents.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.icon} {cat.name}
                </option>
              ))}
            </select>
            <p className="mt-1 text-sm text-gray-500">
              Leave empty to create a top-level category
            </p>
          </div>

          {/* Icon Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Icon</label>
            <div className="space-y-3">
              {/* Current Icon Display */}
              <div className="flex items-center gap-3">
                <div className="text-4xl">{customIcon || icon}</div>
                <button
                  type="button"
                  onClick={() => setShowIconPicker(!showIconPicker)}
                  className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                >
                  {showIconPicker ? 'Hide Icons' : 'Choose Icon'}
                </button>
              </div>

              {/* Icon Picker */}
              {showIconPicker && (
                <div className="border border-gray-300 rounded-lg p-4 bg-gray-50">
                  <div className="grid grid-cols-8 gap-2">
                    {COMMON_ICONS.map((emoji) => (
                      <button
                        key={emoji}
                        type="button"
                        onClick={() => handleIconSelect(emoji)}
                        className={`text-2xl p-2 rounded hover:bg-blue-100 transition-colors ${
                          (customIcon || icon) === emoji ? 'bg-blue-100 ring-2 ring-blue-500' : ''
                        }`}
                      >
                        {emoji}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Custom Icon Input */}
              <div>
                <input
                  type="text"
                  value={customIcon}
                  onChange={(e) => setCustomIcon(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Or enter custom emoji or icon..."
                  maxLength={10}
                />
                <p className="mt-1 text-sm text-gray-500">
                  You can paste any emoji or short text
                </p>
              </div>
            </div>
          </div>

          {/* Sort Order */}
          <div>
            <label htmlFor="sortOrder" className="block text-sm font-medium text-gray-700 mb-2">
              Sort Order
            </label>
            <input
              type="number"
              id="sortOrder"
              value={sortOrder}
              onChange={(e) => setSortOrder(parseInt(e.target.value) || 0)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="0"
            />
            <p className="mt-1 text-sm text-gray-500">
              Lower numbers appear first. Default is 0.
            </p>
          </div>

          {/* Active Toggle */}
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="isActive"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="isActive" className="text-sm font-medium text-gray-700">
              Active (visible to users)
            </label>
          </div>

          {/* Submit Button */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={() => navigate('/admin/categories')}
              className="px-6 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {saving && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              )}
              {saving ? 'Saving...' : isEditMode ? 'Update Category' : 'Create Category'}
            </button>
          </div>
        </form>

        {/* Preview */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Preview</h2>
          <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
            <div className="text-3xl">{customIcon || icon}</div>
            <div className="flex-1">
              <h3 className="font-medium text-gray-900">{name || 'Category Name'}</h3>
              {description && <p className="text-sm text-gray-500 mt-1">{description}</p>}
            </div>
            {!isActive && (
              <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">Inactive</span>
            )}
          </div>
          {parentId && (
            <p className="text-sm text-gray-600 mt-2">
              Parent:{' '}
              {availableParents.find((c) => c.id === parentId)?.name || 'Unknown'}
            </p>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default CategoryEditorPage;
