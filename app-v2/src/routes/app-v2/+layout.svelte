<script lang="ts">
	import './session-v2.css';
	import { page } from '$app/stores';
	import { Button } from '$lib/components/ui/button/index.js';
	import DumbbellIcon from '@lucide/svelte/icons/dumbbell';
	import LayoutDashboardIcon from '@lucide/svelte/icons/layout-dashboard';

	let { children } = $props();

	const path = $derived($page.url.pathname);
</script>

<div class="app-v2-root min-h-dvh">
	<header
		class="sticky top-0 z-50 flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3"
		style="border-color: var(--app-v2-border); background: color-mix(in oklab, var(--app-v2-surface) 92%, transparent); backdrop-filter: blur(8px);"
	>
		<div class="flex items-center gap-3">
			<a
				href="/app-v2/sessions"
				class="app-v2-display flex items-center gap-2 text-xl tracking-wide"
				style="color: var(--app-v2-text); text-decoration: none;"
			>
				<DumbbellIcon class="size-6" style="color: var(--app-v2-accent);" aria-hidden="true" />
				GYMBO
			</a>
			<span class="text-xs font-medium uppercase tracking-widest" style="color: var(--app-v2-muted);">
				App v2
			</span>
		</div>
		<nav class="flex flex-wrap items-center gap-2" aria-label="App v2">
			<Button
				href="/app-v2/sessions"
				variant="ghost"
				size="sm"
				class="app-v2-ghost min-h-10 {path.startsWith('/app-v2/sessions') ? 'bg-white/10 text-white' : ''}"
			>
				Sessions
			</Button>
			<Button href="/app/dashboard" variant="ghost" size="sm" class="app-v2-ghost min-h-10 gap-1">
				<LayoutDashboardIcon class="size-4" aria-hidden="true" />
				Classic app
			</Button>
		</nav>
	</header>
	<div class="mx-auto w-full max-w-6xl px-4 py-6">
		{@render children()}
	</div>
</div>
