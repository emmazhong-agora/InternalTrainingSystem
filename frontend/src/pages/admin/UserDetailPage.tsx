import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import Layout from '../../components/Layout';
import { usersAPI } from '../../services/api';
import { UserDetailResponse, LearningProgress, ChatSession } from '../../types';

const UserDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const userId = parseInt(id || '0');

  const [user, setUser] = useState<UserDetailResponse | null>(null);
  const [progress, setProgress] = useState<LearningProgress[]>([]);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'progress' | 'chats'>('overview');

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch user details
        const userResponse = await usersAPI.getById(userId);
        setUser(userResponse);

        // Fetch learning progress
        const progressResponse = await usersAPI.getProgress(userId);
        setProgress(progressResponse);

        // Fetch chat sessions
        const chatResponse = await usersAPI.getChatSessions(userId);
        setChatSessions(chatResponse);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load user data');
        console.error('Error fetching user data:', err);
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      fetchUserData();
    }
  }, [userId]);

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const formatDate = (dateString?: string): string => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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

  if (error || !user) {
    return (
      <Layout>
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/admin/users')}
              className="text-gray-600 hover:text-gray-900"
            >
              ← Back to Users
            </button>
          </div>
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error || 'User not found'}
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/admin/users')}
              className="text-gray-600 hover:text-gray-900"
            >
              ← Back to Users
            </button>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold text-gray-900">{user.username}</h1>
                {user.is_admin && (
                  <span className="px-3 py-1 text-sm font-semibold rounded-full bg-purple-100 text-purple-800">
                    Admin
                  </span>
                )}
                {user.is_active ? (
                  <span className="px-3 py-1 text-sm font-semibold rounded-full bg-green-100 text-green-800">
                    Active
                  </span>
                ) : (
                  <span className="px-3 py-1 text-sm font-semibold rounded-full bg-red-100 text-red-800">
                    Inactive
                  </span>
                )}
              </div>
              <p className="text-gray-600 mt-1">{user.email}</p>
              {user.full_name && <p className="text-gray-600">{user.full_name}</p>}
            </div>
          </div>
          <Link
            to={`/admin/users/${user.id}/edit`}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Edit User
          </Link>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="flex gap-8">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'overview'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('progress')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'progress'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Learning Progress ({progress.length})
            </button>
            <button
              onClick={() => setActiveTab('chats')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'chats'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Chat Sessions ({chatSessions.length})
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Account Information */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">Account Information</h2>
              <div className="space-y-3">
                <div>
                  <label className="text-sm text-gray-500">User ID</label>
                  <div className="text-gray-900">{user.id}</div>
                </div>
                <div>
                  <label className="text-sm text-gray-500">Username</label>
                  <div className="text-gray-900">{user.username}</div>
                </div>
                <div>
                  <label className="text-sm text-gray-500">Email</label>
                  <div className="text-gray-900">{user.email}</div>
                </div>
                <div>
                  <label className="text-sm text-gray-500">Full Name</label>
                  <div className="text-gray-900">{user.full_name || 'Not provided'}</div>
                </div>
                <div>
                  <label className="text-sm text-gray-500">Created At</label>
                  <div className="text-gray-900">{formatDate(user.created_at)}</div>
                </div>
                <div>
                  <label className="text-sm text-gray-500">Last Activity</label>
                  <div className="text-gray-900">{formatDate(user.last_activity)}</div>
                </div>
              </div>
            </div>

            {/* Learning Statistics */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">Learning Statistics</h2>
              <div className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                  <div>
                    <div className="text-sm text-gray-600">Videos Watched</div>
                    <div className="text-2xl font-bold text-blue-600">{user.total_videos_watched}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-600">Completed</div>
                    <div className="text-xl font-semibold text-green-600">{user.videos_completed}</div>
                  </div>
                </div>
                <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                  <div>
                    <div className="text-sm text-gray-600">Total Watch Time</div>
                    <div className="text-2xl font-bold text-purple-600">
                      {formatDuration(user.total_watch_time)}
                    </div>
                  </div>
                </div>
                <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                  <div>
                    <div className="text-sm text-gray-600">Chat Sessions</div>
                    <div className="text-2xl font-bold text-green-600">{user.chat_sessions_count}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-600">Messages</div>
                    <div className="text-xl font-semibold text-green-700">{user.total_chat_messages}</div>
                  </div>
                </div>
                <div className="flex justify-between items-center p-3 bg-yellow-50 rounded-lg">
                  <div>
                    <div className="text-sm text-gray-600">Quizzes Taken</div>
                    <div className="text-2xl font-bold text-yellow-600">{user.quizzes_taken}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'progress' && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            {progress.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500">No learning progress yet</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Video ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Progress
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Watch Time
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Last Accessed
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {progress.map((item) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Link
                            to={`/videos/${item.video_id}`}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            Video #{item.video_id}
                          </Link>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="w-full bg-gray-200 rounded-full h-2 mr-2" style={{ width: '100px' }}>
                              <div
                                className="bg-blue-600 h-2 rounded-full"
                                style={{ width: `${item.completion_percentage}%` }}
                              ></div>
                            </div>
                            <span className="text-sm text-gray-700">
                              {Math.round(item.completion_percentage)}%
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatDuration(item.total_watch_time)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {item.is_completed ? (
                            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                              Completed
                            </span>
                          ) : (
                            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                              In Progress
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatDate(item.last_accessed)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {activeTab === 'chats' && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            {chatSessions.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500">No chat sessions yet</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Session ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Video ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Title
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Messages
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Last Message
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Created
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {chatSessions.map((session) => (
                      <tr key={session.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          #{session.id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Link
                            to={`/videos/${session.video_id}`}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            Video #{session.video_id}
                          </Link>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900">
                          {session.title || 'Untitled Session'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {session.messages?.length || 0} messages
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatDate(session.last_message_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatDate(session.created_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default UserDetailPage;
