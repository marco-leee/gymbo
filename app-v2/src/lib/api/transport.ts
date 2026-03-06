import { createClient } from '@connectrpc/connect';
import { createConnectTransport } from '@connectrpc/connect-web';
import { AdminGatewayService } from '$lib/proto/gateways/admin/v1/admin_gateway_pb.js';

function getBaseUrl(): string {
	const url = import.meta.env?.PUBLIC_API_URL ?? import.meta.env?.VITE_PUBLIC_API_URL ?? '';
	return typeof url === 'string' && url.length > 0 ? url.replace(/\/$/, '') : '';
}

const transport = createConnectTransport({
	baseUrl: getBaseUrl(),
	useBinaryFormat: true,
});

export const adminClient = createClient(AdminGatewayService, transport);
export { transport };
