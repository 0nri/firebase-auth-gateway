import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from 'auth-gateway-sdk';

const LoginPage: React.FC = () => {
  const { user, isLoading, error, login } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (user) {
    return <Navigate to="/profile" />;
  }

  return (
    <div>
      <h1>Login</h1>
      <div className="card">
        <p>Sign in with your Google account to access the application.</p>
        <button onClick={login}>Sign In with Google</button>
        {error && <p className="error">{error}</p>}
      </div>
    </div>
  );
};

export default LoginPage;
