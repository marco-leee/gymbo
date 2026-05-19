import type { CreateClientInput, UpdateClientInput } from '$lib/services/models/client';

export interface Client {
	id: string;
	email: string;
	full_name: string;
	first_name: string;
	last_name: string;
	gender: string;
	height_cm: number;
	weight_kg: number;
	created_at: string;
	updated_at: string;
}

export interface ListClientsResponse {
	clients: Client[];
	total: number;
}

export async function listClients(search?: string, limit = 20, offset = 0): Promise<ListClientsResponse> {
	const params = new URLSearchParams();
	if (search) params.set('search', search);
	params.set('limit', String(limit));
	params.set('offset', String(offset));

	const response = await fetch(`/api/clients?${params}`);
	if (!response.ok) {
		throw new Error(`Failed to list clients: ${response.statusText}`);
	}
	return response.json();
}

export async function getClient(id: string, fetchFn: typeof fetch = fetch): Promise<Client> {
	const response = await fetchFn(`/api/clients/${id}`);
	if (!response.ok) {
		throw new Error(`Failed to get client: ${response.statusText}`);
	}
	return response.json();
}

export async function createClient(data: CreateClientInput): Promise<Client> {
	const response = await fetch('/api/clients', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(data)
	});
	if (!response.ok) {
		const error = await response.text();
		throw new Error(`Failed to create client: ${error}`);
	}
	return response.json();
}

export async function updateClient(id: string, data: UpdateClientInput): Promise<Client> {
	const response = await fetch(`/api/clients/${id}`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(data)
	});
	if (!response.ok) {
		throw new Error(`Failed to update client: ${response.statusText}`);
	}
	return response.json();
}

export async function deleteClient(id: string): Promise<void> {
	const response = await fetch(`/api/clients/${id}`, {
		method: 'DELETE'
	});
	if (!response.ok) {
		throw new Error(`Failed to delete client: ${response.statusText}`);
	}
}
