<script lang="ts">
	import { createQuery } from '@tanstack/svelte-query';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import * as Sheet from '$lib/components/ui/sheet/index.js';
	import PlusIcon from '@lucide/svelte/icons/plus';
	import SearchIcon from '@lucide/svelte/icons/search';
	import { listClients, getClient } from '$lib/api/clients';
	import { queryClient } from '$lib/query-client';

	let search = $state('');
	let selectedClientId = $state<string | null>(null);
	let drawerOpen = $state(false);

	const clientsQuery = createQuery(() => ({
		queryKey: ['clients', search],
		queryFn: () => listClients(search),
	}));

	const clientDetailQuery = createQuery(() => ({
		queryKey: ['client', selectedClientId],
		queryFn: () => getClient(selectedClientId!),
		enabled: !!selectedClientId && drawerOpen,
	}));

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString();
	}

	function openClientDrawer(clientId: string) {
		selectedClientId = clientId;
		drawerOpen = true;
	}
</script>

<div class="flex flex-1 flex-col gap-4 p-4 pt-0">
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-semibold">Clients</h1>
		<Button href="/app/clients/new">
			<PlusIcon class="mr-2 h-4 w-4" />
			New Client
		</Button>
	</div>

	<div class="flex items-center gap-2">
		<div class="relative flex-1 max-w-sm">
			<SearchIcon class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
			<Input
				type="search"
				placeholder="Search clients..."
				class="pl-8"
				bind:value={search}
			/>
		</div>
	</div>

	<div class="rounded-md border">
		<Table.Root>
			<Table.Header>
				<Table.Row>
					<Table.Head>Name</Table.Head>
					<Table.Head>Email</Table.Head>
					<Table.Head>Added</Table.Head>
					<Table.Head class="text-right">Actions</Table.Head>
				</Table.Row>
			</Table.Header>
			<Table.Body>
				{#if clientsQuery.isLoading}
					<Table.Row>
						<Table.Cell colspan={4} class="py-8 text-center">
							Loading...
						</Table.Cell>
					</Table.Row>
				{:else if clientsQuery.isError}
					<Table.Row>
						<Table.Cell colspan={4} class="text-destructive py-8 text-center">
							Error: {clientsQuery.error.message}
						</Table.Cell>
					</Table.Row>
				{:else if clientsQuery.data && clientsQuery.data.clients.length > 0}
					{#each clientsQuery.data.clients as client (client.id)}
						<Table.Row
							class="cursor-pointer hover:bg-muted/50"
							onclick={() => openClientDrawer(client.id)}
						>
							<Table.Cell class="font-medium">{client.full_name}</Table.Cell>
							<Table.Cell>{client.email}</Table.Cell>
							<Table.Cell>{formatDate(client.created_at)}</Table.Cell>
							<Table.Cell class="text-right">
								<Button variant="ghost" size="sm" onclick={(e) => { e.stopPropagation(); openClientDrawer(client.id); }}>
									View
								</Button>
							</Table.Cell>
						</Table.Row>
					{/each}
				{:else}
					<Table.Row>
						<Table.Cell colspan={4} class="text-muted-foreground py-8 text-center">
							No clients found. Create your first client to get started.
						</Table.Cell>
					</Table.Row>
				{/if}
			</Table.Body>
		</Table.Root>
	</div>

	{#if clientsQuery.data && clientsQuery.data.total > 0}
		<p class="text-muted-foreground text-sm">
			Showing {clientsQuery.data.clients.length} of {clientsQuery.data.total} clients
		</p>
	{/if}
</div>

<Sheet.Root bind:open={drawerOpen}>
	<Sheet.Content side="right" class="w-full max-w-md">
		<Sheet.Header>
			<Sheet.Title>Client Details</Sheet.Title>
			<Sheet.Description>
				View detailed information about this client.
			</Sheet.Description>
		</Sheet.Header>

		<div class="py-6">
			{#if clientDetailQuery.isLoading}
				<p class="text-muted-foreground">Loading client details...</p>
			{:else if clientDetailQuery.isError}
				<p class="text-destructive">Error: {clientDetailQuery.error.message}</p>
			{:else if clientDetailQuery.data}
				{@const client = clientDetailQuery.data}
				<div class="space-y-4">
					<div>
						<p class="text-muted-foreground text-sm">Full Name</p>
						<p class="font-medium">{client.full_name}</p>
					</div>
					<div>
						<p class="text-muted-foreground text-sm">Email</p>
						<p class="font-medium">{client.email}</p>
					</div>
					<div>
						<p class="text-muted-foreground text-sm">Gender</p>
						<p class="font-medium">{client.gender || 'Not specified'}</p>
					</div>
					<div class="grid grid-cols-2 gap-4">
						<div>
							<p class="text-muted-foreground text-sm">Height</p>
							<p class="font-medium">{client.height_cm > 0 ? `${client.height_cm} cm` : 'Not specified'}</p>
						</div>
						<div>
							<p class="text-muted-foreground text-sm">Weight</p>
							<p class="font-medium">{client.weight_kg > 0 ? `${client.weight_kg} kg` : 'Not specified'}</p>
						</div>
					</div>
					<div>
						<p class="text-muted-foreground text-sm">Added On</p>
						<p class="font-medium">{formatDate(client.created_at)}</p>
					</div>
					<div>
						<p class="text-muted-foreground text-sm">User ID</p>
						<p class="font-mono text-xs">{client.user_id}</p>
					</div>
				</div>
			{/if}
		</div>

		<Sheet.Footer>
			<Button variant="outline" onclick={() => drawerOpen = false}>
				Close
			</Button>
		</Sheet.Footer>
	</Sheet.Content>
</Sheet.Root>
