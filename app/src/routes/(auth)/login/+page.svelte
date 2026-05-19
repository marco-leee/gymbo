<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
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

	let email = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	const redirectTo = $derived($page.url.searchParams.get('redirectTo') || '/app/sessions');
	/** Absolute URL required for OAuth callbacks; must not use server-only env on the client. */
	// const callbackURL = $derived(new URL(redirectTo, $page.url.origin).href);
	const callbackURL = `http://localhost:5173/${redirectTo}`

	async function signInEmail(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		loading = true;
		const result = await authClient.signIn.email({
			email,
			password,
			callbackURL
		});
		loading = false;
		if (result.error) {
			error = result.error.message ?? 'Sign in failed';
			return;
		}
		await goto(redirectTo);
	}

	async function signInGoogle() {
		error = '';
		await authClient.signIn.social({
			provider: 'google',
			callbackURL: `http://localhost:5173${redirectTo}`
		});
	}
</script>

<svelte:head>
	<title>Sign in · GYMBO</title>
</svelte:head>

<Card>
	<CardHeader>
		<CardTitle>Sign in</CardTitle>
		<CardDescription>Use your email or Google to continue.</CardDescription>
	</CardHeader>
	<CardContent class="space-y-4">
		{#if error}
			<p class="text-destructive text-sm" role="alert">{error}</p>
		{/if}

		<form class="space-y-4" onsubmit={signInEmail}>
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
					autocomplete="current-password"
					required
					bind:value={password}
					disabled={loading}
				/>
			</div>
			<Button type="submit" class="w-full" disabled={loading}>
				{loading ? 'Signing in…' : 'Sign in'}
			</Button>
		</form>

		{#if data.googleEnabled}
			<div class="relative">
				<div class="absolute inset-0 flex items-center">
					<span class="w-full border-t"></span>
				</div>
				<div class="relative flex justify-center text-xs uppercase">
					<span class="bg-card text-muted-foreground px-2">Or</span>
				</div>
			</div>
			<Button type="button" variant="outline" class="w-full" disabled={loading} onclick={signInGoogle}>
				Continue with Google
			</Button>
		{/if}

		<p class="text-muted-foreground text-center text-sm">
			No account?
			<a href="/signup" class="text-primary underline-offset-4 hover:underline">Sign up</a>
		</p>
	</CardContent>
</Card>
