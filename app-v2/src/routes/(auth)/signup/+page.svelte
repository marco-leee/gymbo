<script lang="ts">
	import { goto } from '$app/navigation';
	import { authClient } from '$lib/auth-client';
	import { Button } from '$lib/components/ui/button/index.js';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';

	let { data } = $props();

	let name = $state('');
	let email = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	async function signUpEmail(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		loading = true;
		const result = await authClient.signUp.email({
			name,
			email,
			password,
			callbackURL: '/app-v2/sessions'
		});
		loading = false;
		if (result.error) {
			error = result.error.message ?? 'Sign up failed';
			return;
		}
		await goto('/app-v2/sessions');
	}

	async function signInGithub() {
		error = '';
		await authClient.signIn.social({
			provider: 'github',
			callbackURL: '/app-v2/sessions'
		});
	}
</script>

<svelte:head>
	<title>Sign up · GYMBO</title>
</svelte:head>

<Card>
	<CardHeader>
		<CardTitle>Create account</CardTitle>
		<CardDescription>Start tracking sessions with GYMBO.</CardDescription>
	</CardHeader>
	<CardContent class="space-y-4">
		{#if error}
			<p class="text-destructive text-sm" role="alert">{error}</p>
		{/if}

		<form class="space-y-4" onsubmit={signUpEmail}>
			<div class="space-y-2">
				<Label for="name">Name</Label>
				<Input
					id="name"
					type="text"
					autocomplete="name"
					required
					bind:value={name}
					disabled={loading}
				/>
			</div>
			<div class="space-y-2">
				<Label for="email">Email</Label>
				<Input
					id="email"
					type="email"
					autocomplete="email"
					required
					bind:value={email}
					disabled={loading}
				/>
			</div>
			<div class="space-y-2">
				<Label for="password">Password</Label>
				<Input
					id="password"
					type="password"
					autocomplete="new-password"
					required
					minlength={8}
					bind:value={password}
					disabled={loading}
				/>
			</div>
			<Button type="submit" class="w-full" disabled={loading}>
				{loading ? 'Creating account…' : 'Sign up'}
			</Button>
		</form>

		{#if data.githubEnabled}
			<div class="relative">
				<div class="absolute inset-0 flex items-center">
					<span class="w-full border-t"></span>
				</div>
				<div class="relative flex justify-center text-xs uppercase">
					<span class="bg-card text-muted-foreground px-2">Or</span>
				</div>
			</div>
			<Button type="button" variant="outline" class="w-full" disabled={loading} onclick={signInGithub}>
				Continue with GitHub
			</Button>
		{/if}

		<p class="text-muted-foreground text-center text-sm">
			Already have an account?
			<a href="/login" class="text-primary underline-offset-4 hover:underline">Sign in</a>
		</p>
	</CardContent>
</Card>
