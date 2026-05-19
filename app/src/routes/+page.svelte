<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import {
		Card,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card/index.js';
	import DumbbellIcon from '@lucide/svelte/icons/dumbbell';
	import UsersIcon from '@lucide/svelte/icons/users';
	import VideoIcon from '@lucide/svelte/icons/video';
	import BarChart3Icon from '@lucide/svelte/icons/bar-chart-3';

	let { data } = $props();

	const primaryHref = $derived(data.isSignedIn ? '/app/sessions' : '/signup');
	const primaryLabel = $derived(data.isSignedIn ? 'Open app' : 'Get started');

	const features = [
		{
			icon: UsersIcon,
			title: 'Clients',
			description: 'Keep your roster in one place and ready for every session.'
		},
		{
			icon: VideoIcon,
			title: 'Capture',
			description: 'Record sessions with pose-aware analysis as your clients move.'
		},
		{
			icon: BarChart3Icon,
			title: 'Review',
			description: 'Revisit form and progress with charts when you are ready.'
		}
	] as const;
</script>

<svelte:head>
	<title>GYMBO — Training analysis for trainers</title>
	<meta
		name="description"
		content="Session tracking, pose-aware video, and charts for trainers and their clients."
	/>
</svelte:head>

<div class="bg-background flex min-h-dvh flex-col">
	<header
		class="border-border/60 bg-background/80 sticky top-0 z-50 border-b backdrop-blur-sm"
	>
		<div class="mx-auto flex h-14 max-w-5xl items-center justify-between px-4 md:h-16">
			<a href="/" class="font-display flex items-center gap-2 text-lg tracking-wide md:text-xl">
				<DumbbellIcon class="text-primary size-5 shrink-0 md:size-6" aria-hidden="true" />
				<span>GYMBO</span>
			</a>
			<nav>
				<Button href={primaryHref} size="sm">{primaryLabel}</Button>
			</nav>
		</div>
	</header>

	<main class="flex flex-1 flex-col">
		<section
			class="from-muted/40 to-background flex min-h-[calc(100dvh-3.5rem)] flex-col justify-center bg-gradient-to-b px-4 md:min-h-[calc(100dvh-4rem)]"
		>
			<div class="mx-auto w-full max-w-5xl text-center">
				<h1 class="font-display text-4xl tracking-tight md:text-5xl">
					See every rep, clearly.
				</h1>
				<p class="text-muted-foreground mx-auto mt-4 max-w-xl text-lg">
					Session tracking, pose-aware video, and charts — built for trainers and their clients.
				</p>
				<div class="mt-8 flex flex-wrap items-center justify-center gap-3">
					<Button href={primaryHref} size="lg">{primaryLabel}</Button>
					{#if !data.isSignedIn}
						<Button href="/login" variant="outline" size="lg">Sign in</Button>
					{/if}
				</div>
			</div>
		</section>

		<section class="px-4 py-12 md:py-16" aria-labelledby="features-heading">
			<div class="mx-auto max-w-5xl">
				<h2 id="features-heading" class="sr-only">Features</h2>
				<ul class="grid grid-cols-1 gap-4 md:grid-cols-3 md:gap-6">
					{#each features as feature (feature.title)}
						<li>
							<Card class="h-full border-border/80">
								<CardHeader>
									<div
										class="bg-primary/10 text-primary mb-2 flex size-10 items-center justify-center rounded-lg"
										aria-hidden="true"
									>
										<feature.icon class="size-5" />
									</div>
									<CardTitle class="font-display text-xl">{feature.title}</CardTitle>
									<CardDescription>{feature.description}</CardDescription>
								</CardHeader>
							</Card>
						</li>
					{/each}
				</ul>
			</div>
		</section>

		<section class="border-border/60 border-t px-4 py-12 md:py-16">
			<div class="mx-auto max-w-5xl text-center">
				<p class="font-display text-2xl tracking-tight md:text-3xl">Ready when you are.</p>
				<p class="text-muted-foreground mt-2">
					{#if data.isSignedIn}
						Your sessions are waiting in the app.
					{:else}
						Create a free account and start your first session.
					{/if}
				</p>
				<div class="mt-6">
					<Button href={primaryHref} size="lg">{primaryLabel}</Button>
				</div>
			</div>
		</section>
	</main>

	<footer class="border-border/60 text-muted-foreground border-t px-4 py-6 text-center text-sm">
		<div class="mx-auto max-w-5xl">
			<p>© {new Date().getFullYear()} GYMBO</p>
			{#if !data.isSignedIn}
				<p class="mt-2">
					Already have an account?
					<a href="/login" class="text-primary underline-offset-4 hover:underline">Sign in</a>
				</p>
			{/if}
		</div>
	</footer>
</div>
