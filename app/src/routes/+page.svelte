<script lang="ts">
	import { onMount } from 'svelte';
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
	import ScanLineIcon from '@lucide/svelte/icons/scan-line';

	let { data } = $props();

	const HERO_BACKGROUND_MP4_SRC = '/videos/output.mp4';
	// const HERO_BACKGROUND_POSTER_SRC = '/videos/output-poster.jpg';
	const POSE_DEMO_VIDEO_SRC = '/videos/demo.mp4';

	let heroVideo = $state<HTMLVideoElement | null>(null);

	function ensureHeroPlaying() {
		const el = heroVideo;
		if (!el) return;
		el.muted = true;
		void el.play().catch(() => {});
	}

	onMount(() => {
		ensureHeroPlaying();
		const retry = window.setInterval(ensureHeroPlaying, 300);
		window.setTimeout(() => window.clearInterval(retry), 3000);
		return () => window.clearInterval(retry);
	});

	let demoVideoReady = $state(false);
	let demoVideoError = $state(false);

	function onDemoVideoReady() {
		demoVideoReady = true;
		demoVideoError = false;
	}

	function onDemoVideoError() {
		demoVideoError = true;
		demoVideoReady = false;
	}

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

	const navLinks = [
		{ href: '#pose-demo', label: 'Pose' },
		{ href: '#features', label: 'Features' },
	] as const;
</script>

<svelte:head>
	<title>GYMBO — Training analysis for trainers</title>
	<meta
		name="description"
		content="Session tracking, pose-aware video, and charts for trainers and their clients."
	/>
	<!-- <link rel="preload" href={HERO_BACKGROUND_POSTER_SRC} as="image" fetchpriority="high" /> -->
	<link rel="preload" href={HERO_BACKGROUND_MP4_SRC} as="video" type="video/mp4" />
	<link rel="preload" href={POSE_DEMO_VIDEO_SRC} as="video" type="video/mp4" />
</svelte:head>

<div class="flex min-h-dvh flex-col">
	<header class="pointer-events-none fixed inset-x-0 top-0 z-50 px-4 pt-3 md:pt-4">
		<nav
			class="pointer-events-auto mx-auto bg-background flex h-16 w-full max-w-5xl items-center gap-3 rounded-full border border-white/20 bg-black/45 px-4 text-white shadow-lg backdrop-blur-md md:gap-4 md:px-6"
			aria-label="Main"
		>
			<div class="flex min-w-0 flex-1 items-center gap-3 md:gap-6">
				<a
					href="/"
					class="font-display flex shrink-0 items-center gap-2 text-lg tracking-wide md:text-xl"
				>
					<DumbbellIcon class="text-primary size-5 shrink-0 md:size-6" aria-hidden="true" />
					<span>GYMBO</span>
				</a>
				<ul class="hidden min-w-0 items-center gap-0.5 sm:flex md:gap-1">
					{#each navLinks as link (link.href)}
						<li>
							<a
								href={link.href}
								class="rounded-full px-2.5 py-1.5 text-sm text-white/85 transition-colors hover:bg-white/10 hover:text-white md:px-3"
							>
								{link.label}
							</a>
						</li>
					{/each}
				</ul>
			</div>
			<Button href={primaryHref} size="sm" class="shrink-0 rounded-full">
				{primaryLabel}
			</Button>
		</nav>
	</header>

	<main class="flex flex-1 flex-col">
		<section
			id="pose-demo"
			class="scroll-mt-24 relative flex h-dvh min-h-dvh flex-col overflow-hidden bg-black bg-cover bg-center px-4 md:scroll-mt-28"
			aria-labelledby="pose-demo-heading"
		>
			<!-- svelte-ignore a11y_media_has_caption -->
			<video
				bind:this={heroVideo}
				class="pointer-events-none absolute inset-0 z-[1] h-full w-full object-cover"
				src={HERO_BACKGROUND_MP4_SRC}
				autoplay
				muted
				loop
				playsinline
				preload="auto"
				aria-hidden="true"
				onloadeddata={ensureHeroPlaying}
				oncanplay={ensureHeroPlaying}
			></video>
			<div
				class="absolute inset-0 z-[2] bg-gradient-to-b from-black/60 via-black/45 to-black/75"
				aria-hidden="true"
			></div>

			<div
				class="relative z-10 mx-auto flex w-full max-w-5xl flex-1 flex-col justify-center gap-8 px-2 pt-20 pb-8 md:gap-10 md:pt-24 md:pb-10"
			>
				<div class="text-center text-white">
					<h1 class="font-display text-4xl tracking-tight drop-shadow-sm md:text-5xl">
						See every rep, clearly.
					</h1>
					<p class="mx-auto mt-3 max-w-xl text-lg text-white/85">
						Session tracking, pose-aware video, and charts — built for trainers and their clients.
					</p>
				</div>

				<div
					class="border-white/15 grid grid-cols-1 items-center gap-6 rounded-2xl border bg-black/45 p-4 shadow-2xl backdrop-blur-md md:grid-cols-[2fr_3fr] md:gap-8 md:p-6"
				>
					<div class="text-white">
						<p
							class="text-primary mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-wider"
						>
							<span
								class="bg-primary/20 flex size-8 items-center justify-center rounded-lg"
								aria-hidden="true"
							>
								<ScanLineIcon class="size-4" />
							</span>
							Pose detection
						</p>
						<h2 id="pose-demo-heading" class="font-display text-2xl tracking-tight md:text-3xl">
							Form you can see, rep by rep.
						</h2>
						<p class="mt-3 text-base text-white/80 md:text-lg">
							Capture a set with live pose overlay on device, then review form and progress in charts
							when you are ready.
						</p>
						<ul class="mt-5 flex flex-wrap gap-2" aria-label="Pose detection highlights">
							<li>
								<span
									class="rounded-full border border-white/20 bg-white/10 px-3 py-1 text-sm text-white/90"
								>
									Live overlay
								</span>
							</li>
							<li>
								<span
									class="rounded-full border border-white/20 bg-white/10 px-3 py-1 text-sm text-white/90"
								>
									Rep-aware metrics
								</span>
							</li>
						</ul>
						<div class="mt-5 flex flex-wrap items-center gap-3 w-full">
							<Button href={primaryHref} size="lg">{primaryLabel}</Button>
						</div>
					</div>

					<div class="relative overflow-hidden rounded-xl border border-white/15 bg-black/30">
						{#if demoVideoError}
							<div
								class="flex aspect-video w-full flex-col items-center justify-center gap-3 px-4 text-center text-white/70"
							>
								<VideoIcon class="size-10 opacity-60" aria-hidden="true" />
								<p class="text-sm">Demo video coming soon!</p>
							</div>
						{:else}
							{#if !demoVideoReady}
								<div
									class="pointer-events-none absolute inset-0 z-10 flex aspect-video w-full flex-col items-center justify-center gap-3 px-4 text-center text-white/70"
									aria-hidden="true"
								>
									<VideoIcon class="size-10 animate-pulse opacity-60" aria-hidden="true" />
									<p class="text-sm">Loading demo…</p>
								</div>
							{/if}
							<!-- svelte-ignore a11y_media_has_caption -->
							<video
								class="aspect-video w-full bg-black/40 object-cover"
								src={POSE_DEMO_VIDEO_SRC}
								controls
								playsinline
								loop
								autoplay
								muted
								preload="auto"
								aria-label="Demo of pose detection overlay during a training set"
								onloadedmetadata={onDemoVideoReady}
								oncanplay={onDemoVideoReady}
								onerror={onDemoVideoError}
							></video>
						{/if}
					</div>
				</div>
			</div>
		</section>

		<section
			id="features"
			class="scroll-mt-24 px-4 py-12 md:scroll-mt-28 md:py-16"
			aria-labelledby="features-heading"
		>
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

		<section
			id="get-started"
			class="scroll-mt-24 border-border/60 border-t px-4 py-12 md:scroll-mt-28 md:py-16"
		>
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

	<footer class="text-muted-foreground border-t px-4 py-6 text-center text-sm flex flex-row justify-between">
		<div class="w-full max-w-5xl mx-auto flex justify-between items-center flex-row gap-4">
			<div class="flex flex-row gap-4">
				<a href="/terms" class="flex items-center gap-2 text-sm">Terms of Service</a>
				<a href="/privacy" class="flex items-center gap-2 text-sm">Privacy Policy</a>
			</div>
			<div class="flex flex-col gap-2">
				<p>© {new Date().getFullYear()} GYMBO</p>
				{#if !data.isSignedIn}
					<p class="mt-2">
						Already have an account?
						<a href="/login" class="text-primary underline-offset-4 hover:underline">Sign in</a>
					</p>
				{/if}
			</div>
		</div>
	</footer>
</div>
