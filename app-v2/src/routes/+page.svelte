<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { authStore } from '$lib/auth/index.js';

	onMount(() => {
		const unsub = authStore.subscribe((state) => {
			if (state.isLoading) return;
			if (state.isAuthenticated) goto('/dashboard');
			else goto('/login');
		});
		return unsub;
	});
</script>

<div class="flex min-h-screen items-center justify-center">
	<p class="text-muted-foreground">Redirecting…</p>
</div>
