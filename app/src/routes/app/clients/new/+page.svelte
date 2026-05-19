<script lang="ts">
	import { goto } from '$app/navigation';
	import { createMutation } from '@tanstack/svelte-query';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import ChevronLeftIcon from '@lucide/svelte/icons/chevron-left';
	import { createClient } from '$lib/api/clients';
	import { queryClient } from '$lib/query-client';
	import type { CreateClientInput } from '$lib/services/models/client';

	let formData = $state<CreateClientInput>({
		email: '',
		full_name: '',
		first_name: '',
		last_name: '',
		gender: '',
		height_cm: 0,
		weight_kg: 0
	});

	let errors = $state<Partial<Record<keyof CreateClientInput, string>>>({});

	const clientMutation = createMutation(() => ({
		mutationFn: createClient,
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ['clients'] });
			goto('/app/clients');
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

<div class="flex flex-1 flex-col gap-4 p-4 pt-0">
	<div class="flex items-center gap-2">
		<Button href="/app/clients" variant="ghost" size="icon">
			<ChevronLeftIcon class="h-4 w-4" />
		</Button>
		<h1 class="text-2xl font-semibold">New Client</h1>
	</div>

	<Card class="mx-auto max-w-2xl">
		<CardHeader>
			<CardTitle>Client Information</CardTitle>
			<CardDescription>Enter the details for your new client</CardDescription>
		</CardHeader>
		<CardContent>
			<form onsubmit={handleSubmit} class="space-y-4">
				<div class="grid gap-4 md:grid-cols-2">
					<div class="space-y-2">
						<Label for="name">Full Name *</Label>
						<Input
							id="name"
							placeholder="John Doe"
							bind:value={formData.full_name}
							aria-invalid={errors.full_name ? 'true' : undefined}
						/>
						{#if errors.full_name}
							<p class="text-destructive text-sm">{errors.full_name}</p>
						{/if}
					</div>
					<div class="space-y-2">
						<Label for="email">Email *</Label>
						<Input
							id="email"
							type="email"
							placeholder="john@example.com"
							bind:value={formData.email}
							aria-invalid={errors.email ? 'true' : undefined}
						/>
						{#if errors.email}
							<p class="text-destructive text-sm">{errors.email}</p>
						{/if}
					</div>
				</div>

				<div class="grid gap-4 md:grid-cols-3">
					<div class="space-y-2">
						<Label for="gender">Gender</Label>
						<Select.Root
							type="single"
							value={formData.gender}
							onValueChange={(v) => formData.gender = v}
						>
							<Select.Trigger class="w-full">
								{formData.gender ? formData.gender : 'Select'}
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
							placeholder="70"
							min="0"
							bind:value={formData.weight_kg}
						/>
					</div>
				</div>

				<div class="space-y-2">
					<Label for="notes">Injuries / Notes</Label>
					<Textarea id="notes" placeholder="Any injuries or special considerations..." />
				</div>

				{#if clientMutation.isError}
					<p class="text-destructive text-sm">
						Failed to create client: {clientMutation.error.message}
					</p>
				{/if}

				<div class="flex gap-2 pt-4">
					<Button type="submit" disabled={clientMutation.isPending}>
						{clientMutation.isPending ? 'Creating...' : 'Create Client'}
					</Button>
					<Button href="/app/clients" variant="outline" type="button">Cancel</Button>
				</div>
			</form>
		</CardContent>
	</Card>
</div>
