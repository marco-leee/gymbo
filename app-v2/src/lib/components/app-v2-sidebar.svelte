<script lang="ts">
	import { page } from '$app/stores';
	import NavMain from './nav-main.svelte';
	import NavUser from './nav-user.svelte';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import DumbbellIcon from '@lucide/svelte/icons/dumbbell';
	import CalendarIcon from '@lucide/svelte/icons/calendar';
	import UserIcon from '@lucide/svelte/icons/user';
	import type { ComponentProps } from 'svelte';

	const navMainConfig = [
		{ title: 'Sessions', url: '/app-v2/sessions', icon: CalendarIcon },
		{ title: 'Clients', url: '/app-v2/clients', icon: UserIcon },
	];

	const filteredNavMain = $derived(
		navMainConfig.map((item) => {
			const path = $page.url.pathname;
			let isActive = false;
			if (item.url === '/app-v2/sessions') {
				isActive =
					path === '/app-v2/sessions' ||
					(path.startsWith('/app-v2/sessions/') && !path.startsWith('/app-v2/sessions/new'));
			} else if (item.url === '/app-v2/sessions/new') {
				isActive =
					path === '/app-v2/sessions/new' || path.startsWith('/app-v2/sessions/new/');
			} else if (item.url === '/app-v2/clients') {
				isActive =
					path === '/app-v2/clients' ||
					(path.startsWith('/app-v2/clients/') && !path.startsWith('/app-v2/clients/new'));
			} else {
				isActive = path === item.url || (item.url !== '/' && path.startsWith(item.url + '/'));
			}
			return { ...item, isActive };
		})
	);

	let { ref = $bindable(null), ...restProps }: ComponentProps<typeof Sidebar.Root> = $props();
</script>

<Sidebar.Root bind:ref variant="inset" {...restProps}>
	<Sidebar.Header>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton size="lg">
					{#snippet child({ props })}
						<a href="/app-v2/sessions" {...props}>
							<div
								class="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg"
							>
								<DumbbellIcon class="size-4" aria-hidden="true" />
							</div>
							<div class="grid flex-1 text-start text-sm leading-tight">
								<span class="app-v2-display truncate font-medium tracking-wide">GYMBO</span>
								<span class="truncate text-xs opacity-80">App v2</span>
							</div>
						</a>
					{/snippet}
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
	</Sidebar.Header>
	<Sidebar.Content>
		<nav aria-label="App v2">
			<NavMain items={filteredNavMain} />
		</nav>
	</Sidebar.Content>
	<Sidebar.Footer>
		<NavUser user={{ name: 'Guest', email: '', avatar: '' }} onLogout={() => {}} />
	</Sidebar.Footer>
</Sidebar.Root>
