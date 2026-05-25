<script lang="ts">
	import { page } from '$app/stores';
	import { browser } from '$app/environment';
	import { onMount, tick } from 'svelte';
	import { useSidebar } from '$lib/components/ui/sidebar/context.svelte.js';
	import {
		resumeTourForPath,
		setTourMobileNavHandler,
		shouldAutoStartTour,
		startTour
	} from '$lib/ui-tour';

	const sidebar = useSidebar();

	onMount(() => {
		setTourMobileNavHandler(async () => {
			if (sidebar.isMobile) {
				sidebar.setOpenMobile(true);
				await tick();
			}
		});

		if (shouldAutoStartTour()) {
			startTour();
		}

		return () => {
			setTourMobileNavHandler(null);
		};
	});

	$effect(() => {
		const pathname = $page.url.pathname;
		const searchParams = $page.url.searchParams;
		if (!browser) return;

		void (async () => {
			await tick();
			await resumeTourForPath(pathname, searchParams);
		})();
	});
</script>
