import React, { createContext, useContext, useEffect, useState } from 'react';

interface User {
  id: string;
  email: string;
  user_metadata: any;
}

interface Session {
  access_token: string;
  refresh_token: string;
}

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  userRole: string | null;
  signUp: (email: string, password: string, fullName: string) => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [userRole, setUserRole] = useState<string | null>(null);

  const fetchCurrentUser = async (token: string) => {
    try {
      const res = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data.user);
        setUserRole(data.role);
        setSession({ access_token: token, refresh_token: '' });
      } else {
        throw new Error("Invalid session");
      }
    } catch {
      setUser(null);
      setSession(null);
      setUserRole(null);
      localStorage.removeItem('medai_token');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Check if coming back from Google OAuth
    if (window.location.hash) {
      const hashParams = new URLSearchParams(window.location.hash.substring(1));
      const accessToken = hashParams.get('access_token');
      if (accessToken) {
        localStorage.setItem('medai_token', accessToken);
        window.history.replaceState(null, '', window.location.pathname);
      }
    }

    const token = localStorage.getItem('medai_token');
    if (token) {
      fetchCurrentUser(token);
    } else {
      setLoading(false);
    }
  }, []);

  const handleAuthResponse = async (res: Response) => {
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Authentication failed");
    }
    if (data.session && data.session.access_token) {
      localStorage.setItem('medai_token', data.session.access_token);
      await fetchCurrentUser(data.session.access_token);
    }
  };

  const signUp = async (email: string, password: string, fullName: string) => {
    const res = await fetch('/api/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    // the backend will handle full_name natively in future, currently ignores it
    await handleAuthResponse(res);
  };

  const signIn = async (email: string, password: string) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    await handleAuthResponse(res);
  };

  const signInWithGoogle = async () => {
    const res = await fetch('/api/auth/google');
    if (res.ok) {
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } else {
      throw new Error("Could not initialize Google log in from backend.");
    }
  };

  const signOut = async () => {
    const token = localStorage.getItem('medai_token');
    if (token) {
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      }).catch(() => {});
    }
    localStorage.removeItem('medai_token');
    setUser(null);
    setSession(null);
    setUserRole(null);
  };

  const resetPassword = async (email: string) => {
    // Implement via backend soon
    alert("Reset password requires further backend implementation.");
  };

  return (
    <AuthContext.Provider value={{ user, session, loading, userRole, signUp, signIn, signInWithGoogle, signOut, resetPassword }}>
      {children}
    </AuthContext.Provider>
  );
};
