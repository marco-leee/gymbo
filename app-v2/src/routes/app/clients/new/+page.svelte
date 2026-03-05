<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import ChevronLeftIcon from '@lucide/svelte/icons/chevron-left';
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
		<CardContent class="space-y-4">
			<div class="grid gap-4 md:grid-cols-2">
				<div class="space-y-2">
					<Label for="name">Full Name *</Label>
					<Input id="name" placeholder="John Doe" />
				</div>
				<div class="space-y-2">
					<Label for="email">Email *</Label>
					<Input id="email" type="email" placeholder="john@example.com" />
				</div>
			</div>

			<div class="grid gap-4 md:grid-cols-2">
				<div class="space-y-2">
					<Label for="phone">Phone</Label>
					<Input id="phone" placeholder="+1 234 567 890" />
				</div>
				<div class="space-y-2">
					<Label for="dob">Date of Birth</Label>
					<Input id="dob" type="date" />
				</div>
			</div>

			<div class="grid gap-4 md:grid-cols-3">
				<div class="space-y-2">
					<Label for="gender">Gender</Label>
					<Select.Root type="single">
						<Select.Trigger class="w-full">Select</Select.Trigger>
						<Select.Content>
							<Select.Item value="male">Male</Select.Item>
							<Select.Item value="female">Female</Select.Item>
							<Select.Item value="other">Other</Select.Item>
						</Select.Content>
					</Select.Root>
				</div>
				<div class="space-y-2">
					<Label for="height">Height (cm)</Label>
					<Input id="height" type="number" placeholder="175" />
				</div>
				<div class="space-y-2">
					<Label for="weight">Weight (kg)</Label>
					<Input id="weight" type="number" placeholder="70" />
				</div>
			</div>

			<div class="space-y-2">
				<Label for="fitness">Fitness Level</Label>
				<Select.Root type="single">
					<Select.Trigger class="w-full">Select level</Select.Trigger>
					<Select.Content>
						<Select.Item value="beginner">Beginner</Select.Item>
						<Select.Item value="intermediate">Intermediate</Select.Item>
						<Select.Item value="advanced">Advanced</Select.Item>
					</Select.Content>
				</Select.Root>
			</div>

			<div class="space-y-2">
				<Label for="notes">Injuries / Notes</Label>
				<Textarea id="notes" placeholder="Any injuries or special considerations..." />
			</div>

			<div class="flex gap-2 pt-4">
				<Button>Create Client</Button>
				<Button href="/app/clients" variant="outline">Cancel</Button>
			</div>
		</CardContent>
	</Card>
</div>
