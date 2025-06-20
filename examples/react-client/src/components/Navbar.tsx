import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from 'auth-gateway-sdk';

const Navbar: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <nav className="nav">
      <div>
        <Link to="/">Auth Gateway Example</Link>
      </div>
      <div className="nav-links">
        <Link to="/">Home</Link>
        {user ? (
          <>
            <Link to="/profile">Profile</Link>
            <button onClick={logout}>Logout</button>
          </>
        ) : (
          <Link to="/login">Login</Link>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
