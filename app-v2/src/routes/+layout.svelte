<script lang="ts">
	import { QueryClientProvider } from '@tanstack/svelte-query';
	import { queryClient } from '$lib/query-client.js';
	import { ModeWatcher } from "mode-watcher";
	import './layout.css';

	let { children } = $props();
</script>

<svelte:head></svelte:head>
<ModeWatcher />
<QueryClientProvider client={queryClient}>
	{@render children()}
</QueryClientProvider>
