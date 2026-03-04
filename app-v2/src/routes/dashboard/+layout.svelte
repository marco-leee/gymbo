<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { authStore } from '$lib/auth/index.js';
	import AppSidebar from '$lib/components/app-sidebar.svelte';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';

	let { children } = $props();

	let auth = $state({ isLoading: true, isAuthenticated: false });

	onMount(() => {
		const unsub = authStore.subscribe((s) => {
			auth = { isLoading: s.isLoading, isAuthenticated: s.isAuthenticated };
			if (!s.isLoading && !s.isAuthenticated) goto('/login');
		});
		return unsub;
	});
</script>

{#if auth.isLoading}
	<div class="flex min-h-screen items-center justify-center">
		<p class="text-muted-foreground">Loading…</p>
	</div>
{:else if auth.isAuthenticated}
	<Sidebar.Provider>
		<AppSidebar />
		<Sidebar.Inset>
			<header class="flex h-16 shrink-0 items-center gap-2">
				<div class="flex items-center gap-2 px-4">
					<Sidebar.Trigger class="-ms-1" />
					<Separator orientation="vertical" class="me-2 data-[orientation=vertical]:h-4" />
				</div>
			</header>
			{@render children()}
		</Sidebar.Inset>
	</Sidebar.Provider>
{/if}
