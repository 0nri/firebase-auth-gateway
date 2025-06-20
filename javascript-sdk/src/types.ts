import React from 'react';


/**
 * User data returned from the Auth Gateway
 */
export interface UserData {
  uid: string;
  email: string;
  display_name?: string;
  photo_url?: string;
}

/**
 * Auth Provider props
 */
export interface AuthProviderProps {
  /**
   * Base URL of the Auth Gateway backend service
   */
  authBackendUrl: string;
  
  /**
   * Path to redirect to after login
   * @default "/"
   */
  loginRedirectPath?: string;
  
  /**
   * Path to redirect to if unauthorized
   * @default "/login"
   */
  unauthorizedRedirectPath?: string;
  
  /**
   * Custom loading component to display during authentication
   */
  LoadingComponent?: React.ComponentType;
  
  /**
   * Children components
   */
  children: React.ReactNode;
}

/**
 * Auth context value
 */
export interface AuthContextValue {
  /**
   * Current authenticated user or null if not authenticated
   */
  user: UserData | null;
  
  /**
   * Whether authentication is in progress
   */
  isLoading: boolean;
  
  /**
   * Error message if authentication failed
   */
  error: string | null;
  
  /**
   * Initiates the login process
   */
  login: () => Promise<void>;
  
  /**
   * Logs the user out
   */
  logout: () => Promise<void>;
}

/**
 * API client configuration
 */
export interface ApiClientConfig {
  /**
   * Base URL of the Auth Gateway backend service
   */
  baseUrl: string;
}

/**
 * Storage keys for localStorage
 */
export enum StorageKeys {
  TOKEN = 'auth_gateway_token',
}

/**
 * Vanilla Auth Client configuration
 */
export interface VanillaAuthClientConfig {
  /**
   * Base URL of the Auth Gateway backend service
   */
  authBackendUrl: string;
  
  /**
   * Redirect URI after authentication
   * @default current location
   */
  redirectUri?: string;
}

/**
 * Auth state change callback
 */
export type AuthStateChangeCallback = (user: UserData | null) => void;

/**
 * Auth error callback
 */
export type AuthErrorCallback = (error: string) => void;

/**
 * Auth loading state change callback
 */
export type AuthLoadingCallback = (isLoading: boolean) => void;
