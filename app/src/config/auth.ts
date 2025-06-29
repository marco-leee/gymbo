import adminGateway from '@/services/admin-gateway';
import { UserRole } from '@/types/auth';
import { GatewayService } from '@/services/shared';

export function isValidGateway(gateway: string): gateway is UserRole {
  return ["admin", "trainer", "client", "organisation"].includes(gateway);
}

export const gateways: Record<UserRole, GatewayService | null> = {
  admin: adminGateway,
  trainer: null,
  client: null,
  organisation: null,
}

  // Helper function to get default redirect for each gateway
export const getDefaultRedirectForGateway = (gateway: UserRole): string => {
    switch (gateway) {
      case 'client':
        return '/app/dashboard';
      case 'trainer':
        return '/app/clients';
      case 'organisation':
        return '/app/organisations';
      case 'admin':
        return '/app/dashboard';
      default:
        return '/app/dashboard';
    }
  };

// Define which routes each user role can access
export const roleRouteAccess: Record<UserRole, string[]> = {
  client: ['/app/dashboard', '/app/exercise', '/app/assessment', '/app/mobile', '/app/desktop'],
  trainer: ['/app/exercise', '/app/assessment', '/app/client', '/app/mobile', '/app/desktop'],
  organisation: ['/app/exercise', '/app/assessment', '/app/client'],
  admin: ['*'], // Admin can access all routes
};
// Check if a user role can access a specific route
export function canUserAccessRoute(userRole: UserRole, pathname: string): boolean {
  const allowedRoutes = roleRouteAccess[userRole];
  
  if (allowedRoutes.includes('*')) {
    return true; // Admin can access everything
  }
  
  return allowedRoutes.some(route => pathname.startsWith(route));
}