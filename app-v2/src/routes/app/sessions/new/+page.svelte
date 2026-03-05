<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import ChevronLeftIcon from '@lucide/svelte/icons/chevron-left';
	import UserIcon from '@lucide/svelte/icons/user';
</script>

<div class="flex flex-1 flex-col gap-4 p-4 pt-0">
	<div class="flex items-center gap-2">
		<Button href="/app/sessions" variant="ghost" size="icon">
			<ChevronLeftIcon class="h-4 w-4" />
		</Button>
		<h1 class="text-2xl font-semibold">New Session</h1>
	</div>

	<Card class="mx-auto max-w-2xl">
		<CardHeader>
			<CardTitle>Session Information</CardTitle>
			<CardDescription>Set up a new training session</CardDescription>
		</CardHeader>
		<CardContent class="space-y-4">
			<div class="space-y-2">
				<Label for="client">Client *</Label>
				<Select.Root type="single">
					<Select.Trigger class="w-full">
						<UserIcon class="mr-2 h-4 w-4" />
						Select client
					</Select.Trigger>
					<Select.Content>
						<Select.Item value="client1">Client One</Select.Item>
						<Select.Item value="client2">Client Two</Select.Item>
					</Select.Content>
				</Select.Root>
			</div>

			<div class="grid gap-4 md:grid-cols-2">
				<div class="space-y-2">
					<Label for="date">Date *</Label>
					<Input id="date" type="date" />
				</div>
				<div class="space-y-2">
					<Label for="time">Time *</Label>
					<Input id="time" type="time" />
				</div>
			</div>

			<div class="space-y-2">
				<Label for="notes">Session Notes</Label>
				<Textarea id="notes" placeholder="Any notes for this session..." />
			</div>

			<div class="border-t pt-4">
				<h3 class="mb-4 font-medium">Exercises</h3>
				<div class="rounded-md border bg-muted/50 p-8 text-center">
					<p class="text-muted-foreground text-sm">No exercises added yet.</p>
					<Button variant="outline" class="mt-2">Add Exercise</Button>
				</div>
			</div>

			<div class="flex gap-2 pt-4">
				<Button>Create Session</Button>
				<Button href="/app/sessions" variant="outline">Cancel</Button>
			</div>
		</CardContent>
	</Card>
</div>
