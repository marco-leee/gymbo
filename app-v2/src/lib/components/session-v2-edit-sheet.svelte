<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import * as Sheet from '$lib/components/ui/sheet/index.js';
	import type { Session } from '$lib/api/sessions';
	import { updateSession } from '$lib/api/sessions';

	let {
		open = $bindable(false),
		sessionId,
		session,
		onSaved
	}: {
		open: boolean;
		sessionId: string;
		session: Session;
		onSaved?: () => void | Promise<void>;
	} = $props();

	const isLocked = $derived(session.status !== 'scheduled');

	let notes = $state('');
	let date = $state('');
	let time = $state('');
	let saving = $state(false);
	let dirty = $state(false);

	$effect(() => {
		if (!open) return;
		const d = session.scheduled_at ? new Date(session.scheduled_at) : new Date();
		date = d.toISOString().slice(0, 10);
		time = d.toTimeString().slice(0, 5);
		notes = session.notes ?? '';
		dirty = false;
	});

	function markDirty() {
		dirty = true;
	}

	function cancel() {
		if (dirty && !confirm('Discard unsaved changes?')) return;
		dirty = false;
		open = false;
	}

	async function handleSubmit() {
		saving = true;
		try {
			const scheduled_at = new Date(`${date}T${time}`).toISOString();
			await updateSession(sessionId, { scheduled_at, notes });
			dirty = false;
			await onSaved?.();
			open = false;
		} catch (e) {
			alert(e instanceof Error ? e.message : 'Failed to save');
		} finally {
			saving = false;
		}
	}
</script>

<Sheet.Root bind:open>
	<Sheet.Content side="right" class="flex w-full flex-col sm:max-w-md">
		<Sheet.Header>
			<Sheet.Title>Edit session</Sheet.Title>
			<Sheet.Description>
				{#if isLocked}
					Session in progress or completed — only notes can be edited.
				{:else}
					Update schedule and notes.
				{/if}
			</Sheet.Description>
		</Sheet.Header>
		<div class="flex flex-1 flex-col gap-4 overflow-y-auto py-4">
			{#if !isLocked}
				<div class="grid gap-4 sm:grid-cols-2">
					<div class="space-y-2">
						<Label for="v2-edit-date">Date</Label>
						<Input id="v2-edit-date" type="date" bind:value={date} oninput={markDirty} />
					</div>
					<div class="space-y-2">
						<Label for="v2-edit-time">Time</Label>
						<Input id="v2-edit-time" type="time" bind:value={time} oninput={markDirty} />
					</div>
				</div>
			{/if}
			<div class="space-y-2">
				<Label for="v2-edit-notes">Notes</Label>
				<Textarea
					id="v2-edit-notes"
					bind:value={notes}
					placeholder="Session notes..."
					rows={4}
					oninput={markDirty}
				/>
			</div>
		</div>
		<Sheet.Footer class="gap-2 sm:justify-end">
			<Button type="button" variant="outline" onclick={cancel}>Cancel</Button>
			<Button type="button" onclick={handleSubmit} disabled={saving}>
				{saving ? 'Saving…' : 'Save'}
			</Button>
		</Sheet.Footer>
	</Sheet.Content>
</Sheet.Root>
