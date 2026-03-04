import type { User } from '$lib/proto/shared/messages/v1/auth_pb.js';

export type UserRole = 'admin' | 'trainer' | 'client' | 'organisation';

export const UserRoles: readonly UserRole[] = [
	'admin',
	'trainer',
	'client',
	'organisation',
] as const;

export interface AuthToken {
	user_type: UserRole;
	access_token: string;
	refresh_token: string;
	expires_in: number;
}

export interface AuthState {
	isLoading: boolean;
	isAuthenticated: boolean;
	user: User | null;
	token: AuthToken | null;
	gateway: UserRole | null;
}
