import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { videosAPI, categoriesAPI } from '../services/api';
import type { Video, VideoCategoryTree } from '../types';
import Layout from '../components/Layout';

interface CategoryTreeItemProps {
  category: VideoCategoryTree;
  level: number;
  selectedId: number | null;
  onSelect: (id: number | null) => void;
}

const CategoryTreeItem: React.FC<CategoryTreeItemProps> = ({ category, level, selectedId, onSelect }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const isSelected = selectedId === category.id;

  return (
    <div>
      <button
        onClick={() => onSelect(category.id)}
        className={`w-full flex items-center gap-2 px-3 py-2 text-left rounded-lg transition-colors ${
          isSelected
            ? 'bg-blue-100 text-blue-700 font-medium'
            : 'hover:bg-gray-100 text-gray-700'
        }`}
        style={{ paddingLeft: `${level * 0.75 + 0.75}rem` }}
      >
        {category.children.length > 0 && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
            className="flex-shrink-0 w-4 h-4 flex items-center justify-center hover:bg-gray-200 rounded"
          >
            <svg
              className={`w-3 h-3 transform transition-transform ${isExpanded ? 'rotate-90' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        )}
        {category.children.length === 0 && <div className="w-4" />}
        <span className="text-lg flex-shrink-0">{category.icon || '📁'}</span>
        <span className="flex-1 truncate text-sm">{category.name}</span>
        <span className="text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded-full">
          {category.video_count}
        </span>
      </button>

      {isExpanded && category.children.length > 0 && (
        <div className="mt-1">
          {category.children.map((child) => (
            <CategoryTreeItem
              key={child.id}
              category={child}
              level={level + 1}
              selectedId={selectedId}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const VideosPage: React.FC = () => {
  const [videos, setVideos] = useState<Video[]>([]);
  const [categories, setCategories] = useState<VideoCategoryTree[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    loadCategories();
  }, []);

  useEffect(() => {
    loadVideos();
  }, [page, search, selectedCategory]);

  const loadCategories = async () => {
    try {
      const data = await categoriesAPI.getTree();
      setCategories(data);
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const loadVideos = async () => {
    setLoading(true);
    try {
      const response = await videosAPI.list({
        page,
        search: search || undefined,
        category_id: selectedCategory || undefined,
      });
      setVideos(response.videos);
      setTotal(response.total);
    } catch (error) {
      console.error('Error loading videos:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getVectorizationStatusBadge = (status: string) => {
    const badges = {
      pending: { text: 'Pending', color: 'bg-yellow-100 text-yellow-800' },
      processing: { text: 'Processing...', color: 'bg-blue-100 text-blue-800 animate-pulse' },
      completed: { text: 'Ready', color: 'bg-green-100 text-green-800' },
      failed: { text: 'Failed', color: 'bg-red-100 text-red-800' },
    };

    const badge = badges[status as keyof typeof badges] || badges.pending;
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded ${badge.color}`}>
        {badge.text}
      </span>
    );
  };

  // Build breadcrumb path
  const getBreadcrumbPath = (categoryId: number | null): { id: number; name: string; icon?: string }[] => {
    if (!categoryId) return [];

    const path: { id: number; name: string; icon?: string }[] = [];
    const findPath = (cats: VideoCategoryTree[], targetId: number, currentPath: VideoCategoryTree[]): boolean => {
      for (const cat of cats) {
        const newPath = [...currentPath, cat];
        if (cat.id === targetId) {
          path.push(...newPath.map(c => ({ id: c.id, name: c.name, icon: c.icon })));
          return true;
        }
        if (cat.children.length > 0 && findPath(cat.children, targetId, newPath)) {
          return true;
        }
      }
      return false;
    };

    findPath(categories, categoryId, []);
    return path;
  };

  const breadcrumbPath = getBreadcrumbPath(selectedCategory);

  return (
    <Layout>
      <div className="flex gap-6 h-full">
        {/* Sidebar */}
        <div
          className={`${
            sidebarOpen ? 'w-72' : 'w-0'
          } flex-shrink-0 transition-all duration-300 overflow-hidden`}
        >
          <div className="bg-white rounded-lg shadow p-4 h-full overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Categories</h2>
              <button
                onClick={() => setSidebarOpen(false)}
                className="lg:hidden p-1 hover:bg-gray-100 rounded"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* All Videos Option */}
            <button
              onClick={() => setSelectedCategory(null)}
              className={`w-full flex items-center gap-2 px-3 py-2 mb-2 text-left rounded-lg transition-colors ${
                selectedCategory === null
                  ? 'bg-blue-100 text-blue-700 font-medium'
                  : 'hover:bg-gray-100 text-gray-700'
              }`}
            >
              <span className="text-lg">📚</span>
              <span className="flex-1 text-sm">All Videos</span>
            </button>

            <div className="border-t pt-2 mt-2">
              {categories.map((category) => (
                <CategoryTreeItem
                  key={category.id}
                  category={category}
                  level={0}
                  selectedId={selectedCategory}
                  onSelect={setSelectedCategory}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 min-w-0">
          <div className="space-y-6">
            {/* Header with Toggle */}
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-3">
                {!sidebarOpen && (
                  <button
                    onClick={() => setSidebarOpen(true)}
                    className="p-2 hover:bg-gray-100 rounded-lg"
                    title="Show categories"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                  </button>
                )}
                <h1 className="text-3xl font-bold text-gray-900">Training Videos</h1>
              </div>
            </div>

            {/* Breadcrumb */}
            {breadcrumbPath.length > 0 && (
              <nav className="flex items-center space-x-2 text-sm text-gray-600">
                <button
                  onClick={() => setSelectedCategory(null)}
                  className="hover:text-blue-600 transition-colors"
                >
                  Home
                </button>
                {breadcrumbPath.map((crumb, index) => (
                  <React.Fragment key={crumb.id}>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    <button
                      onClick={() => setSelectedCategory(crumb.id)}
                      className={`flex items-center gap-1 hover:text-blue-600 transition-colors ${
                        index === breadcrumbPath.length - 1 ? 'font-medium text-gray-900' : ''
                      }`}
                    >
                      {crumb.icon && <span>{crumb.icon}</span>}
                      <span>{crumb.name}</span>
                    </button>
                  </React.Fragment>
                ))}
              </nav>
            )}

            {/* Search */}
            <div>
              <input
                type="text"
                placeholder="Search videos..."
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
              />
            </div>

            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading videos...</p>
              </div>
            ) : videos.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg shadow">
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
                    d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
                <p className="text-gray-500 text-lg">No videos found</p>
                <p className="text-gray-400 mt-2">Try selecting a different category or search term</p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                  {videos.map((video) => (
                    <Link
                      key={video.id}
                      to={`/videos/${video.id}`}
                      className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow"
                    >
                      <div className="aspect-video bg-gradient-to-br from-blue-100 to-blue-200 flex items-center justify-center">
                        <svg
                          className="w-16 h-16 text-blue-400"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" />
                        </svg>
                      </div>
                      <div className="p-4">
                        <h3 className="font-semibold text-lg mb-2 line-clamp-2">
                          {video.title}
                        </h3>
                        {video.description && (
                          <p className="text-gray-600 text-sm mb-2 line-clamp-2">
                            {video.description}
                          </p>
                        )}
                        <div className="flex items-center justify-between text-sm text-gray-500 mb-2">
                          <span>{formatDuration(video.duration)}</span>
                          <span>{new Date(video.created_at).toLocaleDateString()}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-500">AI Assistant:</span>
                          {getVectorizationStatusBadge(video.vectorization_status)}
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>

                {/* Pagination */}
                <div className="flex justify-center mt-8 space-x-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Previous
                  </button>
                  <span className="px-4 py-2 text-gray-700">
                    Page {page} of {Math.max(1, Math.ceil(total / 20))}
                  </span>
                  <button
                    onClick={() => setPage((p) => p + 1)}
                    disabled={page >= Math.ceil(total / 20) || total === 0}
                    className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Next
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default VideosPage;
