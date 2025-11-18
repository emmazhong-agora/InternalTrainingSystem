import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Layout from '../../components/Layout';
import { categoriesAPI } from '../../services/api';
import { VideoCategoryTree } from '../../types';

interface CategoryTreeItemProps {
  category: VideoCategoryTree;
  level: number;
  onDelete: (id: number) => void;
  onToggleActive: (id: number, isActive: boolean) => void;
}

const CategoryTreeItem: React.FC<CategoryTreeItemProps> = ({ category, level, onDelete, onToggleActive }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const navigate = useNavigate();

  const handleDelete = async () => {
    if (window.confirm(`Are you sure you want to delete "${category.name}"?`)) {
      onDelete(category.id);
    }
  };

  const handleToggleActive = async () => {
    onToggleActive(category.id, !category.is_active);
  };

  return (
    <div className="border-l-2 border-gray-200">
      <div
        className={`flex items-center gap-3 p-3 hover:bg-gray-50 ${
          !category.is_active ? 'opacity-50' : ''
        }`}
        style={{ paddingLeft: `${level * 1.5 + 0.75}rem` }}
      >
        {/* Expand/Collapse Button */}
        {category.children.length > 0 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-400 hover:text-gray-600 focus:outline-none"
          >
            <svg
              className={`w-4 h-4 transform transition-transform ${isExpanded ? 'rotate-90' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        )}
        {category.children.length === 0 && <div className="w-4" />}

        {/* Icon */}
        <div className="text-2xl">{category.icon || '📁'}</div>

        {/* Category Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-medium text-gray-900 truncate">{category.name}</h3>
            {!category.is_active && (
              <span className="px-2 py-0.5 text-xs bg-red-100 text-red-800 rounded">Inactive</span>
            )}
          </div>
          {category.description && (
            <p className="text-sm text-gray-500 truncate">{category.description}</p>
          )}
        </div>

        {/* Stats */}
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
              />
            </svg>
            {category.video_count}
          </span>
          {category.children.length > 0 && (
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                />
              </svg>
              {category.children.length}
            </span>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate(`/admin/categories/${category.id}/edit`)}
            className="p-2 text-blue-600 hover:bg-blue-50 rounded"
            title="Edit"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
              />
            </svg>
          </button>
          <button
            onClick={handleToggleActive}
            className={`p-2 rounded ${
              category.is_active
                ? 'text-orange-600 hover:bg-orange-50'
                : 'text-green-600 hover:bg-green-50'
            }`}
            title={category.is_active ? 'Deactivate' : 'Activate'}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {category.is_active ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              )}
            </svg>
          </button>
          <button
            onClick={handleDelete}
            className="p-2 text-red-600 hover:bg-red-50 rounded"
            title="Delete"
            disabled={category.video_count > 0 || category.children.length > 0}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Children */}
      {isExpanded && category.children.length > 0 && (
        <div>
          {category.children.map((child) => (
            <CategoryTreeItem
              key={child.id}
              category={child}
              level={level + 1}
              onDelete={onDelete}
              onToggleActive={onToggleActive}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const CategoriesListPage: React.FC = () => {
  const [categories, setCategories] = useState<VideoCategoryTree[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [includeInactive, setIncludeInactive] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchCategories();
  }, [includeInactive]);

  const fetchCategories = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await categoriesAPI.getTree({ include_inactive: includeInactive });
      setCategories(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load categories');
      console.error('Error fetching categories:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await categoriesAPI.delete(id);
      fetchCategories();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete category');
    }
  };

  const handleToggleActive = async (id: number, isActive: boolean) => {
    try {
      await categoriesAPI.update(id, { is_active: isActive });
      fetchCategories();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update category');
    }
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

  if (error) {
    return (
      <Layout>
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Video Categories</h1>
            <p className="text-gray-600 mt-1">Organize your training videos into categories</p>
          </div>
          <Link
            to="/admin/categories/new"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Category
          </Link>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={includeInactive}
                onChange={(e) => setIncludeInactive(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Show inactive categories</span>
            </label>
          </div>
        </div>

        {/* Category Tree */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center gap-4 text-sm font-medium text-gray-700">
              <div className="flex-1">Category</div>
              <div className="w-24">Videos</div>
              <div className="w-24">Subcategories</div>
              <div className="w-32">Actions</div>
            </div>
          </div>

          {categories.length === 0 ? (
            <div className="p-8 text-center">
              <svg
                className="w-16 h-16 mx-auto text-gray-300 mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                />
              </svg>
              <p className="text-gray-500 text-lg mb-2">No categories yet</p>
              <p className="text-gray-400 mb-4">Create your first category to organize videos</p>
              <button
                onClick={() => navigate('/admin/categories/new')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Create Category
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {categories.map((category) => (
                <CategoryTreeItem
                  key={category.id}
                  category={category}
                  level={0}
                  onDelete={handleDelete}
                  onToggleActive={handleToggleActive}
                />
              ))}
            </div>
          )}
        </div>

        {/* Stats Summary */}
        {categories.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center gap-2 text-blue-800">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span className="text-sm">
                Categories with videos or subcategories cannot be deleted. Remove all videos and
                subcategories first.
              </span>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default CategoriesListPage;
