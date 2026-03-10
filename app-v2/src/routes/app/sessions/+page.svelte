<script lang="ts">
	import { goto } from '$app/navigation';
	import { createQuery } from '@tanstack/svelte-query';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import PlusIcon from '@lucide/svelte/icons/plus';
	import SearchIcon from '@lucide/svelte/icons/search';
	import CalendarIcon from '@lucide/svelte/icons/calendar';
	import MoreHorizontalIcon from '@lucide/svelte/icons/more-horizontal';
	import EyeIcon from '@lucide/svelte/icons/eye';
	import VideoIcon from '@lucide/svelte/icons/video';
	import BarChart3Icon from '@lucide/svelte/icons/bar-chart-3';
	import PencilIcon from '@lucide/svelte/icons/pencil';
	import Trash2Icon from '@lucide/svelte/icons/trash-2';
	import { listSessions, deleteSession, type Session } from '$lib/api/sessions';
	import { listClients } from '$lib/api/clients';

	// Filter states
	let selectedClientId = $state<string>('');
	let selectedStatus = $state<string>('');
	let datePreset = $state<string>('today');

	// Get date range based on preset
	function getDateRange(preset: string): { from?: string; to?: string } {
		const today = new Date();
		today.setHours(0, 0, 0, 0);

		switch (preset) {
			case 'today':
				return {
					from: today.toISOString(),
					to: new Date(today.getTime() + 24 * 60 * 60 * 1000).toISOString()
				};
			case 'week': {
				const weekEnd = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
				return { from: today.toISOString(), to: weekEnd.toISOString() };
			}
			case 'month': {
				const monthEnd = new Date(today.getFullYear(), today.getMonth() + 1, 0);
				monthEnd.setHours(23, 59, 59, 999);
				return { from: today.toISOString(), to: monthEnd.toISOString() };
			}
			default:
				return {};
		}
	}

	const clientsQuery = createQuery(() => ({
		queryKey: ['clients', 'all'],
		queryFn: () => listClients(),
	}));

	const sessionsQuery = createQuery(() => {
		const { from, to } = getDateRange(datePreset);
		return {
			queryKey: ['sessions', selectedClientId, selectedStatus, datePreset],
			queryFn: () => listSessions({
				client: selectedClientId || undefined,
				status: selectedStatus || undefined,
				from,
				to,
				limit: 20,
				offset: 0
			}),
		};
	});

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString(undefined, {
			weekday: 'short',
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function formatTime(dateStr: string): string {
		return new Date(dateStr).toLocaleTimeString(undefined, {
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function getStatusBadgeVariant(status: string): 'default' | 'secondary' | 'destructive' | 'outline' {
		switch (status) {
			case 'scheduled':
				return 'outline';
			case 'in-progress':
				return 'default';
			case 'completed':
				return 'secondary';
			case 'cancelled':
				return 'destructive';
			default:
				return 'outline';
		}
	}

	function getExerciseCount(session: Session): number {
		return session.exercises?.length ?? 0;
	}

	function hasVideos(session: Session): boolean {
		return session.exercises?.some(ex => ex.sets?.some(s => s.video_url)) ?? false;
	}

	async function handleDelete(sessionId: string, e: MouseEvent) {
		e.stopPropagation();
		if (!confirm('Delete this session? This cannot be undone.')) return;
		try {
			await deleteSession(sessionId);
			await goto('/app/sessions');
		} catch (err) {
			alert(err instanceof Error ? err.message : 'Failed to delete');
		}
	}
</script>

<div class="flex flex-1 flex-col gap-4 p-4 pt-0">
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-semibold">Sessions</h1>
		<Button href="/app/sessions/new">
			<PlusIcon class="mr-2 h-4 w-4" />
			New Session
		</Button>
	</div>

	<!-- Filter Panel -->
	<div class="flex flex-wrap items-center gap-3 rounded-lg border p-3">
		<!-- Client Selector -->
		<div class="flex items-center gap-2">
			<SearchIcon class="h-4 w-4 text-muted-foreground" />
			<Select.Root
				type="single"
				value={selectedClientId}
				onValueChange={(val) => selectedClientId = val}
			>
				<Select.Trigger class="w-[200px]">
					<span class={selectedClientId ? '' : 'text-muted-foreground'}>
						{selectedClientId
							? clientsQuery.data?.clients.find(c => c.id === selectedClientId)?.full_name ?? 'Select client...'
							: 'All clients'}
					</span>
				</Select.Trigger>
				<Select.Content>
					<Select.Item value="">All clients</Select.Item>
					{#if clientsQuery.data}
						{#each clientsQuery.data.clients as client}
							<Select.Item value={client.id}>{client.full_name}</Select.Item>
						{/each}
					{/if}
				</Select.Content>
			</Select.Root>
		</div>

		<!-- Date Range Presets -->
		<div class="flex items-center gap-2">
			<CalendarIcon class="h-4 w-4 text-muted-foreground" />
			<div class="flex rounded-md border">
				<Button
					variant={datePreset === 'today' ? 'default' : 'ghost'}
					size="sm"
					onclick={() => datePreset = 'today'}
				>
					Today
				</Button>
				<Button
					variant={datePreset === 'week' ? 'default' : 'ghost'}
					size="sm"
					onclick={() => datePreset = 'week'}
				>
					This Week
				</Button>
				<Button
					variant={datePreset === 'month' ? 'default' : 'ghost'}
					size="sm"
					onclick={() => datePreset = 'month'}
				>
					This Month
				</Button>
				<Button
					variant={datePreset === 'all' ? 'default' : 'ghost'}
					size="sm"
					onclick={() => datePreset = 'all'}
				>
					All
				</Button>
			</div>
		</div>

		<!-- Status Filter -->
		<div class="flex items-center gap-2">
			<Select.Root
				type="single"
				value={selectedStatus}
				onValueChange={(val) => selectedStatus = val}
			>
				<Select.Trigger class="w-[160px]">
					<span class={selectedStatus ? '' : 'text-muted-foreground'}>
						{selectedStatus ? selectedStatus.charAt(0).toUpperCase() + selectedStatus.slice(1) : 'All statuses'}
					</span>
				</Select.Trigger>
				<Select.Content>
					<Select.Item value="">All statuses</Select.Item>
					<Select.Item value="scheduled">Scheduled</Select.Item>
					<Select.Item value="in-progress">In Progress</Select.Item>
					<Select.Item value="completed">Completed</Select.Item>
					<Select.Item value="cancelled">Cancelled</Select.Item>
				</Select.Content>
			</Select.Root>
		</div>

		<!-- Clear Filters -->
		{#if selectedClientId || selectedStatus || datePreset !== 'today'}
			<Button variant="ghost" size="sm" onclick={() => {
				selectedClientId = '';
				selectedStatus = '';
				datePreset = 'today';
			}}>
				Clear filters
			</Button>
		{/if}
	</div>

	<!-- Sessions Table -->
	<div class="rounded-md border">
		<Table.Root>
			<Table.Header>
				<Table.Row>
					<Table.Head>Date & Time</Table.Head>
					<Table.Head>Client</Table.Head>
					<Table.Head>Exercises</Table.Head>
					<Table.Head>Status</Table.Head>
					<Table.Head class="text-right">Actions</Table.Head>
				</Table.Row>
			</Table.Header>
			<Table.Body>
				{#if sessionsQuery.isLoading}
					<Table.Row>
						<Table.Cell colspan={5} class="py-8 text-center">
							Loading...
						</Table.Cell>
					</Table.Row>
				{:else if sessionsQuery.isError}
					<Table.Row>
						<Table.Cell colspan={5} class="text-destructive py-8 text-center">
							Error: {sessionsQuery.error.message}
						</Table.Cell>
					</Table.Row>
				{:else if sessionsQuery.data && sessionsQuery.data.sessions.length > 0}
					{#each sessionsQuery.data.sessions as session (session.id)}
						<Table.Row
							class="cursor-pointer hover:bg-muted/50"
							onclick={() => goto(`/app/sessions/${session.id}`)}
						>
							<Table.Cell>
								<div class="font-medium">{formatDate(session.scheduled_at)}</div>
								<div class="text-muted-foreground text-sm">{formatTime(session.scheduled_at)}</div>
							</Table.Cell>
							<Table.Cell class="font-medium">
								{session.client_name ?? session.client_id}
							</Table.Cell>
							<Table.Cell>
								{getExerciseCount(session)} exercise{getExerciseCount(session) === 1 ? '' : 's'}
							</Table.Cell>
							<Table.Cell>
								<Badge variant={getStatusBadgeVariant(session.status)}>
									{session.status.charAt(0).toUpperCase() + session.status.slice(1)}
								</Badge>
							</Table.Cell>
							<Table.Cell class="text-right">
								<DropdownMenu.Root>
									<DropdownMenu.Trigger
										class="focus:outline-none"
										onclick={(e) => e.stopPropagation()}
									>
										<Button variant="ghost" size="icon">
											<MoreHorizontalIcon class="h-4 w-4" />
										</Button>
									</DropdownMenu.Trigger>
									<DropdownMenu.Content align="end" onclick={(e) => e.stopPropagation()}>
										<DropdownMenu.Item onclick={(e) => { e.stopPropagation(); goto(`/app/sessions/${session.id}`); }}>
											<EyeIcon class="mr-2 h-4 w-4" />
											View
										</DropdownMenu.Item>
										{#if session.status === 'scheduled' || session.status === 'in-progress'}
											<DropdownMenu.Item onclick={(e) => { e.stopPropagation(); goto(`/app/sessions/${session.id}/record`); }}>
												<VideoIcon class="mr-2 h-4 w-4" />
												Record
											</DropdownMenu.Item>
										{/if}
										{#if session.status === 'completed'}
											<DropdownMenu.Item onclick={(e) => { e.stopPropagation(); goto(`/app/sessions/${session.id}/analysis`); }}>
												<BarChart3Icon class="mr-2 h-4 w-4" />
												Analysis
											</DropdownMenu.Item>
										{/if}
										{#if session.status === 'scheduled' && !hasVideos(session)}
											<DropdownMenu.Item onclick={(e) => { e.stopPropagation(); goto(`/app/sessions/${session.id}/edit`); }}>
												<PencilIcon class="mr-2 h-4 w-4" />
												Edit
											</DropdownMenu.Item>
										{/if}
										{#if (session.status === 'scheduled' || session.status === 'in-progress') && !hasVideos(session)}
											<DropdownMenu.Separator />
											<DropdownMenu.Item
												class="text-destructive focus:text-destructive"
												onclick={(e) => handleDelete(session.id, e)}
											>
												<Trash2Icon class="mr-2 h-4 w-4" />
												Delete
											</DropdownMenu.Item>
										{/if}
									</DropdownMenu.Content>
								</DropdownMenu.Root>
							</Table.Cell>
						</Table.Row>
					{/each}
				{:else}
					<Table.Row>
						<Table.Cell colspan={5} class="text-muted-foreground py-8 text-center">
							No sessions found. Create your first session to get started.
						</Table.Cell>
					</Table.Row>
				{/if}
			</Table.Body>
		</Table.Root>
	</div>

	{#if sessionsQuery.data && sessionsQuery.data.total > 0}
		<p class="text-muted-foreground text-sm">
			Showing {sessionsQuery.data.sessions.length} of {sessionsQuery.data.total} sessions
		</p>
	{/if}
</div>
