import axios, { AxiosInstance } from "axios";
import { useMemo } from "react";
import { useAuth } from "./useAuth";

export const useApi = (): AxiosInstance => {
  const { token } = useAuth();

  return useMemo(() => {
    const instance = axios.create({
      baseURL: "/api/v1"
    });

    instance.interceptors.request.use((config) => {
      if (token) {
        config.headers = config.headers ?? {};
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    return instance;
  }, [token]);
};
