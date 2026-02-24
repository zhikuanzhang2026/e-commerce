<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import '../app.css';
	import Header from '$lib/components/Header.svelte';
	import MobileMenu from '$lib/components/header/MobileMenu.svelte';
	import Footer from '$lib/components/Footer.svelte';
	import CartDrawer from '$lib/components/CartDrawer.svelte';
	import CookieBanner from '$lib/components/CookieBanner.svelte';
	import Toast from '$lib/components/ui/Toast.svelte';
	import { fade } from 'svelte/transition';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { env } from '$env/dynamic/public';

	import {
		QueryClient,
		QueryClientProvider,
		MutationCache,
		QueryCache
	} from '@tanstack/svelte-query';
	import { browser } from '$app/environment';
	import { toastStore } from '$lib/stores/toast.svelte';
	import Metadata from '$lib/components/seo/Metadata.svelte';

	const COOKIE_CONSENT_KEY = 'cookie_consent';
	const COOKIE_CONSENT_EVENT = 'cookie-consent-change';

	let { children, data } = $props();
	let cookieConsent = $state<string | null>(null);
	const canLoadAnalytics = $derived(
		Boolean(env.PUBLIC_ANALYTICS_CODE) && cookieConsent === 'accepted'
	);

	const queryClient = new QueryClient({
		mutationCache: new MutationCache({
			onError: (error: unknown, _variables, _context, mutation) => {
				// We always show toast for mutations unless explicitly suppressed via meta
				if (mutation.meta?.suppressErrorToast) return;

				const message = error instanceof Error ? error.message : String(error);
				toastStore.show(message || 'An error occurred', 'error');
			}
		}),
		queryCache: new QueryCache({
			onError: (error: unknown) => {
				console.error('Global Query Error:', error);
			}
		}),
		defaultOptions: {
			queries: {
				enabled: browser,
				staleTime: 60 * 1000
			}
		}
	});

	let isCartOpen = $state(false);

	let isMenuOpen = $state(false);

	// Close menu on navigation
	$effect(() => {
		if ($page.url.pathname) {
			isMenuOpen = false;
		}
	});

	function toggleMenu() {
		isMenuOpen = !isMenuOpen;
	}

	import type { NavItem } from '$lib/types';
	import { NavigationLocationOptions } from '$lib/pocketbase-types';

	// Fallback navigation if data is missing or sparse
	let headerNav = $derived.by(() => {
		if (data.headerNav && data.headerNav.length > 1) {
			return data.headerNav;
		}
		// Default items if backend navigation is insufficient
		const defaults: NavItem[] = [
			{
				label: 'Shop',
				url: '/shop',
				id: 'default-shop',
				location: NavigationLocationOptions.header,
				order: 1,
				isVisible: true
			} as NavItem,
			{
				label: 'Collection',
				url: '/collection',
				id: 'default-collection',
				location: NavigationLocationOptions.header,
				order: 2,
				isVisible: true
			} as NavItem
		];
		// If data has at least one item, merge it? Or just override?
		// Strategy: If data has only 1 item, preprend "Shop" if not present.
		if (data.headerNav && data.headerNav.length === 1) {
			const hasShop = data.headerNav.some((n) => n.url === '/shop');
			const shopItem = {
				label: 'Shop',
				url: '/shop',
				id: 'default-shop-prefix',
				location: NavigationLocationOptions.header,
				order: 0,
				isVisible: true
			} as NavItem;
			return hasShop ? data.headerNav : [shopItem, ...data.headerNav];
		}
		return defaults;
	});

	function toggleCart() {
		isCartOpen = !isCartOpen;
	}

	onMount(() => {
		const syncCookieConsent = () => {
			cookieConsent = localStorage.getItem(COOKIE_CONSENT_KEY);
		};

		const handleCookieConsentChange = (event: Event) => {
			const customEvent = event as CustomEvent<{ status?: string }>;
			cookieConsent = customEvent.detail?.status ?? localStorage.getItem(COOKIE_CONSENT_KEY);
		};

		syncCookieConsent();
		window.addEventListener(COOKIE_CONSENT_EVENT, handleCookieConsentChange);

		return () => {
			window.removeEventListener(COOKIE_CONSENT_EVENT, handleCookieConsentChange);
		};
	});
</script>

<Metadata
	title={data.settings.siteName}
	description="Discover modern luxury essentials at {data.settings
		.siteName}. Rooted in independent style and timeless design."
	siteName={data.settings.siteName}
/>

<svelte:head>
	<link rel="icon" href={data.settings.icon || favicon} />

	{#if canLoadAnalytics}
		<!-- eslint-disable-next-line svelte/no-at-html-tags -->
		{@html env.PUBLIC_ANALYTICS_CODE}
	{/if}
</svelte:head>

<div
	class="flex flex-col min-h-screen bg-background-light dark:bg-background-dark text-text-main dark:text-white transition-colors duration-300"
>
	<!-- Skip to Content - Accessibility -->
	<a
		href="#main-content"
		class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[200] focus:bg-primary focus:text-white focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:uppercase focus:tracking-widest"
	>
		Skip to Content
	</a>

	<QueryClientProvider client={queryClient}>
		<Header
			onCartClick={toggleCart}
			onMenuClick={toggleMenu}
			{isMenuOpen}
			navItems={headerNav}
			siteName={data.settings.siteName}
		/>
		<CartDrawer bind:isOpen={isCartOpen} />

		{#if isMenuOpen}
			<MobileMenu
				navItems={headerNav}
				onClose={() => (isMenuOpen = false)}
				onCartClick={toggleCart}
				onSearchClick={() => {
					isMenuOpen = false;
				}}
			/>
		{/if}

		<main id="main-content" class="flex-grow w-full">
			{#key $page.url.pathname}
				<div in:fade={{ duration: 300, delay: 100 }} class="w-full">
					{@render children()}
				</div>
			{/key}
		</main>

		<Footer navItems={data.footerNav} isHome={$page.url.pathname === '/'} />
		<Toast />
		<CookieBanner />
	</QueryClientProvider>
</div>
