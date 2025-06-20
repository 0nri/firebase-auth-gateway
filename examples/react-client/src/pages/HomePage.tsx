import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from 'auth-gateway-sdk';

const HomePage: React.FC = () => {
  const { user } = useAuth();

  return (
    <div>
      <h1>Auth Gateway Example</h1>
      <div className="card">
        <p>
          This is an example application demonstrating how to use the Auth Gateway
          for authentication with Google Sign-In.
        </p>
        {user ? (
          <div>
            <p>You are logged in as {user.display_name || user.email}.</p>
            <Link to="/profile">View Profile</Link>
          </div>
        ) : (
          <div>
            <p>You are not logged in.</p>
            <Link to="/login">Login</Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default HomePage;
