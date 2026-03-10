<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import ChevronLeftIcon from '@lucide/svelte/icons/chevron-left';
	import { updateSession } from '$lib/api/sessions';

	let { data } = $props();
	const sessionId = $derived($page.params.id);

	const isLocked = $derived(data.session.status !== 'scheduled');
	const scheduledAt = $derived.by(() => {
		const d = data.session.scheduled_at ? new Date(data.session.scheduled_at) : new Date();
		return {
			date: d.toISOString().slice(0, 10),
			time: d.toTimeString().slice(0, 5)
		};
	});

	let notes = $state(data.session.notes ?? '');
	let date = $state(scheduledAt.date);
	let time = $state(scheduledAt.time);

	async function handleSubmit() {
		const id = $page.params.id;
		if (!id) return;
		const scheduled_at = new Date(`${date}T${time}`).toISOString();
		await updateSession(id, { scheduled_at, notes });
		await goto(`/app/sessions/${id}`);
	}
</script>

<div class="flex flex-1 flex-col gap-4 p-4 pt-0">
	<div class="flex items-center gap-2">
		<Button href="/app/sessions/{sessionId}" variant="ghost" size="icon">
			<ChevronLeftIcon class="h-4 w-4" />
		</Button>
		<h1 class="text-2xl font-semibold">Edit Session</h1>
	</div>

	{#if isLocked}
		<Card>
			<CardContent class="pt-6">
				<p class="text-muted-foreground text-sm">
					Session in progress or completed — only notes can be edited.
				</p>
			</CardContent>
		</Card>
	{/if}

	<Card class="max-w-xl">
		<CardHeader>
			<CardTitle>Session details</CardTitle>
		</CardHeader>
		<CardContent class="space-y-4">
			{#if !isLocked}
				<div class="grid gap-4 sm:grid-cols-2">
					<div class="space-y-2">
						<Label for="date">Date</Label>
						<Input id="date" type="date" bind:value={date} disabled={isLocked} />
					</div>
					<div class="space-y-2">
						<Label for="time">Time</Label>
						<Input id="time" type="time" bind:value={time} disabled={isLocked} />
					</div>
				</div>
			{/if}
			<div class="space-y-2">
				<Label for="notes">Notes</Label>
				<Textarea id="notes" bind:value={notes} placeholder="Session notes..." rows={3} />
			</div>
			<div class="flex gap-2">
				<Button onclick={handleSubmit}>Save</Button>
				<Button href="/app/sessions/{sessionId}" variant="outline">Cancel</Button>
			</div>
		</CardContent>
	</Card>
</div>
