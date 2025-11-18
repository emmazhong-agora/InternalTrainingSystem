import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Layout from '../components/Layout';

const HomePage: React.FC = () => {
  const { user, isAdmin } = useAuth();

  return (
    <Layout>
      <div className="text-center space-y-8">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome to the Internal Training System
          </h1>
          <p className="text-xl text-gray-600">
            {user ? `Hello, ${user.full_name || user.username}!` : 'Please log in to continue'}
          </p>
        </div>

        <div className={`grid grid-cols-1 gap-6 max-w-6xl mx-auto mt-12 ${isAdmin ? 'md:grid-cols-2 lg:grid-cols-3' : 'md:grid-cols-2'}`}>
          <Link
            to="/videos"
            className="bg-white p-8 rounded-lg shadow-lg hover:shadow-xl transition-shadow"
          >
            <div className="text-blue-600 mb-4">
              <svg
                className="w-16 h-16 mx-auto"
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
            </div>
            <h2 className="text-2xl font-semibold mb-2">Browse Videos</h2>
            <p className="text-gray-600">
              Access all training videos and continue your learning journey
            </p>
          </Link>

          {isAdmin && (
            <>
              <Link
                to="/admin/dashboard"
                className="bg-white p-8 rounded-lg shadow-lg hover:shadow-xl transition-shadow"
              >
                <div className="text-indigo-600 mb-4">
                  <svg
                    className="w-16 h-16 mx-auto"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
                </div>
                <h2 className="text-2xl font-semibold mb-2">Dashboard</h2>
                <p className="text-gray-600">View system statistics and analytics</p>
              </Link>

              <Link
                to="/admin/categories"
                className="bg-white p-8 rounded-lg shadow-lg hover:shadow-xl transition-shadow"
              >
                <div className="text-teal-600 mb-4">
                  <svg
                    className="w-16 h-16 mx-auto"
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
                </div>
                <h2 className="text-2xl font-semibold mb-2">Manage Categories</h2>
                <p className="text-gray-600">Organize videos into hierarchical categories</p>
              </Link>

              <Link
                to="/admin/upload"
                className="bg-white p-8 rounded-lg shadow-lg hover:shadow-xl transition-shadow"
              >
                <div className="text-green-600 mb-4">
                  <svg
                    className="w-16 h-16 mx-auto"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                    />
                  </svg>
                </div>
                <h2 className="text-2xl font-semibold mb-2">Upload Video</h2>
                <p className="text-gray-600">Add new training content to the platform</p>
              </Link>

              <Link
                to="/admin/prompts"
                className="bg-white p-8 rounded-lg shadow-lg hover:shadow-xl transition-shadow"
              >
                <div className="text-purple-600 mb-4">
                  <svg
                    className="w-16 h-16 mx-auto"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                </div>
                <h2 className="text-2xl font-semibold mb-2">Manage Prompts</h2>
                <p className="text-gray-600">Configure AI prompts for chat, quiz, and voice features</p>
              </Link>

              <Link
                to="/admin/users"
                className="bg-white p-8 rounded-lg shadow-lg hover:shadow-xl transition-shadow"
              >
                <div className="text-orange-600 mb-4">
                  <svg
                    className="w-16 h-16 mx-auto"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                    />
                  </svg>
                </div>
                <h2 className="text-2xl font-semibold mb-2">Manage Users</h2>
                <p className="text-gray-600">View and manage user accounts and learning progress</p>
              </Link>
            </>
          )}
        </div>

        <div className="max-w-3xl mx-auto mt-16 bg-blue-50 p-6 rounded-lg">
          <h3 className="text-lg font-semibold mb-3">Features</h3>
          <ul className="text-left space-y-2 text-gray-700">
            <li className="flex items-start">
              <span className="text-blue-600 mr-2">✓</span>
              <span>Access training videos anytime, anywhere</span>
            </li>
            <li className="flex items-start">
              <span className="text-blue-600 mr-2">✓</span>
              <span>Track your learning progress automatically</span>
            </li>
            <li className="flex items-start">
              <span className="text-blue-600 mr-2">✓</span>
              <span>Resume videos from where you left off</span>
            </li>
            <li className="flex items-start">
              <span className="text-blue-600 mr-2">✓</span>
              <span>Search and filter training content easily</span>
            </li>
            {isAdmin && (
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">✓</span>
                <span>Manage and organize training materials (Admin)</span>
              </li>
            )}
          </ul>
        </div>
      </div>
    </Layout>
  );
};

export default HomePage;
