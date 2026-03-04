<script lang="ts">
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/auth/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';

	let email = $state('');
	let error = $state<string | null>(null);
	let loading = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = null;
		const trimmed = email.trim();
		if (!trimmed) {
			error = 'Please enter your email';
			return;
		}
		loading = true;
		console.log(trimmed)
		try {
			await authStore.login(trimmed, 'admin', (path) => goto(path));
		} catch (err) {
			console.error(err);
			error = err instanceof Error ? err.message : 'Login failed';
		} finally {
			loading = false;
		}
	}
</script>

<div class="flex min-h-screen items-center justify-center bg-muted/30 p-4">
	<div class="w-full max-w-sm rounded-lg border bg-card p-6 shadow-sm">
		<h1 class="mb-6 text-center text-2xl font-semibold">Login</h1>
		<form onsubmit={handleSubmit} class="space-y-4">
			<div>
				<label for="email" class="mb-1.5 block text-sm font-medium">Email</label>
				<Input
					id="email"
					type="email"
					bind:value={email}
					placeholder="you@example.com"
					disabled={loading}
					class="w-full"
					autocomplete="email"
				/>
			</div>
			{#if error}
				<p class="text-sm text-destructive">{error}</p>
			{/if}
			<Button type="submit" class="w-full" disabled={loading}>
				{loading ? 'Signing in…' : 'Continue'}
			</Button>
		</form>
	</div>
</div>
