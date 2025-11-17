// Example usage of authProvider in Electron or Next.js
import authProvider from './authProvider';

async function runAuthFlow() {
  try {
    // Login
    const session = await authProvider.login('yourUsername', 'yourPassword');
    console.log('Logged in:', session.user);
    console.log('JWT:', session.jwt);
    console.log('Access tier:', authProvider.getAccessTier());

    // Check authentication
    if (authProvider.isAuthenticated()) {
      // Make an authenticated GraphQL query
      const query = `query Me { me { id username email tier roles } }`;
      const result = await authProvider.graphql(query);
      console.log('User info:', result);
    }

    // Logout
    authProvider.logout();
    console.log('Logged out.');
  } catch (err) {
    console.error('Auth error:', err);
  }
}

runAuthFlow();
