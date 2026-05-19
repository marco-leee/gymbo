<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { authClient } from '$lib/auth-client';
	import type { AuthSession } from '$lib/auth';
	import NavMain from './nav-main.svelte';
	import NavUser from './nav-user.svelte';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import DumbbellIcon from '@lucide/svelte/icons/dumbbell';
	import CalendarIcon from '@lucide/svelte/icons/calendar';
	import UserIcon from '@lucide/svelte/icons/user';
	import type { ComponentProps } from 'svelte';

	const navMainConfig = [
		{ title: 'Sessions', url: '/app/sessions', icon: CalendarIcon },
		{ title: 'Clients', url: '/app/clients', icon: UserIcon },
	];

	const filteredNavMain = $derived(
		navMainConfig.map((item) => {
			const path = $page.url.pathname;
			let isActive = false;
			if (item.url === '/app/sessions') {
				isActive =
					path === '/app/sessions' ||
					(path.startsWith('/app/sessions/') && !path.startsWith('/app/sessions/new'));
			} else if (item.url === '/app/sessions/new') {
				isActive =
					path === '/app/sessions/new' || path.startsWith('/app/sessions/new/');
			} else if (item.url === '/app/clients') {
				isActive =
					path === '/app/clients' ||
					(path.startsWith('/app/clients/') && !path.startsWith('/app/clients/new'));
			} else {
				isActive = path === item.url || (item.url !== '/' && path.startsWith(item.url + '/'));
			}
			return { ...item, isActive };
		})
	);

	let {
		user,
		ref = $bindable(null),
		...restProps
	}: ComponentProps<typeof Sidebar.Root> & {
		user: AuthSession['user'];
	} = $props();

	const navUser = $derived({
		name: user.name || user.email,
		email: user.email,
		avatar: user.image ?? ''
	});

	async function handleLogout() {
		await authClient.signOut();
		await goto('/login');
	}
</script>

<Sidebar.Root bind:ref variant="inset" {...restProps}>
	<Sidebar.Header>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton size="lg">
					{#snippet child({ props })}
						<a href="/app/sessions" {...props}>
							<div
								class="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg"
							>
								<DumbbellIcon class="size-4" aria-hidden="true" />
							</div>
							<div class="grid flex-1 text-start text-sm leading-tight">
								<span class="app-display truncate font-medium tracking-wide">GYMBO</span>
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
		<NavUser user={navUser} onLogout={handleLogout} />
	</Sidebar.Footer>
</Sidebar.Root>
