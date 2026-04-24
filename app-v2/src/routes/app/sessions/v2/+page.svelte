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
	import Trash2Icon from '@lucide/svelte/icons/trash-2';
	import { listSessions, deleteSession, type Session } from '$lib/api/sessions';
	import { listClients } from '$lib/api/clients';

	let selectedClientId = $state<string>('');
	let selectedStatus = $state<string>('');
	let datePreset = $state<string>('today');

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
		queryFn: () => listClients()
	}));

	const sessionsQuery = createQuery(() => {
		const { from, to } = getDateRange(datePreset);
		return {
			queryKey: ['sessions', 'v2', selectedClientId, selectedStatus, datePreset],
			queryFn: () =>
				listSessions({
					client: selectedClientId || undefined,
					status: selectedStatus || undefined,
					from,
					to,
					limit: 20,
					offset: 0,
					includePoseChartData: false,
					includeVideoPlayUrl: false
				})
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
		return session.exercises?.some((ex) => ex.sets?.some((s) => s.video_url)) ?? false;
	}

	function hubUrl(sessionId: string, view: 'overview' | 'plan' | 'analysis') {
		return `/app/sessions/v2/${sessionId}?view=${view}`;
	}

	function primaryRowAction(session: Session): { label: string; href: string } {
		if (session.status === 'completed') {
			return { label: 'Review', href: hubUrl(session.id, 'analysis') };
		}
		if (session.status === 'in-progress') {
			return { label: 'Continue', href: `/app/sessions/v2/${session.id}/record` };
		}
		if (session.status === 'scheduled') {
			return { label: 'Open', href: hubUrl(session.id, 'overview') };
		}
		return { label: 'Open', href: hubUrl(session.id, 'overview') };
	}

	async function handleDelete(sessionId: string, e: MouseEvent) {
		e.stopPropagation();
		if (!confirm('Delete this session? This cannot be undone.')) return;
		try {
			await deleteSession(sessionId);
			await goto('/app/sessions/v2');
		} catch (err) {
			alert(err instanceof Error ? err.message : 'Failed to delete');
		}
	}
</script>

<div class="flex flex-1 flex-col gap-4 p-4 pt-0">
	<div class="flex flex-wrap items-center justify-between gap-3">
		<div>
			<h1 class="text-2xl font-semibold">Sessions</h1>
			<p class="text-muted-foreground text-sm">Hub layout (v2) — fewer hops; recording opens full screen.</p>
		</div>
		<Button href="/app/sessions/v2/new" class="min-h-11 min-w-11">
			<PlusIcon class="mr-2 h-4 w-4" />
			New Session
		</Button>
	</div>

	<div class="flex flex-wrap items-center gap-3 rounded-lg border p-3">
		<div class="flex items-center gap-2">
			<SearchIcon class="h-4 w-4 text-muted-foreground" aria-hidden="true" />
			<Select.Root
				type="single"
				value={selectedClientId}
				onValueChange={(val) => (selectedClientId = val)}
			>
				<Select.Trigger class="w-[200px]">
					<span class={selectedClientId ? '' : 'text-muted-foreground'}>
						{selectedClientId
							? (clientsQuery.data?.clients.find((c) => c.id === selectedClientId)?.full_name ??
								'Select client...')
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

		<div class="flex items-center gap-2">
			<CalendarIcon class="h-4 w-4 text-muted-foreground" aria-hidden="true" />
			<div class="flex flex-wrap rounded-md border">
				<Button
					variant={datePreset === 'today' ? 'default' : 'ghost'}
					size="sm"
					class="min-h-9"
					onclick={() => (datePreset = 'today')}
				>
					Today
				</Button>
				<Button
					variant={datePreset === 'week' ? 'default' : 'ghost'}
					size="sm"
					class="min-h-9"
					onclick={() => (datePreset = 'week')}
				>
					This Week
				</Button>
				<Button
					variant={datePreset === 'month' ? 'default' : 'ghost'}
					size="sm"
					class="min-h-9"
					onclick={() => (datePreset = 'month')}
				>
					This Month
				</Button>
				<Button
					variant={datePreset === 'all' ? 'default' : 'ghost'}
					size="sm"
					class="min-h-9"
					onclick={() => (datePreset = 'all')}
				>
					All
				</Button>
			</div>
		</div>

		<div class="flex items-center gap-2">
			<Select.Root type="single" value={selectedStatus} onValueChange={(val) => (selectedStatus = val)}>
				<Select.Trigger class="w-[160px]">
					<span class={selectedStatus ? '' : 'text-muted-foreground'}>
						{selectedStatus
							? selectedStatus.charAt(0).toUpperCase() + selectedStatus.slice(1)
							: 'All statuses'}
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

		{#if selectedClientId || selectedStatus || datePreset !== 'today'}
			<Button
				variant="ghost"
				size="sm"
				class="min-h-9"
				onclick={() => {
					selectedClientId = '';
					selectedStatus = '';
					datePreset = 'today';
				}}
			>
				Clear filters
			</Button>
		{/if}
	</div>

	<div class="rounded-md border">
		<Table.Root>
			<Table.Header>
				<Table.Row>
					<Table.Head>Date & Time</Table.Head>
					<Table.Head>Client</Table.Head>
					<Table.Head>Exercises</Table.Head>
					<Table.Head>Status</Table.Head>
					<Table.Head class="text-end">Next step</Table.Head>
					<Table.Head class="text-end w-[52px]"><span class="sr-only">More</span></Table.Head>
				</Table.Row>
			</Table.Header>
			<Table.Body>
				{#if sessionsQuery.isLoading}
					<Table.Row>
						<Table.Cell colspan={6} class="py-8 text-center">Loading...</Table.Cell>
					</Table.Row>
				{:else if sessionsQuery.isError}
					<Table.Row>
						<Table.Cell colspan={6} class="text-destructive py-8 text-center">
							Error: {sessionsQuery.error.message}
						</Table.Cell>
					</Table.Row>
				{:else if sessionsQuery.data && sessionsQuery.data.sessions.length > 0}
					{#each sessionsQuery.data.sessions as session (session.id)}
						<Table.Row class="hover:bg-muted/50">
							<Table.Cell>
								<div class="font-medium">{formatDate(session.scheduled_at)}</div>
								<div class="text-muted-foreground text-sm">{formatTime(session.scheduled_at)}</div>
							</Table.Cell>
							<Table.Cell class="font-medium">
								{session.client_name || session.client_id}
							</Table.Cell>
							<Table.Cell>
								{getExerciseCount(session)} exercise{getExerciseCount(session) === 1 ? '' : 's'}
							</Table.Cell>
							<Table.Cell>
								<Badge variant={getStatusBadgeVariant(session.status)}>
									{session.status.charAt(0).toUpperCase() + session.status.slice(1)}
								</Badge>
							</Table.Cell>
							<Table.Cell class="text-end">
								{@const act = primaryRowAction(session)}
								<Button href={act.href} variant="default" size="sm" class="min-h-10">
									{act.label}
								</Button>
							</Table.Cell>
							<Table.Cell class="text-end">
								<DropdownMenu.Root>
									<DropdownMenu.Trigger
										class="inline-flex h-11 w-11 items-center justify-center rounded-md hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
										aria-label="More actions"
										onclick={(e) => e.stopPropagation()}
									>
										<MoreHorizontalIcon class="h-4 w-4" />
									</DropdownMenu.Trigger>
									<DropdownMenu.Content align="end" onclick={(e) => e.stopPropagation()}>
										<DropdownMenu.Item
											onclick={(e) => {
												e.stopPropagation();
												goto(hubUrl(session.id, 'overview'));
											}}
										>
											<EyeIcon class="mr-2 h-4 w-4" />
											View hub
										</DropdownMenu.Item>
										{#if session.status === 'scheduled' || session.status === 'in-progress'}
											<DropdownMenu.Item
												onclick={(e) => {
													e.stopPropagation();
													goto(`/app/sessions/v2/${session.id}/record`);
												}}
											>
												<VideoIcon class="mr-2 h-4 w-4" />
												Record
											</DropdownMenu.Item>
										{/if}
										{#if session.status === 'completed'}
											<DropdownMenu.Item
												onclick={(e) => {
													e.stopPropagation();
													goto(hubUrl(session.id, 'analysis'));
												}}
											>
												<BarChart3Icon class="mr-2 h-4 w-4" />
												Analysis
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
						<Table.Cell colspan={6} class="text-muted-foreground py-8 text-center">
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

	<p class="text-muted-foreground text-xs">
		Looking for the classic list?
		<a href="/app/sessions" class="text-primary underline-offset-4 hover:underline">Open legacy sessions</a>
	</p>
</div>
