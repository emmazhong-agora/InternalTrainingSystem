import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../../components/Layout';
import { statisticsAPI } from '../../services/api';
import { SystemOverview, PopularContent } from '../../types';

const AdminDashboardPage: React.FC = () => {
  const [overview, setOverview] = useState<SystemOverview | null>(null);
  const [popular, setPopular] = useState<PopularContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [overviewData, popularData] = await Promise.all([
        statisticsAPI.getOverview(),
        statisticsAPI.getPopular(30)
      ]);

      setOverview(overviewData);
      setPopular(popularData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load statistics');
      console.error('Error fetching statistics:', err);
    } finally {
      setLoading(false);
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
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600 mt-1">System overview and statistics</p>
        </div>

        {/* Overview Cards */}
        {overview && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Users</p>
                  <p className="text-3xl font-bold text-blue-600">{overview.total_users}</p>
                  <p className="text-xs text-gray-500 mt-1">{overview.active_users} active</p>
                </div>
                <div className="text-blue-600">
                  <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Videos</p>
                  <p className="text-3xl font-bold text-green-600">{overview.total_videos}</p>
                  <p className="text-xs text-gray-500 mt-1">{overview.total_categories} categories</p>
                </div>
                <div className="text-green-600">
                  <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Watch Hours</p>
                  <p className="text-3xl font-bold text-purple-600">{overview.total_watch_hours.toFixed(1)}</p>
                  <p className="text-xs text-gray-500 mt-1">Total hours watched</p>
                </div>
                <div className="text-purple-600">
                  <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">AI Interactions</p>
                  <p className="text-3xl font-bold text-orange-600">{overview.total_chat_sessions}</p>
                  <p className="text-xs text-gray-500 mt-1">{overview.total_chat_messages} messages</p>
                </div>
                <div className="text-orange-600">
                  <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Popular Content */}
        {popular && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Most Viewed Videos */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Most Viewed Videos</h2>
                <p className="text-sm text-gray-600">Last 30 days</p>
              </div>
              <div className="p-6">
                {popular.most_viewed_videos.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">No data available</p>
                ) : (
                  <ul className="space-y-3">
                    {popular.most_viewed_videos.slice(0, 5).map((video, index) => (
                      <li key={video.video_id} className="flex items-center justify-between">
                        <div className="flex items-center space-x-3 flex-1 min-w-0">
                          <span className="text-lg font-semibold text-gray-400">#{index + 1}</span>
                          <Link
                            to={`/videos/${video.video_id}`}
                            className="text-blue-600 hover:text-blue-800 truncate"
                          >
                            {video.title}
                          </Link>
                        </div>
                        <span className="ml-4 px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                          {video.views} views
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {/* Most Completed Videos */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Most Completed Videos</h2>
                <p className="text-sm text-gray-600">Last 30 days</p>
              </div>
              <div className="p-6">
                {popular.most_completed_videos.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">No data available</p>
                ) : (
                  <ul className="space-y-3">
                    {popular.most_completed_videos.slice(0, 5).map((video, index) => (
                      <li key={video.video_id} className="flex items-center justify-between">
                        <div className="flex items-center space-x-3 flex-1 min-w-0">
                          <span className="text-lg font-semibold text-gray-400">#{index + 1}</span>
                          <Link
                            to={`/videos/${video.video_id}`}
                            className="text-blue-600 hover:text-blue-800 truncate"
                          >
                            {video.title}
                          </Link>
                        </div>
                        <span className="ml-4 px-3 py-1 bg-green-100 text-green-800 text-sm font-medium rounded-full">
                          {video.completions} completed
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {/* Most Discussed Videos */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Most Discussed Videos</h2>
                <p className="text-sm text-gray-600">Most AI chat sessions</p>
              </div>
              <div className="p-6">
                {popular.most_discussed_videos.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">No data available</p>
                ) : (
                  <ul className="space-y-3">
                    {popular.most_discussed_videos.slice(0, 5).map((video, index) => (
                      <li key={video.video_id} className="flex items-center justify-between">
                        <div className="flex items-center space-x-3 flex-1 min-w-0">
                          <span className="text-lg font-semibold text-gray-400">#{index + 1}</span>
                          <Link
                            to={`/videos/${video.video_id}`}
                            className="text-blue-600 hover:text-blue-800 truncate"
                          >
                            {video.title}
                          </Link>
                        </div>
                        <span className="ml-4 px-3 py-1 bg-orange-100 text-orange-800 text-sm font-medium rounded-full">
                          {video.chat_sessions} chats
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {/* Popular Categories */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Popular Categories</h2>
                <p className="text-sm text-gray-600">By total views</p>
              </div>
              <div className="p-6">
                {popular.popular_categories.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">No data available</p>
                ) : (
                  <ul className="space-y-3">
                    {popular.popular_categories.slice(0, 5).map((category, index) => (
                      <li key={category.category_id} className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <span className="text-lg font-semibold text-gray-400">#{index + 1}</span>
                          <span className="text-gray-900">{category.name}</span>
                        </div>
                        <span className="ml-4 px-3 py-1 bg-purple-100 text-purple-800 text-sm font-medium rounded-full">
                          {category.views} views
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              to="/admin/users"
              className="flex items-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
            >
              <svg className="w-8 h-8 text-blue-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              <div>
                <div className="font-semibold text-gray-900">Manage Users</div>
                <div className="text-sm text-gray-600">View and edit users</div>
              </div>
            </Link>

            <Link
              to="/admin/upload"
              className="flex items-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
            >
              <svg className="w-8 h-8 text-green-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <div>
                <div className="font-semibold text-gray-900">Upload Video</div>
                <div className="text-sm text-gray-600">Add new content</div>
              </div>
            </Link>

            <Link
              to="/admin/prompts"
              className="flex items-center p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
            >
              <svg className="w-8 h-8 text-purple-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <div>
                <div className="font-semibold text-gray-900">Manage Prompts</div>
                <div className="text-sm text-gray-600">Configure AI prompts</div>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default AdminDashboardPage;
