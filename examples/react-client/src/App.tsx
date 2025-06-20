import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { AuthProvider } from 'auth-gateway-sdk';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import ProfilePage from './pages/ProfilePage';
import ProtectedRoute from './components/ProtectedRoute';

// Auth Gateway backend URL
const authBackendUrl = "http://localhost:8000";

function App() {
  return (
    <AuthProvider
      authBackendUrl={authBackendUrl}
    >
      <div className="container">
        <Navbar />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/auth-callback" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/profile" element={<ProfilePage />} />
          </Route>
        </Routes>
      </div>
    </AuthProvider>
  );
}

export default App;
