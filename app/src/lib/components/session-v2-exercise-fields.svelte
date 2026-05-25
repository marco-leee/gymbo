<script lang="ts">
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { exerciseTypeLabel } from '$lib/api/sessions';
	import {
		CUSTOM_PRESET_VALUE,
		applyCatalogPreset,
		catalogEntryLabel,
		findCatalogEntry,
		EXERCISE_CATALOG,
		type SessionExerciseFormRow
	} from '$lib/exercises/catalog';

	let {
		row = $bindable(),
		idPrefix
	}: {
		row: SessionExerciseFormRow;
		idPrefix: string;
	} = $props();

	const presetEntry = $derived(findCatalogEntry(row.catalogKey));
	const isCustomPreset = $derived(row.catalogKey === CUSTOM_PRESET_VALUE);
	/** Preset row: lock name. Type/measurement only when the catalog entry defines them. */
	const lockName = $derived(!isCustomPreset);
	const lockType = $derived(!isCustomPreset && presetEntry?.type !== undefined);
	const lockMeasurement = $derived(!isCustomPreset && presetEntry?.measurement !== undefined);

	function onPresetPick(value: string | undefined) {
		applyCatalogPreset(row, value ?? CUSTOM_PRESET_VALUE);
	}

	const presetTriggerLabel = $derived(
		isCustomPreset ? 'Custom' : presetEntry ? catalogEntryLabel(presetEntry) : row.catalogKey
	);
</script>

<div class="space-y-4">
	<div class="space-y-2">
		<Label for={`${idPrefix}-preset`}>Exercise preset</Label>
		<Select.Root type="single" value={row.catalogKey} onValueChange={(v) => onPresetPick(v)}>
			<Select.Trigger class="min-h-11 w-full" id={`${idPrefix}-preset`}>
				{presetTriggerLabel}
			</Select.Trigger>
			<Select.Content>
				{#each EXERCISE_CATALOG as entry (entry.key)}
					<Select.Item value={entry.key}>{catalogEntryLabel(entry)}</Select.Item>
				{/each}
				<!-- <Select.Item value={CUSTOM_PRESET_VALUE}>Custom</Select.Item> -->
			</Select.Content>
		</Select.Root>
	</div>

	{#if lockName}
		<div class="space-y-2">
			<Label>Name</Label>
			<Input type="text" value={row.name} disabled class="min-h-11" />
		</div>
	{:else}
		<div class="space-y-2">
			<Label for={`${idPrefix}-name`}>Name *</Label>
			<Input
				id={`${idPrefix}-name`}
				type="text"
				bind:value={row.name}
				placeholder="e.g. Bench press"
				class="min-h-11"
			/>
		</div>
	{/if}

	<div class="grid gap-4 sm:grid-cols-2">
		<div class="space-y-2">
			<Label for={`${idPrefix}-type`}>Type</Label>
			<Select.Root
				type="single"
				value={row.type}
				disabled={lockType}
				onValueChange={(v) => (row.type = (v ?? 'strength') as SessionExerciseFormRow['type'])}
			>
				<Select.Trigger class="min-h-11 w-full" id={`${idPrefix}-type`}>
					<span>{exerciseTypeLabel(row.type)}</span>
				</Select.Trigger>
				<Select.Content>
					<Select.Item value="strength">Strength</Select.Item>
					<Select.Item value="cardio">Cardio</Select.Item>
					<Select.Item value="flexibility">Flexibility</Select.Item>
					<Select.Item value="warm_up">Warm up</Select.Item>
				</Select.Content>
			</Select.Root>
		</div>
		<div class="space-y-2">
			<Label for={`${idPrefix}-meas`}>Measurement</Label>
			<Select.Root
				type="single"
				value={row.measurement}
				disabled={lockMeasurement}
				onValueChange={(v) => (row.measurement = (v ?? 'reps') as SessionExerciseFormRow['measurement'])}
			>
				<Select.Trigger class="min-h-11 w-full" id={`${idPrefix}-meas`}>
					<span>{row.measurement === 'reps' ? 'Reps' : 'Duration'}</span>
				</Select.Trigger>
				<Select.Content>
					<Select.Item value="reps">Reps</Select.Item>
					<Select.Item value="duration">Duration</Select.Item>
				</Select.Content>
			</Select.Root>
		</div>
	</div>

	{#if row.measurement === 'reps'}
		<div class="grid gap-4 sm:grid-cols-2">
			<div class="space-y-2">
				<Label for={`${idPrefix}-treps`}>Target Reps</Label>
				<Input
					id={`${idPrefix}-treps`}
					type="number"
					min="0"
					bind:value={row.target_reps}
					placeholder="e.g. 12"
					class="min-h-11"
				/>
			</div>
			<div class="space-y-2">
				<Label for={`${idPrefix}-tw`}>Target Weight (kg)</Label>
				<Input
					id={`${idPrefix}-tw`}
					type="number"
					min="0"
					step="0.5"
					bind:value={row.target_weight_kg}
					placeholder="e.g. 60"
					class="min-h-11"
				/>
			</div>
		</div>
	{:else}
		<div class="grid gap-4 sm:grid-cols-2">
			<div class="space-y-2">
				<Label for={`${idPrefix}-tdur`}>Target Duration (sec)</Label>
				<Input
					id={`${idPrefix}-tdur`}
					type="number"
					min="0"
					bind:value={row.target_duration}
					placeholder="e.g. 60"
					class="min-h-11"
				/>
			</div>
			<div class="space-y-2">
				<Label for={`${idPrefix}-tw2`}>Target Weight (kg)</Label>
				<Input
					id={`${idPrefix}-tw2`}
					type="number"
					min="0"
					step="0.5"
					bind:value={row.target_weight_kg}
					placeholder="e.g. 0"
					class="min-h-11"
				/>
			</div>
		</div>
	{/if}

	<div class="grid gap-4 sm:grid-cols-2">
		<div class="space-y-2">
			<Label for={`${idPrefix}-sets`}>Number of Sets</Label>
			<Input
				id={`${idPrefix}-sets`}
				type="number"
				min="0"
				bind:value={row.target_sets}
				placeholder="Optional"
				class="min-h-11"
			/>
		</div>
		<div class="space-y-2">
			<Label for={`${idPrefix}-rest`}>Rest (sec)</Label>
			<Input
				id={`${idPrefix}-rest`}
				type="number"
				min="0"
				bind:value={row.rest_seconds}
				class="min-h-11"
			/>
		</div>
	</div>

	<div class="space-y-2">
		<Label for={`${idPrefix}-notes`}>Exercise notes</Label>
		<Textarea
			id={`${idPrefix}-notes`}
			bind:value={row.notes}
			rows={3}
			placeholder="Optional: cues, equipment, substitutions…"
			class="min-h-[5rem]"
		/>
	</div>
</div>
