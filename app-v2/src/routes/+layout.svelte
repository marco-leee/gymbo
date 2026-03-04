<script lang="ts">
	import { onMount } from 'svelte';
	import { QueryClientProvider } from '@tanstack/svelte-query';
	import { queryClient } from '$lib/query-client.js';
	import { authStore } from '$lib/auth/index.js';
	import './layout.css';

	let { children } = $props();

	onMount(() => {
		authStore.refreshAuth();
	});
</script>

<svelte:head></svelte:head>
<QueryClientProvider client={queryClient}>
	{@render children()}
</QueryClientProvider>
