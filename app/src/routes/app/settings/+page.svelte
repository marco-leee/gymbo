<script lang="ts">
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Switch } from '$lib/components/ui/switch/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
</script>

<div class="flex flex-1 flex-col gap-4 p-4 pt-0">
	<h1 class="text-2xl font-semibold">Settings</h1>

	<div class="grid gap-4 md:grid-cols-2">
		<!-- App Preferences -->
		<Card>
			<CardHeader>
				<CardTitle>App Preferences</CardTitle>
				<CardDescription>Customize your app experience</CardDescription>
			</CardHeader>
			<CardContent class="space-y-4">
				<div class="flex items-center justify-between">
					<div class="space-y-0.5">
						<Label>Dark Mode</Label>
						<p class="text-muted-foreground text-sm">Toggle dark mode on/off</p>
					</div>
					<Switch />
				</div>
				<div class="space-y-2">
					<Label>Language</Label>
					<Select.Root type="single">
						<Select.Trigger class="w-full">Select language</Select.Trigger>
						<Select.Content>
							<Select.Item value="en">English</Select.Item>
							<Select.Item value="zh">中文</Select.Item>
						</Select.Content>
					</Select.Root>
				</div>
			</CardContent>
		</Card>

		<!-- Account Settings -->
		<Card>
			<CardHeader>
				<CardTitle>Account</CardTitle>
				<CardDescription>Manage your account settings</CardDescription>
			</CardHeader>
			<CardContent class="space-y-4">
				<div class="space-y-2">
					<Label>Email</Label>
					<Input type="email" value="trainer@example.com" disabled />
				</div>
				<div class="space-y-2">
					<Label>Password</Label>
					<Button variant="outline" class="w-full">Change Password</Button>
				</div>
			</CardContent>
		</Card>
	</div>

	<!-- Danger Zone -->
	<Card class="border-destructive">
		<CardHeader>
			<CardTitle class="text-destructive">Danger Zone</CardTitle>
			<CardDescription>Irreversible actions</CardDescription>
		</CardHeader>
		<CardContent>
			<Button variant="destructive">Delete Account</Button>
		</CardContent>
	</Card>
</div>
