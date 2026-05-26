<script lang="ts">
	import { goto } from '$app/navigation';
	import { tick } from 'svelte';
	import { createMutation } from '@tanstack/svelte-query';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import ChevronLeftIcon from '@lucide/svelte/icons/chevron-left';
	import { createClient } from '$lib/api/clients';
	import { queryClient } from '$lib/query-client';
	import { advanceTourAfterClientCreated, resumeTourForPath } from '$lib/ui-tour';

	type NewClientForm = {
		email: string;
		full_name: string;
		first_name: string;
		last_name: string;
		gender: string;
		height_cm: number;
		weight_kg: number;
	};

	let formData = $state<NewClientForm>({
		email: '',
		full_name: '',
		first_name: '',
		last_name: '',
		gender: '',
		height_cm: 0,
		weight_kg: 0
	});

	let errors = $state<Partial<Record<keyof NewClientForm, string>>>({});

	const clientMutation = createMutation(() => ({
		mutationFn: createClient,
		onSuccess: async () => {
			queryClient.invalidateQueries({ queryKey: ['clients'] });
			advanceTourAfterClientCreated();
			await goto('/app/clients');
			await tick();
			await resumeTourForPath('/app/clients');
		},
		onError: (error: Error) => {
			console.error('Failed to create client:', error);
		}
	}));

	function validate(): boolean {
		errors = {};
		if (!formData.full_name.trim()) {
			errors.full_name = 'Full name is required';
		}
		if (!formData.email.trim()) {
			errors.email = 'Email is required';
		} else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
			errors.email = 'Invalid email format';
		}
		return Object.keys(errors).length === 0;
	}

	function handleSubmit(e: Event) {
		e.preventDefault();
		if (!validate()) return;

		const [first = '', ...rest] = formData.full_name.trim().split(' ');
		clientMutation.mutate({
			...formData,
			first_name: first,
			last_name: rest.join(' ')
		});
	}
</script>

<div class="flex flex-col gap-6">
	<div class="flex flex-wrap items-center gap-2">
		<Button href="/app/clients" variant="ghost" size="icon" class="app-ghost min-h-11 min-w-11">
			<ChevronLeftIcon class="h-5 w-5" aria-hidden="true" />
			<span class="sr-only">Back to clients</span>
		</Button>
		<h1 class="app-display text-3xl md:text-4xl" style="color: var(--app-text);">New client</h1>
	</div>
	<Card.Root class="mx-auto w-full" data-tour="clients-form">
		<Card.Header>
			<Card.Title>Client information</Card.Title>
			<Card.Description>Enter details for your new client.</Card.Description>
		</Card.Header>

		<form onsubmit={handleSubmit}>
			<Card.Content class="space-y-4">
				<div class="grid gap-4 md:grid-cols-2">
					<div class="space-y-2">
						<Label for="name">Full name *</Label>
						<Input
							id="name"
							class="min-h-11 bg-background"
							placeholder="John Doe"
							bind:value={formData.full_name}
							aria-invalid={errors.full_name ? 'true' : undefined}
						/>
						{#if errors.full_name}
							<p class="text-sm text-red-400">{errors.full_name}</p>
						{/if}
					</div>
					<div class="space-y-2">
						<Label for="email">Email *</Label>
						<Input
							id="email"
							type="email"
							class="min-h-11 bg-background"
							placeholder="john@example.com"
							bind:value={formData.email}
							aria-invalid={errors.email ? 'true' : undefined}
						/>
						{#if errors.email}
							<p class="text-sm text-red-400">{errors.email}</p>
						{/if}
					</div>
				</div>

				<div class="grid gap-4 md:grid-cols-3">
					<div class="space-y-2">
						<Label for="gender">Gender</Label>
						<Select.Root type="single" value={formData.gender} onValueChange={(v) => (formData.gender = v)}>
							<Select.Trigger class="min-h-11 w-full bg-background">
								<span class={formData.gender ? '' : 'text-muted-foreground'}>
									{formData.gender ? formData.gender : 'Select'}
								</span>
							</Select.Trigger>
							<Select.Content>
								<Select.Item value="male">Male</Select.Item>
								<Select.Item value="female">Female</Select.Item>
								<Select.Item value="other">Other</Select.Item>
							</Select.Content>
						</Select.Root>
					</div>
					<div class="space-y-2">
						<Label for="height">Height (cm)</Label>
						<Input
							id="height"
							type="number"
							class="min-h-11 bg-background"
							placeholder="175"
							min="0"
							bind:value={formData.height_cm}
						/>
					</div>
					<div class="space-y-2">
						<Label for="weight">Weight (kg)</Label>
						<Input
							id="weight"
							type="number"
							class="min-h-11 bg-background"
							placeholder="70"
							min="0"
							bind:value={formData.weight_kg}
						/>
					</div>
				</div>

				<div class="space-y-2">
					<Label for="notes">Injuries / notes</Label>
					<Textarea
						id="notes"
						class="min-h-[100px] bg-background"
						placeholder="Any injuries or special considerations…"
					/>
				</div>

				{#if clientMutation.isError}
					<p class="text-sm text-red-400">Failed to create client: {clientMutation.error.message}</p>
				{/if}
			</Card.Content>

			<Card.Footer class="flex flex-wrap gap-3 pt-4">
				<Button type="submit" class="min-h-11" disabled={clientMutation.isPending}>
					{clientMutation.isPending ? 'Creating…' : 'Create client'}
				</Button>
				<Button href="/app/clients" variant="outline" type="button" class="app-outline min-h-11">
					Cancel
				</Button>
			</Card.Footer>
		</form>
	</Card.Root>
</div>
