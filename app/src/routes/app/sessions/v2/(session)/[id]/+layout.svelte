<script lang="ts">
	import { page } from '$app/stores';
	import { invalidateAll } from '$app/navigation';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import ChevronLeftIcon from '@lucide/svelte/icons/chevron-left';
	import PencilIcon from '@lucide/svelte/icons/pencil';
	import Trash2Icon from '@lucide/svelte/icons/trash-2';
	import SessionV2EditSheet from '$lib/components/session-v2-edit-sheet.svelte';
	import { deleteSession, type Session } from '$lib/api/sessions';
	import { goto } from '$app/navigation';

	let { data, children } = $props();

	const sessionId = $derived($page.params.id);
	const view = $derived(($page.url.searchParams.get('view') ?? 'overview') as
		| 'overview'
		| 'plan'
		| 'analysis');

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

	function tabClass(v: string) {
		const active = view === v;
		return active
			? 'border-primary text-foreground min-h-10 border-b-2 px-3 py-2 text-sm font-medium'
			: 'text-muted-foreground hover:text-foreground min-h-10 border-b-2 border-transparent px-3 py-2 text-sm font-medium';
	}

	async function handleDelete() {
		if (!confirm('Delete this session? This cannot be undone.')) return;
		if (!sessionId) return;
		try {
			await deleteSession(sessionId);
			await goto('/app/sessions/v2');
		} catch (e) {
			alert(e instanceof Error ? e.message : 'Failed to delete');
		}
	}
</script>

<div class="flex flex-1 flex-col gap-4 p-4 pt-0">
	<div class="flex flex-wrap items-start gap-3">
		<Button href="/app/sessions/v2" variant="ghost" size="icon" class="shrink-0" aria-label="Back to sessions">
			<ChevronLeftIcon class="h-4 w-4" />
		</Button>
		<div class="min-w-0 flex-1">
			<nav aria-label="Breadcrumb" class="text-muted-foreground mb-1 text-xs">
				<ol class="flex flex-wrap items-center gap-1">
					<li>
						<a href="/app/sessions/v2" class="underline-offset-4 hover:text-foreground hover:underline">
							Sessions
						</a>
					</li>
					<li aria-hidden="true">/</li>
					<li class="truncate font-medium text-foreground">{clientLabel}</li>
					<li aria-hidden="true">/</li>
					<li class="tabular-nums">{formatDate(data.session.scheduled_at)}</li>
				</ol>
			</nav>
			<div class="flex flex-wrap items-center gap-2">
				<h1 class="text-2xl font-semibold">Session</h1>
				<Badge variant={getStatusBadgeVariant(data.session.status)}>
					{data.session.status.replace('-', ' ')}
				</Badge>
			</div>
			<p class="text-muted-foreground text-sm tabular-nums">
				{formatDate(data.session.scheduled_at)} · {formatTime(data.session.scheduled_at)}
			</p>
		</div>
		<div class="flex flex-wrap items-center gap-2">
			<Button
				type="button"
				variant="outline"
				size="sm"
				class="min-h-10"
				onclick={() => (editOpen = true)}
			>
				<PencilIcon class="mr-2 h-4 w-4" aria-hidden="true" />
				Edit details
			</Button>
			{#if canDelete}
				<Button type="button" variant="outline" size="sm" class="min-h-10" onclick={handleDelete}>
					<Trash2Icon class="mr-2 h-4 w-4" aria-hidden="true" />
					Delete
				</Button>
			{/if}
		</div>
	</div>

	<nav aria-label="Session views" class="-mx-1 overflow-x-auto border-b">
		<ul class="flex min-h-11 w-max gap-1 px-1">
			<li>
				<a
					href="/app/sessions/v2/{sessionId}?view=overview"
					class={tabClass('overview')}
					aria-current={view === 'overview' ? 'page' : undefined}
				>
					Overview
				</a>
			</li>
			<li>
				<a
					href="/app/sessions/v2/{sessionId}?view=plan"
					class={tabClass('plan')}
					aria-current={view === 'plan' ? 'page' : undefined}
				>
					Plan
				</a>
			</li>
			<li>
				<a
					href="/app/sessions/v2/{sessionId}?view=analysis"
					class={tabClass('analysis')}
					aria-current={view === 'analysis' ? 'page' : undefined}
				>
					Analysis
				</a>
			</li>
		</ul>
	</nav>

	<main id="session-v2-main">
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
