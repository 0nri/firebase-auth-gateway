import axios, { AxiosInstance } from 'axios';
import { ApiClientConfig, UserData, StorageKeys } from './types';

/**
 * API client for communicating with the Auth Gateway backend
 */
export class ApiClient {
  private client: AxiosInstance;
  
  /**
   * Creates a new API client
   * @param config API client configuration
   */
  constructor(config: ApiClientConfig) {
    this.client = axios.create({
      baseURL: config.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Add request interceptor to include the token in requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem(StorageKeys.TOKEN);
      
      if (token) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
      }
      
      return config;
    });
  }
  
  /**
   * Initiates the login process
   * @param redirectUri Optional redirect URI after authentication
   * @returns Authentication URL to redirect to
   */
  async login(redirectUri?: string): Promise<string> {
    try {
      const response = await this.client.post<{ url: string }>('/auth/login', {
        redirect_uri: redirectUri || window.location.origin
      });
      
      return response.data.url;
    } catch (error) {
      console.error('Login initiation failed:', error);
      throw error;
    }
  }
  
  /**
   * Handles the authentication callback
   * @param code Authorization code from the callback
   * @param state Optional state from the callback
   * @returns Token and user data
   */
  async handleCallback(code: string, state?: string): Promise<{ token: string, user: UserData }> {
    try {
      const response = await this.client.post<{ token: string, user: UserData }>('/auth/callback', {
        code,
        state
      });
      
      return response.data;
    } catch (error) {
      console.error('Authentication callback failed:', error);
      throw error;
    }
  }
  
  /**
   * Logs the user out
   */
  async logout(): Promise<void> {
    try {
      await this.client.post('/auth/logout');
    } catch (error) {
      console.error('Logout failed:', error);
      throw error;
    }
  }
  
  /**
   * Verifies a token with the Auth Gateway backend
   * @param token Authentication token
   * @returns User data if token is valid
   */
  async verifyToken(token: string): Promise<UserData> {
    try {
      const response = await this.client.post<UserData>('/verify-token', null, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      return response.data;
    } catch (error) {
      console.error('Token verification failed:', error);
      throw error;
    }
  }
  
  /**
   * Gets the current user data using the stored token
   * @returns User data if token is valid
   */
  async getCurrentUser(): Promise<UserData> {
    try {
      const response = await this.client.post<UserData>('/verify-token');
      return response.data;
    } catch (error) {
      console.error('Failed to get current user:', error);
      throw error;
    }
  }
}

/**
 * Creates a new API client
 * @param config API client configuration
 * @returns API client instance
 */
export const createApiClient = (config: ApiClientConfig): ApiClient => {
  return new ApiClient(config);
};
