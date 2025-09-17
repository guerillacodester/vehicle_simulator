import { ApolloClient, InMemoryCache, createHttpLink } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';

// Create HTTP link to Strapi GraphQL endpoint
const httpLink = createHttpLink({
  uri: process.env.NEXT_PUBLIC_STRAPI_URL + '/graphql' || 'http://localhost:1337/graphql',
});

// Auth link (if needed in the future)
const authLink = setContext((_, { headers }) => {
  // Get token from localStorage in the future
  // const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  
  return {
    headers: {
      ...headers,
      // authorization: token ? `Bearer ${token}` : "",
    }
  };
});

// Create Apollo Client
export const apolloClient = new ApolloClient({
  link: authLink.concat(httpLink),
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: {
      errorPolicy: 'all',
    },
    query: {
      errorPolicy: 'all',
    },
  },
});