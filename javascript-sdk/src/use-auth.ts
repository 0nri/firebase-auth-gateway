import { useContext } from 'react';
import { AuthContext } from './auth-context';
import { AuthContextValue } from './types';

/**
 * Hook to access authentication state and methods
 * @returns Authentication context value
 */
export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};
