# Auth Gateway Frontend SDK

A SDK for seamless authentication with Auth Gateway, supporting both React and vanilla JavaScript.

## Features

- Google Sign-In integration via Auth Gateway backend
- Centralized Firebase configuration in the backend
- JWT token management
- React Context API for React applications
- Event-based API for vanilla JavaScript applications
- TypeScript support
- Minimal code integration

## Installation

```bash
# Install from git repository (latest stable)
npm install git+https://github.com/0nri/firebase-auth-gateway.git#subdirectory=javascript-sdk

# Install specific version using git tag
npm install git+https://github.com/0nri/firebase-auth-gateway.git@v1.0.0#subdirectory=javascript-sdk

# Using yarn
yarn add git+https://github.com/0nri/firebase-auth-gateway.git#subdirectory=javascript-sdk
```

## Quick Start

### 1. Wrap your application with AuthProvider

```jsx
// App.jsx or App.tsx
import React from 'react';
import { AuthProvider } from 'auth-gateway-sdk';

// Auth Gateway backend URL
const authBackendUrl = "https://your-auth-gateway-backend.com";

function App() {
  return (
    <AuthProvider
      authBackendUrl={authBackendUrl}
    >
      <YourApp />
    </AuthProvider>
  );
}

export default App;
```

### 2. Use the authentication hook in your components

```jsx
// LoginButton.jsx or LoginButton.tsx
import React from 'react';
import { useAuth } from 'auth-gateway-sdk';

function LoginButton() {
  const { user, isLoading, error, login, logout } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (user) {
    return (
      <div>
        <p>Welcome, {user.display_name || user.email}!</p>
        <button onClick={logout}>Sign Out</button>
      </div>
    );
  }

  return (
    <div>
      <button onClick={login}>Sign In with Google</button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
}

export default LoginButton;
```

## API Reference

### AuthProvider

The `AuthProvider` component wraps your application and provides authentication state and methods.

#### Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| authBackendUrl | string | Yes | URL of the Auth Gateway backend service |
| loginRedirectPath | string | No | Path to redirect to after login (default: "/") |
| unauthorizedRedirectPath | string | No | Path to redirect to if unauthorized (default: "/login") |
| LoadingComponent | React.ComponentType | No | Custom loading component to display during authentication |
| children | React.ReactNode | Yes | Child components |

### useAuth

The `useAuth` hook provides access to authentication state and methods.

#### Return Value

| Property | Type | Description |
|----------|------|-------------|
| user | UserData \| null | Current authenticated user or null if not authenticated |
| isLoading | boolean | Whether authentication is in progress |
| error | string \| null | Error message if authentication failed |
| login | () => Promise<void> | Function to initiate the login process |
| logout | () => Promise<void> | Function to log the user out |

### UserData

The `UserData` interface represents the authenticated user.

| Property | Type | Description |
|----------|------|-------------|
| uid | string | User ID |
| email | string | User email |
| display_name | string \| undefined | User display name |
| photo_url | string \| undefined | User profile photo URL |

## Advanced Configuration

### Custom Loading Component

```jsx
import React from 'react';
import { AuthProvider } from 'auth-gateway-sdk';
import Spinner from './Spinner'; // Your custom loading component

function App() {
  return (
    <AuthProvider
      authBackendUrl={authBackendUrl}
      LoadingComponent={Spinner}
    >
      <YourApp />
    </AuthProvider>
  );
}
```

### Protected Routes (with React Router)

```jsx
import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from 'auth-gateway-sdk';

function ProtectedRoute() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

// In your router configuration
// <Route element={<ProtectedRoute />}>
//   <Route path="/dashboard" element={<Dashboard />} />
//   <Route path="/settings" element={<Settings />} />
// </Route>
```

## Error Handling

The SDK provides error handling through the `error` property returned by the `useAuth` hook. You can display this error to the user or handle it programmatically.

```jsx
const { error } = useAuth();

if (error) {
  // Handle the error
  console.error('Authentication error:', error);
  // Display error message to the user
  return <div className="error-message">{error}</div>;
}
```

## TypeScript Support

The SDK is written in TypeScript and provides type definitions for all components and hooks.

```tsx
import { useAuth, UserData } from 'auth-gateway-sdk';

function Profile() {
  const { user } = useAuth();
  
  const displayUserInfo = (userData: UserData) => {
    return (
      <div>
        <h2>{userData.display_name}</h2>
        <p>{userData.email}</p>
        {userData.photo_url && <img src={userData.photo_url} alt="Profile" />}
      </div>
    );
  };
  
  return (
    <div>
      {user ? displayUserInfo(user) : <p>Not logged in</p>}
    </div>
  );
}
```

## Vanilla JavaScript Usage

The SDK also provides a vanilla JavaScript client that doesn't depend on React.

### Initialization

```javascript
import { VanillaAuthClient } from 'auth-gateway-sdk';

// Initialize the client
const authClient = new VanillaAuthClient({
  authBackendUrl: "https://your-auth-gateway-backend.com"
});
```

### Authentication State Changes

```javascript
// Listen for authentication state changes
const unsubscribe = authClient.onAuthStateChanged((user) => {
  if (user) {
    console.log('User is logged in:', user);
    // Update UI for authenticated user
  } else {
    console.log('User is logged out');
    // Update UI for unauthenticated user
  }
});

// Later, when you want to stop listening
unsubscribe();
```

### Loading State

```javascript
// Listen for loading state changes
authClient.onLoadingStateChanged((isLoading) => {
  if (isLoading) {
    // Show loading indicator
  } else {
    // Hide loading indicator
  }
});
```

### Error Handling

```javascript
// Listen for errors
authClient.onError((error) => {
  console.error('Auth error:', error);
  // Display error message
});
```

### Login and Logout

```javascript
// Login
document.getElementById('loginButton').addEventListener('click', async () => {
  try {
    const user = await authClient.login();
    console.log('Login successful:', user);
  } catch (error) {
    console.error('Login failed:', error);
  }
});

// Logout
document.getElementById('logoutButton').addEventListener('click', async () => {
  try {
    await authClient.logout();
    console.log('Logout successful');
  } catch (error) {
    console.error('Logout failed:', error);
  }
});
```

### Getting Current State

```javascript
// Get current user
const user = authClient.getCurrentUser();

// Check if authentication is loading
const isLoading = authClient.isAuthLoading();

// Get current error
const error = authClient.getError();
```

### Cleanup

```javascript
// Clean up resources when done
authClient.destroy();
```

For a complete example, see the [vanilla JavaScript example](../examples/vanilla-js/index.html).
