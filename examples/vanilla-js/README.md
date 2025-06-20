# Auth Gateway Vanilla JavaScript Example

This example demonstrates how to use the Auth Gateway SDK with vanilla JavaScript (without React).

## Features

- Google Sign-In integration
- User profile display
- Login/logout functionality
- Error handling
- Loading state management

## Prerequisites

- A Firebase project with Google Sign-In enabled
- The Auth Gateway backend service running
- The Auth Gateway frontend SDK built

## Setup

1. Update the Auth Gateway backend URL in `index.html`:

```javascript
const authBackendUrl = "http://localhost:8000";  // Replace with your Auth Gateway backend URL
```

**Note**: Firebase configuration is no longer needed in the client application. All Firebase configuration is now handled by the Auth Gateway backend service.

2. Build the Auth Gateway frontend SDK:

```bash
cd ../../javascript-sdk
npm install
npm run build
```

## Running the Example

You can run this example using any static file server. For example:

```bash
# Using Python's built-in HTTP server
python -m http.server

# Using Node.js http-server
npx http-server
```

Then open your browser and navigate to the example page (e.g., http://localhost:8000).

## How It Works

This example uses the `VanillaAuthClient` class from the Auth Gateway SDK to handle authentication:

1. **Initialization**:
   ```javascript
   const authClient = new VanillaAuthClient({
     authBackendUrl
   });
   ```

2. **Auth State Changes**:
   ```javascript
   authClient.onAuthStateChanged((user) => {
     // Update UI based on user state
   });
   ```

3. **Loading State**:
   ```javascript
   authClient.onLoadingStateChanged((isLoading) => {
     // Show/hide loading indicator
   });
   ```

4. **Error Handling**:
   ```javascript
   authClient.onError((error) => {
     // Display error message
   });
   ```

5. **Login**:
   ```javascript
   await authClient.login();
   ```

6. **Logout**:
   ```javascript
   await authClient.logout();
   ```

7. **Get Current User**:
   ```javascript
   const user = authClient.getCurrentUser();
   ```

## Key Differences from React Implementation

Unlike the React implementation which uses React Context and hooks, the vanilla JavaScript implementation:

1. Uses an event-based system for state changes
2. Provides methods for getting the current state
3. Requires manual DOM manipulation for UI updates
4. Does not depend on any React-specific features

This makes it suitable for use in any JavaScript application, not just React applications.
