<script lang="ts">
	import { QueryClientProvider } from "@tanstack/svelte-query";
	import { queryClient } from "$lib/query-client.js";
	import { ModeWatcher } from "mode-watcher";
	import "./layout.css";

	let { children } = $props();
	import posthog from "posthog-js";
	import { browser } from "$app/environment";
	import { onMount } from "svelte";

	export const load = async () => {
		
		return;
	};
	
	onMount(() => {
		if (browser) {
			posthog.init("phc_qKaRhkRKcRP6oyW9udbBeSv84SG4Z22Ndnm7NGNuP6KH", {
				api_host: "https://us.i.posthog.com",
				defaults: "2026-01-30",
			});
		}
	})
</script>

<svelte:head></svelte:head>
<ModeWatcher />
<QueryClientProvider client={queryClient}>
	{@render children()}
</QueryClientProvider>
