<script lang="ts">
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import CalendarIcon from '@lucide/svelte/icons/calendar';
	import UserIcon from '@lucide/svelte/icons/user';
	import VideoIcon from '@lucide/svelte/icons/video';
	import ActivityIcon from '@lucide/svelte/icons/activity';
</script>

<div class="flex flex-1 flex-col gap-4 p-4 pt-0">
	<h1 class="text-2xl font-semibold">Dashboard</h1>

	<!-- Quick Stats -->
	<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
		<Card>
			<CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
				<CardTitle class="text-sm font-medium">Today's Sessions</CardTitle>
				<CalendarIcon class="text-muted-foreground h-4 w-4" />
			</CardHeader>
			<CardContent>
				<div class="text-2xl font-bold">0</div>
				<p class="text-muted-foreground text-xs">Scheduled for today</p>
			</CardContent>
		</Card>
		<Card>
			<CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
				<CardTitle class="text-sm font-medium">Active Clients</CardTitle>
				<UserIcon class="text-muted-foreground h-4 w-4" />
			</CardHeader>
			<CardContent>
				<div class="text-2xl font-bold">0</div>
				<p class="text-muted-foreground text-xs">Total clients</p>
			</CardContent>
		</Card>
		<Card>
			<CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
				<CardTitle class="text-sm font-medium">Pending Analysis</CardTitle>
				<VideoIcon class="text-muted-foreground h-4 w-4" />
			</CardHeader>
			<CardContent>
				<div class="text-2xl font-bold">0</div>
				<p class="text-muted-foreground text-xs">Videos processing</p>
			</CardContent>
		</Card>
		<Card>
			<CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
				<CardTitle class="text-sm font-medium">Recent Activity</CardTitle>
				<ActivityIcon class="text-muted-foreground h-4 w-4" />
			</CardHeader>
			<CardContent>
				<div class="text-2xl font-bold">0</div>
				<p class="text-muted-foreground text-xs">This week</p>
			</CardContent>
		</Card>
	</div>

	<div class="grid gap-4 md:grid-cols-2">
		<!-- Today's Schedule -->
		<Card class="col-span-1">
			<CardHeader>
				<CardTitle>Today's Schedule</CardTitle>
				<CardDescription>Your sessions for today</CardDescription>
			</CardHeader>
			<CardContent>
				<div class="text-muted-foreground py-8 text-center text-sm">
					No sessions scheduled for today.
				</div>
			</CardContent>
		</Card>

		<!-- Recent Activity -->
		<Card class="col-span-1">
			<CardHeader>
				<CardTitle>Recent Activity</CardTitle>
				<CardDescription>Latest updates and completions</CardDescription>
			</CardHeader>
			<CardContent>
				<div class="text-muted-foreground py-8 text-center text-sm">
					No recent activity to show.
				</div>
			</CardContent>
		</Card>
	</div>

	<!-- Quick Actions -->
	<div class="flex gap-2">
		<Button href="/app/sessions/new">New Session</Button>
		<Button href="/app/clients/new" variant="outline">Add Client</Button>
	</div>
</div>
