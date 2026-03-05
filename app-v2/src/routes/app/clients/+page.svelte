<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import PlusIcon from '@lucide/svelte/icons/plus';
	import SearchIcon from '@lucide/svelte/icons/search';
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
			<Input type="search" placeholder="Search clients..." class="pl-8" />
		</div>
	</div>

	<div class="rounded-md border">
		<Table.Root>
			<Table.Header>
				<Table.Row>
					<Table.Head>Name</Table.Head>
					<Table.Head>Email</Table.Head>
					<Table.Head>Last Session</Table.Head>
					<Table.Head>Total Sessions</Table.Head>
					<Table.Head class="text-right">Actions</Table.Head>
				</Table.Row>
			</Table.Header>
			<Table.Body>
				<Table.Row>
					<Table.Cell colspan={5} class="text-muted-foreground py-8 text-center">
						No clients yet. Create your first client to get started.
					</Table.Cell>
				</Table.Row>
			</Table.Body>
		</Table.Root>
	</div>
</div>
