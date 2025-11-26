import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import VideosPage from './pages/VideosPage';
import VideoPlayerPage from './pages/VideoPlayerPage';
import UploadPage from './pages/UploadPage';
import ExamTakerPage from './pages/ExamTakerPage';

// Admin Pages
import AdminDashboardPage from './pages/admin/AdminDashboardPage';
import PromptsListPage from './pages/admin/PromptsListPage';
import PromptEditorPage from './pages/admin/PromptEditorPage';
import UsersListPage from './pages/admin/UsersListPage';
import UserDetailPage from './pages/admin/UserDetailPage';
import UserEditorPage from './pages/admin/UserEditorPage';
import CategoriesListPage from './pages/admin/CategoriesListPage';
import CategoryEditorPage from './pages/admin/CategoryEditorPage';
import ExamsListPage from './pages/admin/ExamsListPage';
import ExamCreatorPage from './pages/admin/ExamCreatorPage';
import ExamResultsPage from './pages/admin/ExamResultsPage';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/exam/:id" element={<ExamTakerPage />} />

          {/* Protected routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <HomePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/videos"
            element={
              <ProtectedRoute>
                <VideosPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/videos/:id"
            element={
              <ProtectedRoute>
                <VideoPlayerPage />
              </ProtectedRoute>
            }
          />

          {/* Admin routes */}
          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute requireAdmin>
                <AdminDashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/upload"
            element={
              <ProtectedRoute requireAdmin>
                <UploadPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/categories"
            element={
              <ProtectedRoute requireAdmin>
                <CategoriesListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/categories/new"
            element={
              <ProtectedRoute requireAdmin>
                <CategoryEditorPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/categories/:id/edit"
            element={
              <ProtectedRoute requireAdmin>
                <CategoryEditorPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/prompts"
            element={
              <ProtectedRoute requireAdmin>
                <PromptsListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/prompts/new"
            element={
              <ProtectedRoute requireAdmin>
                <PromptEditorPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/prompts/:id"
            element={
              <ProtectedRoute requireAdmin>
                <PromptEditorPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/users"
            element={
              <ProtectedRoute requireAdmin>
                <UsersListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/users/new"
            element={
              <ProtectedRoute requireAdmin>
                <UserEditorPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/users/:id"
            element={
              <ProtectedRoute requireAdmin>
                <UserDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/users/:id/edit"
            element={
              <ProtectedRoute requireAdmin>
                <UserEditorPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/exams"
            element={
              <ProtectedRoute requireAdmin>
                <ExamsListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/exams/create"
            element={
              <ProtectedRoute requireAdmin>
                <ExamCreatorPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/exams/:id/edit"
            element={
              <ProtectedRoute requireAdmin>
                <ExamCreatorPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/exams/:id/results"
            element={
              <ProtectedRoute requireAdmin>
                <ExamResultsPage />
              </ProtectedRoute>
            }
          />

          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
