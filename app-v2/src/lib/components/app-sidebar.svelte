<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { authStore } from '$lib/auth/index.js';
	import { canUserAccessRoute } from '$lib/auth/config.js';
	import type { AuthState } from '$lib/auth/types.js';
	import NavMain from './nav-main.svelte';
	import NavUser from './nav-user.svelte';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import CommandIcon from '@lucide/svelte/icons/command';
	import MonitorIcon from '@lucide/svelte/icons/monitor';
	import SmartphoneIcon from '@lucide/svelte/icons/smartphone';
	import ClipboardListIcon from '@lucide/svelte/icons/clipboard-list';
	import DumbbellIcon from '@lucide/svelte/icons/dumbbell';
	import UsersIcon from '@lucide/svelte/icons/users';
	import UserIcon from '@lucide/svelte/icons/user';
	import BuildingIcon from '@lucide/svelte/icons/building';
	import Settings2Icon from '@lucide/svelte/icons/settings-2';
	import type { ComponentProps } from 'svelte';

	const navMainConfig = [
		{ title: 'Pose Detection Live', url: '/dashboard/desktop', icon: MonitorIcon },
		{ title: 'Pose Detection Mobile', url: '/dashboard/mobile', icon: SmartphoneIcon },
		{ title: 'Assessments', url: '/dashboard/assessments', icon: ClipboardListIcon },
		{ title: 'Exercises', url: '/dashboard/exercises', icon: DumbbellIcon },
		{ title: 'Trainers', url: '/dashboard/trainers', icon: UsersIcon },
		{ title: 'Clients', url: '/dashboard/clients', icon: UserIcon },
		{ title: 'Organisations', url: '/dashboard/organisations', icon: BuildingIcon },
		{ title: 'Settings', url: '/dashboard/settings', icon: Settings2Icon },
	];

	let authState = $state<AuthState>({
		isLoading: true,
		isAuthenticated: false,
		user: null,
		token: null,
		gateway: null,
	});

	onMount(() => authStore.subscribe((s) => (authState = s)));

	const filteredNavMain = $derived(
		navMainConfig
			.filter((item) => {
				const role = authState.token?.user_type;
				if (!role) return false;
				return canUserAccessRoute(role, item.url);
			})
			.map((item) => ({
				...item,
				isActive: $page.url.pathname === item.url || $page.url.pathname.startsWith(item.url + '/'),
			}))
	);

	function handleLogout() {
		authStore.logout((path) => goto(path));
	}

	let { ref = $bindable(null), ...restProps }: ComponentProps<typeof Sidebar.Root> = $props();
</script>

<Sidebar.Root bind:ref variant="inset" {...restProps}>
	<Sidebar.Header>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton size="lg">
					{#snippet child({ props })}
						<a href="/dashboard" {...props}>
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
		<NavUser
			user={authState.user ? { name: authState.user.name ?? '', email: authState.user.email ?? '', avatar: '' } : { name: '', email: '', avatar: '' }}
			onLogout={handleLogout}
		/>
	</Sidebar.Footer>
</Sidebar.Root>
