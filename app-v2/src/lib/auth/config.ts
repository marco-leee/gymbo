import type { UserRole } from './types.js';

export function isValidGateway(gateway: string): gateway is UserRole {
	return ['admin', 'trainer', 'client', 'organisation'].includes(gateway);
}

export function getDefaultRedirectForGateway(gateway: UserRole): string {
	switch (gateway) {
		case 'client':
			return '/dashboard';
		case 'trainer':
			return '/dashboard/clients';
		case 'organisation':
			return '/dashboard/organisations';
		case 'admin':
			return '/dashboard';
		default:
			return '/dashboard';
	}
}

export const roleRouteAccess: Record<UserRole, string[]> = {
	client: ['/dashboard', '/dashboard/exercises', '/dashboard/assessments', '/dashboard/mobile', '/dashboard/desktop'],
	trainer: ['/dashboard/exercises', '/dashboard/assessments', '/dashboard/clients', '/dashboard/mobile', '/dashboard/desktop'],
	organisation: ['/dashboard/exercises', '/dashboard/assessments', '/dashboard/clients', '/dashboard/organisations'],
	admin: ['*'],
};

export function canUserAccessRoute(userRole: UserRole, pathname: string): boolean {
	const allowedRoutes = roleRouteAccess[userRole];
	if (allowedRoutes.includes('*')) return true;
	return allowedRoutes.some((route) => pathname.startsWith(route));
}
