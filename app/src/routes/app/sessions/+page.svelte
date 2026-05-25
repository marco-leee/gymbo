<script lang="ts">
	import { goto } from '$app/navigation';
	import { createQuery } from '@tanstack/svelte-query';
	import { Button } from '$lib/components/ui/button/index.js';
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
				const weekStart = new Date(today);
				const daysSinceMonday = (weekStart.getDay() + 6) % 7;
				weekStart.setDate(weekStart.getDate() - daysSinceMonday);
				const weekEnd = new Date(weekStart);
				weekEnd.setDate(weekEnd.getDate() + 7);
				return { from: weekStart.toISOString(), to: weekEnd.toISOString() };
			}
			case 'month': {
				const monthStart = new Date(today.getFullYear(), today.getMonth(), 1);
				const monthEnd = new Date(today.getFullYear(), today.getMonth() + 1, 1);
				return { from: monthStart.toISOString(), to: monthEnd.toISOString() };
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
			queryKey: ['sessions', 'app', selectedClientId, selectedStatus, datePreset],
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

	function hubUrl(sessionId: string, view: 'session' | 'analysis') {
		return `/app/sessions/${sessionId}?view=${view}`;
	}

	function primaryRowAction(session: Session): { label: string; href: string } {
		if (session.status === 'completed') {
			return { label: 'Review', href: hubUrl(session.id, 'analysis') };
		}
		if (session.status === 'in-progress') {
			return { label: 'Continue', href: `/app/sessions/${session.id}/run` };
		}
		return { label: 'Open', href: hubUrl(session.id, 'session') };
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

<svelte:head>
	<title>Sessions | Gymbo</title>
</svelte:head>

<div class="flex flex-col gap-8">
	<div class="flex flex-wrap items-end justify-between gap-4">
		<div>
			<h1 class="app-display text-4xl md:text-5xl" style="color: var(--app-text);">Sessions</h1>
			<p class="mt-1 max-w-xl text-sm" style="color: var(--app-muted);">
				Bold layout — jump in with one tap. Live workouts use execution mode.
			</p>
		</div>
		<Button href="/app/sessions/new" class="app-cta min-h-12 rounded-lg px-6 text-base">
			<PlusIcon class="mr-2 h-5 w-5" aria-hidden="true" />
			New session
		</Button>
	</div>

	<div class="app-card flex flex-wrap items-center gap-3 p-4">
		<div class="flex items-center gap-2">
			<SearchIcon class="h-4 w-4 shrink-0" style="color: var(--app-muted);" aria-hidden="true" />
			<Select.Root type="single" value={selectedClientId} onValueChange={(val) => (selectedClientId = val)}>
				<Select.Trigger class="w-[200px] border-zinc-600 bg-zinc-900/50">
					<span class={selectedClientId ? '' : 'text-zinc-500'}>
						{selectedClientId
							? (clientsQuery.data?.clients.find((c) => c.id === selectedClientId)?.full_name ??
								'Client')
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
			<CalendarIcon class="h-4 w-4 shrink-0" style="color: var(--app-muted);" aria-hidden="true" />
			<div class="flex flex-wrap gap-1 rounded-lg border p-1" style="border-color: var(--app-border);">
				{#each ['today', 'week', 'month', 'all'] as preset}
					<Button
						variant={datePreset === preset ? 'default' : 'ghost'}
						size="sm"
						class="min-h-9 rounded-md {datePreset === preset ? 'app-cta' : 'app-ghost'}"
						onclick={() => (datePreset = preset)}
					>
						{preset === 'today'
							? 'Today'
							: preset === 'week'
								? 'Week'
								: preset === 'month'
									? 'Month'
									: 'All'}
					</Button>
				{/each}
			</div>
		</div>
		<Select.Root type="single" value={selectedStatus} onValueChange={(val) => (selectedStatus = val)}>
			<Select.Trigger class="w-[160px] border-zinc-600 bg-zinc-900/50">
				<span class={selectedStatus ? '' : 'text-zinc-500'}>
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
		{#if selectedClientId || selectedStatus || datePreset !== 'today'}
			<Button variant="ghost" size="sm" class="app-ghost min-h-9" onclick={() => {
				selectedClientId = '';
				selectedStatus = '';
				datePreset = 'today';
			}}>
				Clear
			</Button>
		{/if}
	</div>

	{#if sessionsQuery.isLoading}
		<p style="color: var(--app-muted);">Loading…</p>
	{:else if sessionsQuery.isError}
		<p class="text-red-400">Error: {sessionsQuery.error.message}</p>
	{:else if sessionsQuery.data && sessionsQuery.data.sessions.length > 0}
		<ul class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each sessionsQuery.data.sessions as session (session.id)}
				{@const act = primaryRowAction(session)}
				<li class="app-card flex flex-col gap-4 p-5">
					<div class="flex items-start justify-between gap-2">
						<div>
							<p class="app-display text-2xl leading-none" style="color: var(--app-accent);">
								{formatTime(session.scheduled_at)}
							</p>
							<p class="mt-1 text-sm" style="color: var(--app-muted);">
								{formatDate(session.scheduled_at)}
							</p>
						</div>
						<Badge variant={getStatusBadgeVariant(session.status)} class="shrink-0 capitalize">
							{session.status.replace('-', ' ')}
						</Badge>
					</div>
					<p class="text-lg font-semibold leading-tight">
						{session.client_name || session.client_id}
					</p>
					<p class="text-sm" style="color: var(--app-muted);">
						{getExerciseCount(session)} exercise{getExerciseCount(session) === 1 ? '' : 's'}
					</p>
					<div class="mt-auto flex flex-wrap items-center gap-2">
						<Button href={act.href} class="app-cta min-h-11 flex-1 rounded-lg">
							{act.label}
						</Button>
						<!-- TODO: Review this dropdown menu -->
						<!-- <DropdownMenu.Root>
							<DropdownMenu.Trigger
								class="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--app-accent)]"
								style="border-color: var(--app-border);"
								aria-label="More actions"
							>
								<MoreHorizontalIcon class="h-4 w-4" />
							</DropdownMenu.Trigger>
							<DropdownMenu.Content align="end">
								<DropdownMenu.Item onclick={() => goto(hubUrl(session.id, 'session'))}>
									<EyeIcon class="mr-2 h-4 w-4" />
									Session hub
								</DropdownMenu.Item>
								{#if session.status === 'scheduled' || session.status === 'in-progress'}
									<DropdownMenu.Item onclick={() => goto(`/app/sessions/${session.id}/run`)}>
										<VideoIcon class="mr-2 h-4 w-4" />
										Execution
									</DropdownMenu.Item>
									<DropdownMenu.Item onclick={() => goto(`/app/sessions/${session.id}/record`)}>
										Table recorder
									</DropdownMenu.Item>
								{/if}
								{#if session.status === 'completed'}
									<DropdownMenu.Item onclick={() => goto(hubUrl(session.id, 'analysis'))}>
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
						</DropdownMenu.Root> -->
					</div>
				</li>
			{/each}
		</ul>
	{:else}
		<div class="app-card py-16 text-center">
			<p style="color: var(--app-muted);">No sessions match. Create one to start.</p>
			<Button href="/app/sessions/new" class="app-cta mt-4">New session</Button>
		</div>
	{/if}

	{#if sessionsQuery.data && sessionsQuery.data.total > 0}
		<p class="text-sm" style="color: var(--app-muted);">
			Showing {sessionsQuery.data.sessions.length} of {sessionsQuery.data.total}
		</p>
	{/if}
</div>
