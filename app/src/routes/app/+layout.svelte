<script lang="ts">
	import AppSidebar from '$lib/components/app-sidebar.svelte';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import DumbbellIcon from '@lucide/svelte/icons/dumbbell';

	let { children, data } = $props();
</script>

<div class="app-root min-h-dvh">
	<Sidebar.Provider>
		<AppSidebar user={data.user} />
		<Sidebar.Inset class="min-h-dvh">
			<header
				class="sticky top-0 z-50 flex h-14 shrink-0 items-center gap-2 border-b px-3 md:h-16 md:px-4"
				style="border-color: var(--app-border); background: color-mix(in oklab, var(--app-surface) 92%, transparent); backdrop-filter: blur(8px);"
			>
				<Sidebar.Trigger class="-ms-0.5 shrink-0" />
				<Separator orientation="vertical" class="shrink-0 data-[orientation=vertical]:h-5 md:data-[orientation=vertical]:h-4" />
				<a
					href="/app/sessions"
					class="app-display flex min-w-0 flex-1 items-center gap-2 truncate text-lg tracking-wide md:text-xl"
					style="color: var(--app-text); text-decoration: none;"
				>
					<DumbbellIcon class="size-5 shrink-0 md:size-6" style="color: var(--app-accent);" aria-hidden="true" />
					<span class="truncate">GYMBO</span>
				</a>
			</header>
			<div class="w-full flex-1 px-3 py-4 md:mx-auto md:max-w-6xl md:px-4 md:py-6">
				{@render children()}
			</div>
		</Sidebar.Inset>
	</Sidebar.Provider>
</div>
