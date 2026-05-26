<script lang="ts">
	import { page } from '$app/stores';
	import { invalidateAll } from '$app/navigation';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import * as Tabs from '$lib/components/ui/tabs/index.js';
	import ChevronLeftIcon from '@lucide/svelte/icons/chevron-left';
	import PencilIcon from '@lucide/svelte/icons/pencil';
	import Trash2Icon from '@lucide/svelte/icons/trash-2';
	import SessionV2EditSheet from '$lib/components/session-v2-edit-sheet.svelte';
	import { deleteSession, type Session } from '$lib/api/sessions';
	import { goto } from '$app/navigation';

	let { data, children } = $props();

	const sessionId = $derived($page.params.id);
	const view = $derived(($page.url.searchParams.get('view') ?? 'session') as 'session' | 'analysis');

	let editOpen = $state(false);

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

	function getStatusBadgeVariant(
		status: string
	): 'default' | 'secondary' | 'destructive' | 'outline' {
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

	function hasVideos(session: Session): boolean {
		return session.exercises?.some((ex) => ex.sets?.some((s) => s.video_url)) ?? false;
	}

	const canDelete = $derived(
		(data.session.status === 'scheduled' || data.session.status === 'in-progress') &&
			!hasVideos(data.session)
	);

	const clientLabel = $derived(
		data.client?.full_name ?? data.session.client_name ?? data.session.client_id
	);

	async function handleDelete() {
		if (!confirm('Delete this session? This cannot be undone.')) return;
		if (!sessionId) return;
		try {
			await deleteSession(sessionId);
			await goto('/app/sessions');
		} catch (e) {
			alert(e instanceof Error ? e.message : 'Failed to delete');
		}
	}
</script>

<div class="flex flex-col gap-6">
	<div class="flex flex-wrap items-start gap-4">
		<Button
			href="/app/sessions"
			variant="ghost"
			size="icon"
			class="app-ghost shrink-0"
			aria-label="Back to sessions"
		>
			<ChevronLeftIcon class="h-5 w-5" />
		</Button>
		<div class="min-w-0 flex-1">
			<nav aria-label="Breadcrumb" class="mb-2 text-xs font-medium uppercase tracking-wider" style="color: var(--app-muted);">
				<ol class="flex flex-wrap items-center gap-2">
					<li>
						<a href="/app/sessions" class="hover:text-[var(--app-accent)]">Sessions</a>
					</li>
					<li aria-hidden="true">/</li>
					<li class="truncate text-[var(--app-text)]">{clientLabel}</li>
					<li aria-hidden="true">/</li>
					<li class="tabular-nums">{formatDate(data.session.scheduled_at)}</li>
				</ol>
			</nav>
			<div class="flex flex-wrap items-center gap-3">
				<h1 class="app-display text-3xl md:text-4xl" style="color: var(--app-text);">Session</h1>
				<Badge variant={getStatusBadgeVariant(data.session.status)} class="capitalize">
					{data.session.status.replace('-', ' ')}
				</Badge>
			</div>
			<p class="mt-1 text-sm tabular-nums" style="color: var(--app-muted);">
				{formatDate(data.session.scheduled_at)} · {formatTime(data.session.scheduled_at)}
			</p>
		</div>
		<div class="flex flex-wrap items-center gap-2">
			<Button type="button" variant="outline" size="sm" class="app-outline min-h-10" onclick={() => (editOpen = true)}>
				<PencilIcon class="mr-2 h-4 w-4" aria-hidden="true" />
				Edit
			</Button>
			{#if canDelete}
				<Button type="button" variant="outline" size="sm" class="min-h-10 border-red-500/50 text-red-400 hover:bg-red-500/10" onclick={handleDelete}>
					<Trash2Icon class="mr-2 h-4 w-4" aria-hidden="true" />
					Delete
				</Button>
			{/if}
		</div>
	</div>

	<nav aria-label="Session" class="w-full max-w-md">
		<Tabs.Root
			value={view}
			onValueChange={(v) => {
				if (v === 'session' || v === 'analysis') {
					goto(`/app/sessions/${sessionId}?view=${v}`, { keepFocus: true });
				}
			}}
			class="w-full"
		>
			<Tabs.List class="grid w-full grid-cols-2">
				<Tabs.Trigger value="session">Session</Tabs.Trigger>
				<Tabs.Trigger value="analysis">Analysis</Tabs.Trigger>
			</Tabs.List>
		</Tabs.Root>
	</nav>

	<main id="app-session-main">
		{@render children()}
	</main>
</div>

<SessionV2EditSheet
	bind:open={editOpen}
	sessionId={sessionId!}
	session={data.session}
	onSaved={async () => {
		await invalidateAll();
	}}
/>
