<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Card, CardContent } from '$lib/components/ui/card/index.js';

	const redirectPath = '/app';
	const redirectDelaySeconds = 5;
	const statusCode = $page.status;

	let secondsLeft = $state(redirectDelaySeconds);

	onMount(() => {
		const interval = setInterval(() => {
			secondsLeft -= 1;
			if (secondsLeft <= 0) {
				clearInterval(interval);
				goto(redirectPath);
			}
		}, 1000);

		return () => clearInterval(interval);
	});
</script>

<svelte:head>
	<title>{statusCode} Wrong Place — GYMBO</title>
</svelte:head>

<div class="bg-background flex min-h-dvh items-center justify-center p-4">
	<Card class="w-3xl overflow-hidden py-0">
		<CardContent class="flex flex-col p-0 sm:flex-row sm:items-stretch">
			<div
				class="bg-muted/40 relative flex shrink-0 items-center justify-center sm:w-[400px]"
				aria-hidden="true"
			>
				<img
					src="/error-light.png"
					alt=""
					width="400"
					height="400"
					class="size-[400px] object-contain dark:hidden bg-card-background"
				/>
				<img
					src="/error-dark.png"
					alt=""
					width="400"
					height="400"
					class="hidden size-[400px] object-contain dark:block bg-card-background"
				/>
			</div>

			<div class="flex flex-1 flex-col justify-center gap-6 p-6 sm:p-8">
				<div class="space-y-3">
					<h1 class="font-display text-foreground text-3xl tracking-tight sm:text-4xl">
						Get Out! (JKJK) 🤪
					</h1>
                    {#if $page.error?.message}
                        <p class="text-foreground/60 text-2xl">{$page.status} {$page.error.message}</p>
                    {/if}
					<p class="text-muted-foreground text-base leading-relaxed sm:text-lg">
						You are in the wrong place. You belong to somewhere valuable.
					</p>
                    <p class="text-muted-foreground text-base leading-relaxed sm:text-lg">
                        Let me take you back. And you are welcome!
                    </p>
				</div>

				<div class="flex flex-col gap-3 sm:flex-row sm:items-center">
					<Button href={redirectPath} size="lg">
                        Redirecting in {secondsLeft}
                        {secondsLeft === 1 ? 'second' : 'seconds'}…
                    </Button>
				</div>
			</div>
		</CardContent>
	</Card>
</div>
