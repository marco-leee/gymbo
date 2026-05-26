<script lang="ts">
	import MonitorIcon from "@lucide/svelte/icons/monitor";
	import MoonIcon from "@lucide/svelte/icons/moon";
	import SunIcon from "@lucide/svelte/icons/sun";
	import { setMode, userPrefersMode } from "mode-watcher";

	import * as ToggleGroup from "$lib/components/ui/toggle-group/index.js";

	function handleThemeChange(value: string) {
		if (value === "light" || value === "dark" || value === "system") {
			setMode(value);
		}
	}
</script>

<div class="px-1">
	<p class="mb-1.5 px-1 text-xs text-muted-foreground">Theme</p>
	<ToggleGroup.Root
		type="single"
		variant="outline"
		size="sm"
		class="grid w-full grid-cols-3"
		value={userPrefersMode.current ?? "system"}
		onValueChange={(value) => value && handleThemeChange(value)}
	>
		<ToggleGroup.Item value="light" aria-label="Light theme" class="w-full">
			<SunIcon />
			<span class="sr-only">Light</span>
		</ToggleGroup.Item>
		<ToggleGroup.Item value="dark" aria-label="Dark theme" class="w-full">
			<MoonIcon />
			<span class="sr-only">Dark</span>
		</ToggleGroup.Item>
		<ToggleGroup.Item value="system" aria-label="System theme" class="w-full">
			<MonitorIcon />
			<span class="sr-only">System</span>
		</ToggleGroup.Item>
	</ToggleGroup.Root>
</div>
