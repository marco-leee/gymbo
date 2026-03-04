import { createClient } from '@connectrpc/connect';
import { createConnectTransport } from '@connectrpc/connect-web';
import type { Interceptor } from '@connectrpc/connect';
import { AdminGatewayService } from '$lib/proto/gateways/admin/v1/admin_gateway_pb.js';
import { tokenService } from '$lib/auth/token.js';

function getBaseUrl(): string {
	const url = import.meta.env?.PUBLIC_API_URL ?? import.meta.env?.VITE_PUBLIC_API_URL ?? '';
	return typeof url === 'string' && url.length > 0 ? url.replace(/\/$/, '') : '';
}

const authInterceptor: Interceptor = (next) => async (req) => {
	const token = tokenService.getStoredToken()?.access_token;
	if (token) {
		req.header.set('Authorization', `Bearer ${token}`);
	}
	return await next(req);
};

const transport = createConnectTransport({
	baseUrl: getBaseUrl(),
	useBinaryFormat: true,
	interceptors: [authInterceptor],
});

export const adminClient = createClient(AdminGatewayService, transport);
export { transport };
