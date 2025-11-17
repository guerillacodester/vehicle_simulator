// Reusable Auth/Data Provider for Strapi GraphQL
// Can be used in Electron, Next.js, or any TS/JS app

export interface AuthSession {
  jwt: string;
  user: {
    id: string;
    username: string;
    email: string;
    tier?: string;
    roles?: string[];
    [key: string]: any;
  };
}

class AuthProvider {
  private jwt: string | null = null;
  private user: AuthSession['user'] | null = null;

  async login(username: string, password: string, graphqlUrl = 'http://localhost:1337/graphql'): Promise<AuthSession> {
    const query = `mutation Login($identifier: String!, $password: String!) { login(input: { identifier: $identifier, password: $password }) { jwt user { id username email tier roles } } }`;
    const variables = { identifier: username, password };
    const resp = await fetch(graphqlUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, variables })
    });
    const result = await resp.json();
    const login = result?.data?.login;
    if (!login?.jwt || !login?.user) throw new Error('Invalid credentials');
    this.jwt = login.jwt;
    this.user = login.user;
    return { jwt: login.jwt, user: login.user };
  }

  logout() {
    this.jwt = null;
    this.user = null;
  }

  getSession(): AuthSession | null {
    if (this.jwt && this.user) return { jwt: this.jwt, user: this.user };
    return null;
  }

  isAuthenticated(): boolean {
    return !!this.jwt;
  }

  getAccessTier(): string | string[] | null {
    return this.user?.tier || this.user?.roles || null;
  }

  async graphql<T = any>(query: string, variables?: Record<string, any>, graphqlUrl = 'http://localhost:1337/graphql'): Promise<T> {
    if (!this.jwt) throw new Error('Not authenticated');
    const resp = await fetch(graphqlUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.jwt}`
      },
      body: JSON.stringify({ query, variables })
    });
    return await resp.json();
  }
}

const authProvider = new AuthProvider();
export default authProvider;
