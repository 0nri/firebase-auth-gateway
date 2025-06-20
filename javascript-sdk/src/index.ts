// Export React components
export { AuthProvider } from './auth-context';

// Export React hooks
export { useAuth } from './use-auth';

// Export vanilla JavaScript client
export { VanillaAuthClient } from './vanilla-auth';

// Export types
export {
  UserData,
  AuthProviderProps,
  AuthContextValue,
  VanillaAuthClientConfig,
  AuthStateChangeCallback,
  AuthErrorCallback,
  AuthLoadingCallback,
} from './types';
