<script lang="ts">
	let { children } = $props();
</script>

<div class="bg-background flex min-h-dvh flex-col items-center justify-center p-4">
	<div class="w-full max-w-md">
		{@render children()}
	</div>
</div>
