import { useState, useEffect, useCallback } from 'react';
import { fetchCurrentUser, loginUser, registerUser, logoutUser, getAuthToken } from '../api';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const checkAuth = useCallback(async () => {
    const token = getAuthToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const profile = await fetchCurrentUser();
      setUser(profile);
    } catch (err) {
      console.warn('Auth validation failed:', err);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async (email, password) => {
    setError(null);
    try {
      const data = await loginUser({ email, password });
      setUser(data.user);
      return data.user;
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Login failed';
      setError(msg);
      throw new Error(msg);
    }
  };

  const register = async (email, password, displayName) => {
    setError(null);
    try {
      const data = await registerUser({ email, password, display_name: displayName });
      setUser(data.user);
      return data.user;
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Registration failed';
      setError(msg);
      throw new Error(msg);
    }
  };

  const logout = () => {
    logoutUser();
    setUser(null);
    setError(null);
  };

  return {
    user,
    isAuthenticated: !!user,
    loading,
    error,
    login,
    register,
    logout,
    refreshUser: checkAuth,
  };
}
