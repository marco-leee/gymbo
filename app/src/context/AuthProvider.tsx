"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { AuthState, UserRole } from "@/types/auth";
import { tokenService } from "@/services/auth";
import { signIn, signOut, useSession } from "next-auth/react";
import { notifications } from "@mantine/notifications";
import { gateways } from "@/config/auth";
import { AuthService } from "@/services/interfaces";
import { GatewayService } from "@/services/shared";

interface AuthContextType extends AuthState {
  login: (gateway: UserRole) => void;
  logout: () => void;
  refreshAuth: () => Promise<void>;
  getDataGateway: (gateway: UserRole) => GatewayService;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const authFreeRoutes = pathname.match(/(\/|login|api)/g) ? true : false;

  const { data: session, status } = useSession({
    required: !authFreeRoutes,
    onUnauthenticated: () => {
      if (authFreeRoutes) return;
      notifications.show({
        title: "Unauthorized",
        message: "You must be logged in to access this page",
        color: "red",
      })
      router.push('/login');
    }
  });

  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    user: null,
    token: null,
    gateway: null,
  });

  useEffect(() => {
    if (status === "loading") {
      return;
    }

    if (status === "authenticated" && session) {
      (async () => {
        try {
          await refreshAuth();
        } catch (error) {
          console.error("Auth restore failed:", error);
          // logout();
        }
      })()
    }
  }, [status, session]);

  const login = async (gateway: UserRole) => {
    await signIn("google", {
      callbackUrl: `http://localhost:3000/auth/callback/${gateway}`,
    })
  };

  const logout = () => {
    tokenService.clearStoredData();
    setAuthState({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      token: null,
      gateway: null,
    });
    signOut({
      callbackUrl: "/login",
    });
  };

  const refreshAuth = async () => {
    let token = tokenService.getStoredToken();
    const type = token?.user_type as UserRole;
    const gateway = getDataGateway(type);

    // * Restore auth state from local storage.
    if (!token) {
      const res = await gateway.login(session?.user?.email as string);
      token = {
        user_type: type,
        access_token: res.accessToken,
        refresh_token: res.refreshToken,
        expires_in: Number(res.expiresAt),  
      };
      tokenService.storeToken(token);
    };

    if (tokenService.isTokenExpired(token)) {
      token = await gateway.refreshToken(token.refresh_token);
      tokenService.storeToken(token);
    };

    gateway.setToken(token);

    const user = await gateway.getCurrentUser();

    setAuthState({
      isAuthenticated: true,
      isLoading: false,
      user: user,
      token: token,
      gateway: gateway,
    });
  };

  const getDataGateway = (gateway: UserRole): GatewayService => {
    return gateways[gateway]!!;
  };

  const contextValue: AuthContextType = {
    ...authState,
    login,
    logout,
    refreshAuth,
    getDataGateway,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
} 