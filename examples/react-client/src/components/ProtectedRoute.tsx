import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from 'auth-gateway-sdk';

const ProtectedRoute: React.FC = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;
