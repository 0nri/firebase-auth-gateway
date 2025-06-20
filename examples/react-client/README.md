# Auth Gateway Example Client

This is an example React application demonstrating how to use the Auth Gateway for authentication with Google Sign-In.

## Features

- Google Sign-In integration
- Protected routes
- User profile display
- Minimal code integration

## Prerequisites

- Node.js 14+
- npm or yarn
- Auth Gateway backend service running

## Setup

1. Install dependencies:

```bash
npm install
# or
yarn install
```

2. Configure Auth Gateway backend URL:

Edit `src/App.tsx` and update the Auth Gateway backend URL:

```jsx
// Auth Gateway backend URL
const authBackendUrl = "http://localhost:8000";  // Replace with your Auth Gateway backend URL
```

**Note**: Firebase configuration is no longer needed in the client application. All Firebase configuration is now handled by the Auth Gateway backend service.

## Running the Application

```bash
npm run dev
# or
yarn dev
```

The application will be available at http://localhost:5173

## Pages

- **Home**: Landing page with basic information
- **Login**: Sign in with Google
- **Profile**: Protected page showing user information

## Components

- **Navbar**: Navigation bar with login/logout functionality
- **ProtectedRoute**: Route wrapper that redirects to login if not authenticated

## Authentication Flow

1. User clicks "Login" button
2. Browser redirects to Auth Gateway backend login endpoint
3. Auth Gateway redirects to Google Sign-In
4. User authenticates with Google
5. Google redirects back to Auth Gateway with authorization code
6. Auth Gateway exchanges code for Firebase token and validates user
7. Auth Gateway redirects back to client application with verified token
8. Client application stores token and updates authentication state

## Implementation Details

The application uses the Auth Gateway SDK to handle authentication:

```jsx
import { AuthProvider, useAuth } from 'auth-gateway-sdk';

// Wrap your application with AuthProvider
<AuthProvider
  authBackendUrl={authBackendUrl}
>
  <App />
</AuthProvider>

// Use the useAuth hook in your components
const { user, isLoading, error, login, logout } = useAuth();
