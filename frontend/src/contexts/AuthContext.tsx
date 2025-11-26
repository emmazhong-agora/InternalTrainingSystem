import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User, LoginCredentials, RegisterData, AuthResponse } from '../types';
import { authAPI } from '../services/api';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  clearError: () => void;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  registerAdmin: (data: RegisterData) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if user is logged in on mount
    const token = localStorage.getItem('access_token');
    const storedUser = localStorage.getItem('user');

    if (token && storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (error) {
        console.error('Error parsing stored user:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
      }
    }

    setLoading(false);
  }, []);

  const login = async (credentials: LoginCredentials) => {
    setError(null);
    try {
      const response: AuthResponse = await authAPI.login(credentials);
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
      setUser(response.user);
    } catch (err: any) {
      const detail =
        err.response?.data?.detail ||
        err.message ||
        'Failed to login. Please check your credentials.';
      setError(detail);
      throw err;
    }
  };

  const register = async (data: RegisterData) => {
    setError(null);
    try {
      await authAPI.register(data);
      await login({ username: data.username, password: data.password });
    } catch (err: any) {
      const detail =
        err.response?.data?.detail ||
        err.message ||
        'Failed to register. Please check your input and try again.';
      setError(detail);
      throw err;
    }
  };

  const registerAdmin = async (data: RegisterData) => {
    setError(null);
    try {
      await authAPI.registerAdmin(data);
      await login({ username: data.username, password: data.password });
    } catch (err: any) {
      const detail =
        err.response?.data?.detail ||
        err.message ||
        'Failed to register admin user.';
      setError(detail);
      throw err;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setUser(null);
    setError(null);
    window.location.href = '/login';
  };

  const value: AuthContextType = {
    user,
    loading,
    error,
    clearError: () => setError(null),
    login,
    register,
    registerAdmin,
    logout,
    isAuthenticated: !!user,
    isAdmin: user?.is_admin || false,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
