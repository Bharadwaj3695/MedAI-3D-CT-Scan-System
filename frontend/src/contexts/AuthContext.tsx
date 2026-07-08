import React, { createContext, useContext, useEffect, useState } from "react";
import { AuthService, User, Session } from "../services/auth.service";

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

  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return ctx;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [userRole, setUserRole] = useState<string | null>(null);

  /**
   * Fetch authenticated user details
   */
  const fetchCurrentUser = async (token: string) => {
    try {
      const data = await AuthService.getCurrentUser(token);

      setUser(data.user);
      setUserRole(data.role);

      setSession({
        access_token: token,
        refresh_token: "",
      });
    } catch (err) {
      console.error("Failed to fetch current user:", err);

      localStorage.removeItem("medai_token");

      setUser(null);
      setSession(null);
      setUserRole(null);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Restore session on page refresh
   */
  useEffect(() => {
    // Handle Google OAuth redirect
    if (window.location.hash) {
      const hashParams = new URLSearchParams(window.location.hash.substring(1));

      const accessToken = hashParams.get("access_token");

      if (accessToken) {
        localStorage.setItem("medai_token", accessToken);

        window.history.replaceState(
          null,
          "",
          window.location.pathname
        );
      }
    }

    const token = localStorage.getItem("medai_token");

    if (token) {
      fetchCurrentUser(token);
    } else {
      setLoading(false);
    }
  }, []);

  /**
   * Process login response
   */
  const handleAuthResponse = async (data: any) => {
    if (data.access_token) {
      localStorage.setItem("medai_token", data.access_token);

      await fetchCurrentUser(data.access_token);
    } else {
      throw new Error("Authentication token was not returned.");
    }
  };

  /**
   * Register user
   */
  const signUp = async (
    email: string,
    password: string,
    fullName: string
  ) => {
    await AuthService.signUp(email, password);

    // Backend currently returns only user info.
    // User must login after successful registration.
  };

  /**
   * Login user
   */
  ync (email: string, password: string) => {
    const const signIn = asdata = await AuthService.signIn(email, password);

    await handleAuthResponse(data);
  };

  /**
   * Google OAuth
   */
  const signInWithGoogle = async () => {
    const data = await AuthService.signInWithGoogle();

    if (data.url) {
      window.location.href = data.url;
    }
  };

  /**
   * Logout
   */
  const signOut = async () => {
    const token = localStorage.getItem("medai_token");

    if (token) {
      try {
        await AuthService.signOut(token);
      } catch (err) {
        console.warn("Logout request failed:", err);
      }
    }

    localStorage.removeItem("medai_token");

    setUser(null);
    setSession(null);
    setUserRole(null);
  };

  /**
   * Reset Password
   */
  const resetPassword = async (email: string) => {
    alert("Reset password will be implemented in the backend.");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        userRole,
        signUp,
        signIn,
        signInWithGoogle,
        signOut,
        resetPassword,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};