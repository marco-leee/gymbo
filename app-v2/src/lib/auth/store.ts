import { writable } from 'svelte/store';
import { adminClient } from '$lib/api/transport.js';
import { queryClient } from '$lib/query-client.js';
import { tokenService } from './token.js';
import { getDefaultRedirectForGateway } from './config.js';
import type { AuthState, AuthToken, UserRole } from './types.js';
import type { User } from '$lib/proto/shared/messages/v1/auth_pb.js';

export const CURRENT_USER_QUERY_KEY = ['auth', 'currentUser'] as const;

const initialState: AuthState = {
	isLoading: true,
	isAuthenticated: false,
	user: null,
	token: null,
	gateway: null,
};

function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>(initialState);

	async function refreshAuth(): Promise<void> {
		let token = tokenService.getStoredToken();
		const type = (token?.user_type ?? 'admin') as UserRole;

		if (!token?.access_token) {
			update((s) => ({ ...s, isLoading: false, isAuthenticated: false, user: null, token: null, gateway: null }));
			queryClient.removeQueries({ queryKey: CURRENT_USER_QUERY_KEY });
			return;
		}

		if (tokenService.isTokenExpired(token)) {
			try {
				const res = await adminClient.refreshToken({ refreshToken: token.refresh_token });
				token = {
					user_type: type,
					access_token: res.accessToken,
					refresh_token: res.refreshToken,
					expires_in: Number(res.expiresAt),
				};
				tokenService.storeToken(token);
			} catch {
				tokenService.clearStoredData();
				update((s) => ({ ...s, isLoading: false, isAuthenticated: false, user: null, token: null, gateway: null }));
				queryClient.removeQueries({ queryKey: CURRENT_USER_QUERY_KEY });
				return;
			}
		}

		if (type !== 'admin') {
			update((s) => ({ ...s, isLoading: false, isAuthenticated: false, user: null, token: null, gateway: null }));
			return;
		}

		try {
			const res = await adminClient.getCurrentUser({});
			const user = res.user;
			if (!user) throw new Error('No user');
			update((s) => ({
				...s,
				isLoading: false,
				isAuthenticated: true,
				user: user as User,
				token,
				gateway: 'admin',
			}));
			queryClient.setQueryData(CURRENT_USER_QUERY_KEY, user);
		} catch {
			tokenService.clearStoredData();
			update((s) => ({ ...s, isLoading: false, isAuthenticated: false, user: null, token: null, gateway: null }));
			queryClient.removeQueries({ queryKey: CURRENT_USER_QUERY_KEY });
		}
	}

	async function login(
		email: string,
		gateway: UserRole = 'admin',
		goto?: (path: string) => void
	): Promise<void> {
		if (gateway !== 'admin') throw new Error('Only admin gateway is supported');
		try {
			
		} catch (err) {
			console.error(err);
			throw err;
		}
		const loginRes = await adminClient.login({ email });
		const token: AuthToken = {
			user_type: gateway,
			access_token: loginRes.accessToken,
			refresh_token: loginRes.refreshToken,
			expires_in: Number(loginRes.expiresAt),
		};
		tokenService.storeToken(token);
		const userRes = await adminClient.getCurrentUser({});
		const user = userRes.user;
		if (!user) throw new Error('No user in response');
		update((s) => ({
			...s,
			isLoading: false,
			isAuthenticated: true,
			user: user as User,
			token,
			gateway: 'admin',
		}));
		queryClient.setQueryData(CURRENT_USER_QUERY_KEY, user);
		const redirectTo = getDefaultRedirectForGateway(gateway);
		if (goto) goto(redirectTo);
	}

	function logout(goto?: (path: string) => void): void {
		tokenService.clearStoredData();
		set({
			isLoading: false,
			isAuthenticated: false,
			user: null,
			token: null,
			gateway: null,
		});
		queryClient.removeQueries({ queryKey: CURRENT_USER_QUERY_KEY });
		if (goto) goto('/login');
	}

	return {
		subscribe,
		set,
		refreshAuth,
		login,
		logout,
	};
}

export const authStore = createAuthStore();
