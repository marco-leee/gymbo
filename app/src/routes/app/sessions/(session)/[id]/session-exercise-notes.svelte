<script lang="ts">
	import { invalidateAll } from '$app/navigation';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import { updateSessionExerciseNotes } from '$lib/api/sessions';

	let {
		sessionId,
		exerciseId,
		notes,
		canEdit
	}: {
		sessionId: string;
		exerciseId: string;
		notes?: string | undefined;
		canEdit: boolean;
	} = $props();

	let draft = $state('');
	let saving = $state(false);

	$effect(() => {
		draft = notes ?? '';
	});

	const dirty = $derived(draft.trim() !== (notes ?? '').trim());

	async function saveNotes() {
		saving = true;
		try {
			const next = draft.trim().length === 0 ? null : draft.trim();
			await updateSessionExerciseNotes(sessionId, exerciseId, next);
			await invalidateAll();
		} catch (e) {
			alert(e instanceof Error ? e.message : 'Failed to save notes');
		} finally {
			saving = false;
		}
	}
</script>

<div class="space-y-2">
	<Label
		for="ex-notes-{exerciseId}"
		class="text-xs font-semibold uppercase tracking-wider"
		style="color: var(--app-muted);"
	>
		Exercise notes
	</Label>
	{#if canEdit}
		<Textarea
			id="ex-notes-{exerciseId}"
			bind:value={draft}
			rows={3}
			placeholder="Coaching cues, equipment, substitutions…"
			class="min-h-[5rem]"
			style="color: var(--app-text);"
		/>
		<Button
			type="button"
			size="sm"
			variant="outline"
			class="min-h-9 app-outline"
			disabled={saving || !dirty}
			onclick={saveNotes}
		>
			{saving ? 'Saving…' : 'Save notes'}
		</Button>
	{:else if notes?.trim()}
		<p class="whitespace-pre-wrap text-sm leading-relaxed" style="color: var(--app-muted);">{notes}</p>
	{/if}
</div>
