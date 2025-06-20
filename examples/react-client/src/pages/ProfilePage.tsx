import React from 'react';
import { useAuth } from 'auth-gateway-sdk';

const ProfilePage: React.FC = () => {
  const { user } = useAuth();

  if (!user) {
    return null; // This should be handled by ProtectedRoute
  }

  return (
    <div>
      <h1>Profile</h1>
      <div className="card profile">
        {user.photo_url && (
          <img
            src={user.photo_url}
            alt={user.display_name || 'User'}
            className="profile-image"
          />
        )}
        <h2>{user.display_name || 'User'}</h2>
        <p>{user.email}</p>
        <p>User ID: {user.uid}</p>
      </div>
      <div className="card">
        <h3>Authentication Information</h3>
        <p>
          You are authenticated using Google Sign-In through the Auth Gateway.
          Your session is managed using a stateless JWT approach.
        </p>
      </div>
    </div>
  );
};

export default ProfilePage;
