import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { promptsAPI } from '../../services/api';
import type { PromptTemplate } from '../../types';

const PromptsListPage: React.FC = () => {
  const navigate = useNavigate();
  const [prompts, setPrompts] = useState<PromptTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  // Filters
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  const [activeOnly, setActiveOnly] = useState(false);

  useEffect(() => {
    loadPrompts();
  }, [page, categoryFilter, activeOnly]);

  const loadPrompts = async () => {
    try {
      setLoading(true);
      setError(null);
      const params: any = {
        page,
        page_size: pageSize,
      };

      if (categoryFilter) {
        params.category = categoryFilter;
      }

      if (activeOnly) {
        params.active_only = true;
      }

      const data = await promptsAPI.list(params);
      setPrompts(data.prompts);
      setTotal(data.total);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load prompts');
      console.error('Error loading prompts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number, name: string) => {
    if (!window.confirm(`Are you sure you want to delete prompt "${name}"?`)) {
      return;
    }

    try {
      await promptsAPI.delete(id);
      loadPrompts();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete prompt');
    }
  };

  const getCategoryBadge = (category: string) => {
    const colors: { [key: string]: string } = {
      chat: 'bg-blue-100 text-blue-800',
      quiz: 'bg-green-100 text-green-800',
      voice_ai: 'bg-purple-100 text-purple-800',
      analysis: 'bg-yellow-100 text-yellow-800',
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  const filteredPrompts = prompts.filter((prompt) => {
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      return (
        prompt.name.toLowerCase().includes(search) ||
        prompt.description?.toLowerCase().includes(search) ||
        prompt.category.toLowerCase().includes(search)
      );
    }
    return true;
  });

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Prompt Management</h1>
              <p className="mt-2 text-sm text-gray-600">
                Manage AI prompts for chat, quiz, voice AI, and analysis features
              </p>
            </div>
            <button
              onClick={() => navigate('/admin/prompts/new')}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              + Create Prompt
            </button>
          </div>

          {/* Filters */}
          <div className="bg-white rounded-lg shadow p-4 mb-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Search */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Search
                </label>
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search by name, category..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {/* Category Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category
                </label>
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">All Categories</option>
                  <option value="chat">Chat</option>
                  <option value="quiz">Quiz</option>
                  <option value="voice_ai">Voice AI</option>
                  <option value="analysis">Analysis</option>
                </select>
              </div>

              {/* Active Only */}
              <div className="flex items-end">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={activeOnly}
                    onChange={(e) => setActiveOnly(e.target.checked)}
                    className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Active Only</span>
                </label>
              </div>

              {/* Refresh Button */}
              <div className="flex items-end">
                <button
                  onClick={loadPrompts}
                  className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                >
                  Refresh
                </button>
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">
              Showing <span className="font-semibold">{filteredPrompts.length}</span> of{' '}
              <span className="font-semibold">{total}</span> prompts
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Loading State */}
        {loading ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-300 border-t-indigo-600"></div>
            <p className="mt-2 text-gray-600">Loading prompts...</p>
          </div>
        ) : (
          <>
            {/* Prompts Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Category
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Model
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Version
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Usage
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredPrompts.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                          No prompts found. Create your first prompt to get started.
                        </td>
                      </tr>
                    ) : (
                      filteredPrompts.map((prompt) => (
                        <tr key={prompt.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4">
                            <div className="text-sm font-medium text-gray-900">{prompt.name}</div>
                            {prompt.description && (
                              <div className="text-sm text-gray-500 mt-1 max-w-xs truncate">
                                {prompt.description}
                              </div>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span
                              className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getCategoryBadge(
                                prompt.category
                              )}`}
                            >
                              {prompt.category}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">{prompt.model}</div>
                            <div className="text-xs text-gray-500">
                              temp: {prompt.temperature} | tokens: {prompt.max_tokens}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-sm text-gray-900">{prompt.version}</span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex flex-col gap-1">
                              <span
                                className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                  prompt.is_active
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-red-100 text-red-800'
                                }`}
                              >
                                {prompt.is_active ? 'Active' : 'Inactive'}
                              </span>
                              {prompt.is_default && (
                                <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                                  Default
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">{prompt.usage_count} times</div>
                            {prompt.last_used_at && (
                              <div className="text-xs text-gray-500">
                                Last: {new Date(prompt.last_used_at).toLocaleDateString()}
                              </div>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex gap-2">
                              <button
                                onClick={() => navigate(`/admin/prompts/${prompt.id}`)}
                                className="text-indigo-600 hover:text-indigo-900"
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => navigate(`/admin/prompts/${prompt.id}/test`)}
                                className="text-green-600 hover:text-green-900"
                              >
                                Test
                              </button>
                              <button
                                onClick={() => handleDelete(prompt.id, prompt.name)}
                                className="text-red-600 hover:text-red-900"
                              >
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-4 flex justify-between items-center">
                <div className="text-sm text-gray-600">
                  Page {page} of {totalPages}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default PromptsListPage;
