<script lang="ts">
	import { createQuery } from '@tanstack/svelte-query';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import * as Sheet from '$lib/components/ui/sheet/index.js';
	import PlusIcon from '@lucide/svelte/icons/plus';
	import SearchIcon from '@lucide/svelte/icons/search';
	import { listClients, getClient } from '$lib/api/clients';

	let search = $state('');
	let selectedClientId = $state<string | null>(null);
	let drawerOpen = $state(false);

	const clientsQuery = createQuery(() => ({
		queryKey: ['clients', search],
		queryFn: () => listClients(search)
	}));

	const clientDetailQuery = createQuery(() => ({
		queryKey: ['client', selectedClientId],
		queryFn: () => getClient(selectedClientId!),
		enabled: !!selectedClientId && drawerOpen
	}));

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString();
	}

	function openClientDrawer(clientId: string) {
		selectedClientId = clientId;
		drawerOpen = true;
	}
</script>

<svelte:head>
	<title>Clients | Gymbo</title>
</svelte:head>

<div class="flex flex-col gap-8">
	<div class="flex flex-wrap items-end justify-between gap-4">
		<div>
			<h1 class="app-display text-4xl md:text-5xl" style="color: var(--app-text);">Clients</h1>
			<p class="mt-1 max-w-xl text-sm" style="color: var(--app-muted);">
				Search and open a client. Add new clients in one tap.
			</p>
		</div>
		<Button href="/app/clients/new" data-tour="clients-new" class="app-cta min-h-12 rounded-lg px-6 text-base">
			<PlusIcon class="mr-2 h-5 w-5" aria-hidden="true" />
			New client
		</Button>
	</div>

	<div class="app-card flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
		<div class="relative w-full sm:max-w-sm">
			<SearchIcon
				class="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2"
				style="color: var(--app-muted);"
				aria-hidden="true"
			/>
			<Input
				type="search"
				placeholder="Search clients…"
				class="min-h-11 border-zinc-600 bg-zinc-900/50 pl-9"
				bind:value={search}
			/>
		</div>
	</div>

	{#if clientsQuery.isLoading}
		<p style="color: var(--app-muted);">Loading…</p>
	{:else if clientsQuery.isError}
		<p class="text-red-400">Error: {clientsQuery.error.message}</p>
	{:else if clientsQuery.data && clientsQuery.data.clients.length > 0}
		<ul class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each clientsQuery.data.clients as client (client.id)}
				<li class="app-card flex flex-col gap-3 p-5">
					<div>
						<p class="text-lg font-semibold leading-tight">{client.full_name}</p>
						<p class="mt-1 text-sm" style="color: var(--app-muted);">{client.email}</p>
					</div>
					<p class="text-sm" style="color: var(--app-muted);">
						Added {formatDate(client.created_at)}
					</p>
					<Button
						class="app-cta mt-auto min-h-11 w-full rounded-lg"
						onclick={() => openClientDrawer(client.id)}
					>
						View details
					</Button>
				</li>
			{/each}
		</ul>
	{:else}
		<div class="app-card py-16 text-center">
			<p style="color: var(--app-muted);">No clients match. Create your first one.</p>
			<Button href="/app/clients/new" data-tour="clients-new" class="app-cta mt-4 min-h-11">New client</Button>
		</div>
	{/if}

	{#if clientsQuery.data && clientsQuery.data.total > 0}
		<p class="text-sm" style="color: var(--app-muted);">
			Showing {clientsQuery.data.clients.length} of {clientsQuery.data.total} clients
		</p>
	{/if}
</div>

<Sheet.Root bind:open={drawerOpen}>
	<Sheet.Content
		side="right"
		class="w-full max-w-md border-l"
		// style="background: var(--app-surface-2); color: var(--app-text); border-color: var(--app-border);"
	>
		<Sheet.Header>
			<Sheet.Title>Client details</Sheet.Title>
			<Sheet.Description style="color: var(--app-muted);">
				View information for this client.
			</Sheet.Description>
		</Sheet.Header>

		<div class="py-6">
			{#if clientDetailQuery.isLoading}
				<p style="color: var(--app-muted);">Loading client details…</p>
			{:else if clientDetailQuery.isError}
				<p class="text-red-400">Error: {clientDetailQuery.error.message}</p>
			{:else if clientDetailQuery.data}
				{@const client = clientDetailQuery.data}
				<div class="space-y-4">
					<div>
						<p class="text-sm" style="color: var(--app-muted);">Full name</p>
						<p class="font-medium">{client.full_name}</p>
					</div>
					<div>
						<p class="text-sm" style="color: var(--app-muted);">Email</p>
						<p class="font-medium">{client.email}</p>
					</div>
					<div>
						<p class="text-sm" style="color: var(--app-muted);">Gender</p>
						<p class="font-medium">{client.gender || 'Not specified'}</p>
					</div>
					<div class="grid grid-cols-2 gap-4">
						<div>
							<p class="text-sm" style="color: var(--app-muted);">Height</p>
							<p class="font-medium">{client.height_cm > 0 ? `${client.height_cm} cm` : 'Not specified'}</p>
						</div>
						<div>
							<p class="text-sm" style="color: var(--app-muted);">Weight</p>
							<p class="font-medium">{client.weight_kg > 0 ? `${client.weight_kg} kg` : 'Not specified'}</p>
						</div>
					</div>
					<div>
						<p class="text-sm" style="color: var(--app-muted);">Added on</p>
						<p class="font-medium">{formatDate(client.created_at)}</p>
					</div>
					<div>
						<p class="text-sm" style="color: var(--app-muted);">User ID</p>
						<p class="font-mono text-xs">{client.id}</p>
					</div>
				</div>
			{/if}
		</div>

		<Sheet.Footer>
			<Button
				variant="outline"
				class="app-outline min-h-11"
				onclick={() => (drawerOpen = false)}
			>
				Close
			</Button>
		</Sheet.Footer>
	</Sheet.Content>
</Sheet.Root>
