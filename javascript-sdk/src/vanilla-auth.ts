import { 
  VanillaAuthClientConfig, 
  UserData, 
  StorageKeys,
  AuthStateChangeCallback,
  AuthErrorCallback,
  AuthLoadingCallback
} from './types';
import { ApiClient, createApiClient } from './api-client';
import { EventEmitter } from './events';

/**
 * Auth Gateway client for vanilla JavaScript
 */
export class VanillaAuthClient {
  private apiClient: ApiClient | null = null;
  private user: UserData | null = null;
  private isLoading: boolean = true;
  private error: string | null = null;
  private events: EventEmitter = new EventEmitter();

  /**
   * Creates a new VanillaAuthClient
   * @param config Client configuration
   */
  constructor(config: VanillaAuthClientConfig) {
    this.initialize(config);
  }

  /**
   * Initialize the client
   * @param config Client configuration
   */
  private async initialize(config: VanillaAuthClientConfig): Promise<void> {
    try {
      // Initialize API client
      this.apiClient = createApiClient({ baseUrl: config.authBackendUrl });

      // Check for authentication callback in URL
      const url = new URL(window.location.href);
      const code = url.searchParams.get('code');
      const state = url.searchParams.get('state');
      const token = url.searchParams.get('token');

      if (token) {
        // Handle direct token from our custom callback
        await this.handleDirectToken(token);
      } else if (code) {
        // Handle authentication callback (legacy flow)
        await this.handleCallback(code, state || undefined);
      } else {
        // Check for existing token
        await this.checkExistingAuth();
      }
    } catch (err) {
      console.error('Failed to initialize:', err);
      this.setError('Failed to initialize authentication');
      this.setLoading(false);
    }
  }

  /**
   * Handle direct token from custom callback
   * @param token ID token
   */
  private async handleDirectToken(token: string): Promise<void> {
    if (!this.apiClient) {
      this.setLoading(false);
      return;
    }

    this.setLoading(true);
    this.setError(null);

    try {
      // Store token
      localStorage.setItem(StorageKeys.TOKEN, token);
      
      // Get user data
      const userData = await this.apiClient.getCurrentUser();
      this.setUser(userData);
      
      // Remove token from URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } catch (err) {
      console.error('Authentication failed:', err);
      this.setError('Authentication failed. Please try again.');
      localStorage.removeItem(StorageKeys.TOKEN);
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Handle authentication callback
   * @param code Authorization code
   * @param state Optional state
   */
  private async handleCallback(code: string, state?: string): Promise<void> {
    if (!this.apiClient) {
      this.setLoading(false);
      return;
    }

    this.setLoading(true);
    this.setError(null);

    try {
      // Exchange code for token
      const { token, user } = await this.apiClient.handleCallback(code, state);
      
      // Store token and user data
      localStorage.setItem(StorageKeys.TOKEN, token);
      this.setUser(user);
      
      // Remove code and state from URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } catch (err) {
      console.error('Authentication callback failed:', err);
      this.setError('Authentication failed. Please try again.');
      localStorage.removeItem(StorageKeys.TOKEN);
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Check for existing authentication
   */
  private async checkExistingAuth(): Promise<void> {
    if (!this.apiClient) {
      this.setLoading(false);
      return;
    }

    const token = localStorage.getItem(StorageKeys.TOKEN);
    
    if (!token) {
      this.setLoading(false);
      return;
    }

    try {
      const userData = await this.apiClient.getCurrentUser();
      this.setUser(userData);
    } catch (err) {
      console.error('Authentication failed:', err);
      localStorage.removeItem(StorageKeys.TOKEN);
      this.setError('Authentication failed. Please log in again.');
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Set the current user
   * @param user User data
   */
  private setUser(user: UserData | null): void {
    this.user = user;
    this.events.emit('authStateChanged', user);
  }

  /**
   * Set the loading state
   * @param isLoading Loading state
   */
  private setLoading(isLoading: boolean): void {
    this.isLoading = isLoading;
    this.events.emit('loadingStateChanged', isLoading);
  }

  /**
   * Set the error message
   * @param error Error message
   */
  private setError(error: string | null): void {
    this.error = error;
    if (error) {
      this.events.emit('error', error);
    }
  }

  /**
   * Register an auth state change listener
   * @param callback Callback function
   * @returns Unsubscribe function
   */
  onAuthStateChanged(callback: AuthStateChangeCallback): () => void {
    // Immediately call with current state
    callback(this.user);
    // Register for future changes
    return this.events.on('authStateChanged', callback);
  }

  /**
   * Register an error listener
   * @param callback Callback function
   * @returns Unsubscribe function
   */
  onError(callback: AuthErrorCallback): () => void {
    return this.events.on('error', callback);
  }

  /**
   * Register a loading state change listener
   * @param callback Callback function
   * @returns Unsubscribe function
   */
  onLoadingStateChanged(callback: AuthLoadingCallback): () => void {
    // Immediately call with current state
    callback(this.isLoading);
    // Register for future changes
    return this.events.on('loadingStateChanged', callback);
  }

  /**
   * Get the current user
   * @returns Current user or null if not authenticated
   */
  getCurrentUser(): UserData | null {
    return this.user;
  }

  /**
   * Get the current loading state
   * @returns Loading state
   */
  isAuthLoading(): boolean {
    return this.isLoading;
  }

  /**
   * Get the current error message
   * @returns Error message or null if no error
   */
  getError(): string | null {
    return this.error;
  }

  /**
   * Initiates the login process with Google Sign-In
   * @returns Promise that resolves when login is complete
   */
  async login(): Promise<void> {
    if (!this.apiClient) {
      this.setError('Authentication not initialized');
      return;
    }

    this.setLoading(true);
    this.setError(null);

    try {
      // Get authentication URL from backend
      const redirectUri = this.getRedirectUri();
      const authUrl = await this.apiClient.login(redirectUri);
      
      // Redirect to authentication URL
      window.location.href = authUrl;
    } catch (err) {
      console.error('Login failed:', err);
      this.setError('Login failed. Please try again.');
      this.setLoading(false);
    }
  }

  /**
   * Get the redirect URI for authentication
   * @returns Redirect URI
   */
  private getRedirectUri(): string {
    return window.location.origin + window.location.pathname;
  }

  /**
   * Logs the user out
   * @returns Promise that resolves when logout is complete
   */
  async logout(): Promise<void> {
    if (!this.apiClient) {
      this.setError('Authentication not initialized');
      return;
    }

    this.setLoading(true);
    this.setError(null);

    try {
      // Call logout endpoint
      await this.apiClient.logout();

      // Clear local storage and state
      localStorage.removeItem(StorageKeys.TOKEN);
      this.setUser(null);
    } catch (err) {
      console.error('Logout failed:', err);
      this.setError('Logout failed. Please try again.');
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Destroy the client and clean up resources
   */
  destroy(): void {
    this.events.clear();
  }
}
