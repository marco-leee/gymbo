import type { AuthToken } from './types.js';

const ACCESS_TOKEN_KEY = 'gymbo_auth_token';

export class TokenService {
	storeToken(token: AuthToken): void {
		localStorage.setItem(ACCESS_TOKEN_KEY, JSON.stringify(token));
	}

	getStoredToken(): AuthToken | null {
		const raw = localStorage.getItem(ACCESS_TOKEN_KEY);
		if (!raw) return null;
		try {
			return JSON.parse(raw) as AuthToken;
		} catch {
			return null;
		}
	}

	clearStoredData(): void {
		localStorage.removeItem(ACCESS_TOKEN_KEY);
	}

	isTokenExpired(token: AuthToken): boolean {
		if (!token.expires_in) return true;
		const expiryTime = new Date(token.expires_in * 1000);
		return new Date() >= expiryTime;
	}
}

export const tokenService = new TokenService();
