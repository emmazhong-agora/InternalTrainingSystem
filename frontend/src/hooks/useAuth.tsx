import axios from "axios";
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

interface AuthUser {
  id: number;
  email: string;
  created_at: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("its_token"));
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState<boolean>(!!token);

  const fetchProfile = useCallback(async (accessToken: string) => {
    try {
      const response = await axios.get<AuthUser>("/api/v1/auth/me", {
        headers: { Authorization: `Bearer ${accessToken}` }
      });
      setUser(response.data);
    } catch (error) {
      console.error("Failed to load user profile", error);
      setUser(null);
      setToken(null);
      localStorage.removeItem("its_token");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (token) {
      fetchProfile(token);
    } else {
      setLoading(false);
    }
  }, [token, fetchProfile]);

  const login = useCallback(async (email: string, password: string) => {
    const response = await axios.post<{ access_token: string }>("/api/v1/auth/login/json", {
      email,
      password
    });
    const accessToken = response.data.access_token;
    localStorage.setItem("its_token", accessToken);
    setToken(accessToken);
    await fetchProfile(accessToken);
  }, [fetchProfile]);

  const logout = useCallback(() => {
    localStorage.removeItem("its_token");
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(() => ({ user, token, loading, login, logout }), [user, token, loading, login, logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
