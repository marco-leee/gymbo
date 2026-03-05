<script lang="ts">
	import { page } from '$app/stores';
	import NavMain from './nav-main.svelte';
	import NavUser from './nav-user.svelte';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import CommandIcon from '@lucide/svelte/icons/command';
	import LayoutDashboardIcon from '@lucide/svelte/icons/layout-dashboard';
	import UserIcon from '@lucide/svelte/icons/user';
	import CalendarIcon from '@lucide/svelte/icons/calendar';
	import Settings2Icon from '@lucide/svelte/icons/settings-2';
	import type { ComponentProps } from 'svelte';

	const navMainConfig = [
		{ title: 'Dashboard', url: '/app/dashboard', icon: LayoutDashboardIcon },
		{ title: 'Clients', url: '/app/clients', icon: UserIcon },
		{ title: 'Sessions', url: '/app/sessions', icon: CalendarIcon },
		{ title: 'Settings', url: '/app/settings', icon: Settings2Icon },
	];

	const filteredNavMain = $derived(
		navMainConfig.map((item) => ({
			...item,
			isActive: $page.url.pathname === item.url || $page.url.pathname.startsWith(item.url + '/'),
		}))
	);

	let { ref = $bindable(null), ...restProps }: ComponentProps<typeof Sidebar.Root> = $props();
</script>

<Sidebar.Root bind:ref variant="inset" {...restProps}>
	<Sidebar.Header>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton size="lg">
					{#snippet child({ props })}
						<a href="/app/dashboard" {...props}>
							<div
								class="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg"
							>
								<CommandIcon class="size-4" />
							</div>
							<div class="grid flex-1 text-start text-sm leading-tight">
								<span class="truncate font-medium">Acme Inc</span>
								<span class="truncate text-xs">Enterprise</span>
							</div>
						</a>
					{/snippet}
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
	</Sidebar.Header>
	<Sidebar.Content>
		<NavMain items={filteredNavMain} />
	</Sidebar.Content>
	<Sidebar.Footer>
		<NavUser user={{ name: 'Guest', email: '', avatar: '' }} onLogout={() => {}} />
	</Sidebar.Footer>
</Sidebar.Root>
