import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from '../../components/Layout';
import { usersAPI } from '../../services/api';
import { UserDetailResponse, UserCreateData, UserUpdateData } from '../../types';

const UserEditorPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEditMode = id !== 'new' && id !== undefined;
  const userId = isEditMode ? parseInt(id) : null;

  const [loading, setLoading] = useState(isEditMode);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    full_name: '',
    is_active: true,
    is_admin: false,
  });

  useEffect(() => {
    if (isEditMode && userId) {
      fetchUser();
    }
  }, [userId]);

  const fetchUser = async () => {
    try {
      setLoading(true);
      setError(null);
      const user = await usersAPI.getById(userId!);
      setFormData({
        email: user.email,
        username: user.username,
        password: '', // Don't pre-fill password
        full_name: user.full_name || '',
        is_active: user.is_active,
        is_admin: user.is_admin,
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load user');
      console.error('Error fetching user:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!formData.email || !formData.username) {
      setError('Email and username are required');
      return;
    }

    if (!isEditMode && !formData.password) {
      setError('Password is required when creating a new user');
      return;
    }

    if (formData.password && formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    try {
      setSaving(true);
      setError(null);

      if (isEditMode && userId) {
        // Update existing user
        const updateData: UserUpdateData = {
          email: formData.email,
          username: formData.username,
          full_name: formData.full_name || undefined,
          is_active: formData.is_active,
          is_admin: formData.is_admin,
        };

        // Only include password if it was changed
        if (formData.password) {
          updateData.password = formData.password;
        }

        await usersAPI.update(userId, updateData);
        navigate(`/admin/users/${userId}`);
      } else {
        // Create new user
        const createData: UserCreateData = {
          email: formData.email,
          username: formData.username,
          password: formData.password,
          full_name: formData.full_name || undefined,
          is_admin: formData.is_admin,
        };

        const newUser = await usersAPI.create(createData, formData.is_admin);
        navigate(`/admin/users/${newUser.id}`);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save user');
      console.error('Error saving user:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
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

  return (
    <Layout>
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/admin/users')}
            className="text-gray-600 hover:text-gray-900"
          >
            ← Back to Users
          </button>
          <h1 className="text-3xl font-bold text-gray-900">
            {isEditMode ? 'Edit User' : 'Create New User'}
          </h1>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Account Information */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Account Information</h2>
            <div className="space-y-4">
              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleChange('email', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>

              {/* Username */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Username <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => handleChange('username', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                  minLength={3}
                  maxLength={50}
                />
              </div>

              {/* Password */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Password {!isEditMode && <span className="text-red-500">*</span>}
                </label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => handleChange('password', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required={!isEditMode}
                  minLength={8}
                  placeholder={isEditMode ? 'Leave blank to keep current password' : 'Minimum 8 characters'}
                />
                {isEditMode && (
                  <p className="text-sm text-gray-500 mt-1">
                    Leave blank to keep the current password
                  </p>
                )}
              </div>

              {/* Full Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => handleChange('full_name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Optional"
                />
              </div>
            </div>
          </div>

          {/* Permissions & Status */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Permissions & Status</h2>
            <div className="space-y-4">
              {/* Is Admin */}
              <div className="flex items-start">
                <div className="flex items-center h-5">
                  <input
                    type="checkbox"
                    checked={formData.is_admin}
                    onChange={(e) => handleChange('is_admin', e.target.checked)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                </div>
                <div className="ml-3">
                  <label className="font-medium text-gray-700">
                    Administrator
                  </label>
                  <p className="text-sm text-gray-500">
                    Grant admin privileges to manage users, videos, and system settings
                  </p>
                </div>
              </div>

              {/* Is Active */}
              {isEditMode && (
                <div className="flex items-start">
                  <div className="flex items-center h-5">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => handleChange('is_active', e.target.checked)}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                  </div>
                  <div className="ml-3">
                    <label className="font-medium text-gray-700">
                      Active Account
                    </label>
                    <p className="text-sm text-gray-500">
                      Allow this user to access the system
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={() => navigate('/admin/users')}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : isEditMode ? 'Update User' : 'Create User'}
            </button>
          </div>
        </form>
      </div>
    </Layout>
  );
};

export default UserEditorPage;
