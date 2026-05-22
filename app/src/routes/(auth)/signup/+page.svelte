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

	let name = $state('');
	let email = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	const redirectTo = $derived($page.url.searchParams.get('redirectTo') || '/app/sessions');

	async function signUpEmail(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		loading = true;
		const result = await authClient.signUp.email({
			name,
			email,
			password,
			callbackURL: redirectTo
		});
		loading = false;
		if (result.error) {
			error = result.error.message ?? 'Sign up failed';
			return;
		}
		await goto(redirectTo);
	}

	async function signInGoogle() {
		error = '';
		await authClient.signIn.social({
			provider: 'google',
			callbackURL: redirectTo
		});
	}
</script>

<svelte:head>
	<title>Sign up · GYMBO</title>
</svelte:head>

<Card>
	<CardHeader>
		<CardTitle>Create account</CardTitle>
		<CardDescription>Use your email or Google to get started.</CardDescription>
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

		{#if data.googleEnabled || data.githubEnabled}
			<div class="relative">
				<div class="absolute inset-0 flex items-center">
					<span class="w-full border-t"></span>
				</div>
				<div class="relative flex justify-center text-xs uppercase">
					<span class="bg-card text-muted-foreground px-2">Or</span>
				</div>
			</div>
			<div class="flex flex-col gap-2">
				<Button
					type="button"
					variant="outline"
					class="w-full"
					disabled={loading}
					onclick={signInGoogle}
				>
					Continue with Google
				</Button>
			</div>
		{/if}

		<p class="text-muted-foreground text-center text-sm">
			Already have an account?
			<a href="/login" class="text-primary underline-offset-4 hover:underline">Sign in</a>
		</p>
	</CardContent>
</Card>
