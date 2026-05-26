<script lang="ts">
	import { page } from '$app/stores';
	import AppSidebar from '$lib/components/app-sidebar.svelte';
	import UiTourRunner from '$lib/components/ui-tour-runner.svelte';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import DumbbellIcon from '@lucide/svelte/icons/dumbbell';

	let { children, data } = $props();

	const isOnboarding = $derived($page.url.pathname.startsWith('/app/onboarding'));
	const isRecord = $derived($page.url.pathname.endsWith('/record'));
</script>

{#if isOnboarding || isRecord}
	{@render children()}
{:else}
	<div class="min-h-dvh">
		<Sidebar.Provider>
			<UiTourRunner />
			<AppSidebar user={data.user} />
			<Sidebar.Inset class="min-h-dvh">
				<header
					class="sticky top-0 z-50 flex h-14 shrink-0 items-center gap-2 border-b px-3 md:h-16 md:px-4"
				>
					<Sidebar.Trigger class="-ms-0.5 shrink-0" />
				</header>
				<div class="w-full flex-1 p-4 md:mx-auto md:max-w-6xl md:px-4 md:py-6">
					{@render children()}
				</div>
			</Sidebar.Inset>
		</Sidebar.Provider>
	</div>
{/if}
