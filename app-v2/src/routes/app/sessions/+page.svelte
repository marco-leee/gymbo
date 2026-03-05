<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import PlusIcon from '@lucide/svelte/icons/plus';
	import SearchIcon from '@lucide/svelte/icons/search';
	import FilterIcon from '@lucide/svelte/icons/filter';
</script>

<div class="flex flex-1 flex-col gap-4 p-4 pt-0">
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-semibold">Sessions</h1>
		<Button href="/app/sessions/new">
			<PlusIcon class="mr-2 h-4 w-4" />
			New Session
		</Button>
	</div>

	<div class="flex items-center gap-2">
		<div class="relative flex-1 max-w-sm">
			<SearchIcon class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
			<Input type="search" placeholder="Search sessions..." class="pl-8" />
		</div>
		<Button variant="outline" size="icon">
			<FilterIcon class="h-4 w-4" />
		</Button>
	</div>

	<div class="rounded-md border">
		<Table.Root>
			<Table.Header>
				<Table.Row>
					<Table.Head>Date</Table.Head>
					<Table.Head>Client</Table.Head>
					<Table.Head>Exercises</Table.Head>
					<Table.Head>Status</Table.Head>
					<Table.Head class="text-right">Actions</Table.Head>
				</Table.Row>
			</Table.Header>
			<Table.Body>
				<Table.Row>
					<Table.Cell colspan={5} class="text-muted-foreground py-8 text-center">
						No sessions yet. Create your first session to get started.
					</Table.Cell>
				</Table.Row>
			</Table.Body>
		</Table.Root>
	</div>
</div>
