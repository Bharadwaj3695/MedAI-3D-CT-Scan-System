export interface User {
  id: string;
  email: string;
  user_metadata: any;
}

export interface Session {
  access_token: string;
  refresh_token: string;
}

export interface AuthResponse {
  user?: User;
  session?: Session;
  role?: string;
  detail?: string;
  url?: string;
}

export const AuthService = {
  /**
   * Register a new user with email and password
   */
  async signUp(email: string, password: string): Promise<AuthResponse> {
    const res = await fetch('/api/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Registration failed');
    }
    return data;
  },

  /**
   * Authenticate a user with email and password
   */
  async signIn(email: string, password: string): Promise<AuthResponse> {
    const formData = new URLSearchParams();

    formData.append("username", email);
    formData.append("password", password);

    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData,
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Authentication failed");
    }

    return data;
  },

  /**
   * Get the Google OAuth login URL
   */
  async signInWithGoogle(): Promise<{ url: string }> {
    const res = await fetch('/api/auth/google');
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Could not initialize Google log in from backend.');
    }
    return data;
  },

  /**
   * Log out the current user
   */
  async signOut(token: string): Promise<void> {
    const res = await fetch('/api/auth/logout', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || 'Logout failed');
    }
  },

  /**
   * Fetch the profile and role of the currently logged-in user
   */
  async getCurrentUser(token: string): Promise<{ user: User; role: string }> {
    const res = await fetch('/api/auth/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to fetch current user');
    }
    return data;
  }
};
