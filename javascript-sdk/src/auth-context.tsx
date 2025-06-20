import React, { createContext, useEffect, useState } from 'react';
import { 
  AuthContextValue, 
  AuthProviderProps, 
  UserData, 
  StorageKeys 
} from './types';
import { ApiClient, createApiClient } from './api-client';

// Create the auth context with a default value
export const AuthContext = createContext<AuthContextValue>({
  user: null,
  isLoading: true,
  error: null,
  login: async () => {},
  logout: async () => {},
});

/**
 * Auth Provider component that wraps the application and provides authentication state
 */
export const AuthProvider: React.FC<AuthProviderProps> = ({
  authBackendUrl,
  loginRedirectPath = '/',
  unauthorizedRedirectPath = '/login',
  LoadingComponent,
  children,
}) => {
  // State
  const [user, setUser] = useState<UserData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [apiClient, setApiClient] = useState<ApiClient | null>(null);

  // Initialize API client
  useEffect(() => {
    try {
      // Initialize API client
      const client = createApiClient({ baseUrl: authBackendUrl });
      setApiClient(client);
    } catch (err) {
      console.error('Failed to initialize:', err);
      setError('Failed to initialize authentication');
      setIsLoading(false);
    }
  }, [authBackendUrl]);

  // Check for authentication callback in URL
  useEffect(() => {
    if (!apiClient) return;

    const url = new URL(window.location.href);
    const code = url.searchParams.get('code');
    const state = url.searchParams.get('state');
    const token = url.searchParams.get('token');

    if (token) {
      // Handle direct token from our custom callback
      setIsLoading(true);
      setError(null);

      try {
        // Store token
        localStorage.setItem(StorageKeys.TOKEN, token);
        
        // Get user data
        const getUserData = async () => {
          try {
            const userData = await apiClient.getCurrentUser();
            setUser(userData);
          } catch (err) {
            console.error('Failed to get user data:', err);
            setError('Authentication failed. Please try again.');
            localStorage.removeItem(StorageKeys.TOKEN);
            
            // Redirect to unauthorized redirect path
            window.history.replaceState({}, document.title, unauthorizedRedirectPath);
          } finally {
            setIsLoading(false);
          }
        };
        
        getUserData();
        
        // Remove token from URL
        window.history.replaceState({}, document.title, loginRedirectPath);
      } catch (err) {
        console.error('Authentication failed:', err);
        setError('Authentication failed. Please try again.');
        localStorage.removeItem(StorageKeys.TOKEN);
        setIsLoading(false);
        
        // Redirect to unauthorized redirect path
        window.history.replaceState({}, document.title, unauthorizedRedirectPath);
      }
    } else if (code) {
      // Handle authentication callback (legacy flow)
      const handleCallback = async () => {
        setIsLoading(true);
        setError(null);

        try {
          // Exchange code for token
          const { token, user } = await apiClient.handleCallback(code, state || undefined);
          
          // Store token and user data
          localStorage.setItem(StorageKeys.TOKEN, token);
          setUser(user);
          
          // Redirect to login redirect path
          window.history.replaceState({}, document.title, loginRedirectPath);
        } catch (err) {
          console.error('Authentication callback failed:', err);
          setError('Authentication failed. Please try again.');
          localStorage.removeItem(StorageKeys.TOKEN);
          
          // Redirect to unauthorized redirect path
          window.history.replaceState({}, document.title, unauthorizedRedirectPath);
        } finally {
          setIsLoading(false);
        }
      };

      handleCallback();
    } else {
      // Check for existing token
      const checkAuth = async () => {
        const token = localStorage.getItem(StorageKeys.TOKEN);
        
        if (!token) {
          setIsLoading(false);
          return;
        }

        try {
          const userData = await apiClient.getCurrentUser();
          setUser(userData);
        } catch (err) {
          console.error('Authentication failed:', err);
          localStorage.removeItem(StorageKeys.TOKEN);
          setError('Authentication failed. Please log in again.');
        } finally {
          setIsLoading(false);
        }
      };

      checkAuth();
    }
  }, [apiClient, loginRedirectPath, unauthorizedRedirectPath]);

  /**
   * Initiates the login process with Google Sign-In
   */
  const login = async (): Promise<void> => {
    if (!apiClient) {
      setError('Authentication not initialized');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Get authentication URL from backend
      const authUrl = await apiClient.login(window.location.origin);
      
      // Redirect to authentication URL
      window.location.href = authUrl;
    } catch (err) {
      console.error('Login failed:', err);
      setError('Login failed. Please try again.');
      setIsLoading(false);
    }
  };

  /**
   * Logs the user out
   */
  const logout = async (): Promise<void> => {
    if (!apiClient) {
      setError('Authentication not initialized');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Call logout endpoint
      await apiClient.logout();

      // Clear local storage and state
      localStorage.removeItem(StorageKeys.TOKEN);
      setUser(null);
    } catch (err) {
      console.error('Logout failed:', err);
      setError('Logout failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Render loading component if still loading
  if (isLoading && LoadingComponent) {
    return <LoadingComponent />;
  }

  // Provide auth context to children
  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        error,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
