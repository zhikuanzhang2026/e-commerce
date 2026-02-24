<script lang="ts">
	import type { NavItem } from '$lib/types';
	import { TRANSITIONS } from '$lib/constants';
	import { MESSAGES } from '$lib/messages';

	interface FooterProps {
		navItems?: NavItem[];
		isHome?: boolean;
		siteSettings?: {
			siteName: string;
			// ... other settings if needed
		};
	}

	let { navItems = [], isHome = false }: FooterProps = $props();
	const COOKIE_SETTINGS_OPEN_EVENT = 'cookie-settings-open';

	let email = $state('');
	let status = $state<'idle' | 'loading' | 'success' | 'error'>('idle');
	let message = $state('');

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();

		if (!email || !email.includes('@')) {
			status = 'error';
			message = MESSAGES.ERROR.PLEASE_ENTER_VALID_EMAIL;
			return;
		}

		status = 'loading';

		// 模拟 API 调用 - 实际项目中替换为真实的 newsletter API
		await new Promise((resolve) => setTimeout(resolve, 800));

		// 成功订阅
		status = 'success';
		message = MESSAGES.SUCCESS.SUBSCRIBED;
		email = '';

		// 3秒后重置状态
		setTimeout(() => {
			status = 'idle';
			message = '';
		}, 3000);
	}

	function openCookieSettings() {
		window.dispatchEvent(new Event(COOKIE_SETTINGS_OPEN_EVENT));
	}
</script>

<footer
	class={`bg-white dark:bg-black text-primary dark:text-white ${isHome ? 'pt-20 pb-13' : 'py-13'} px-6 md:px-12 flex items-center justify-center`}
>
	<div
		class="w-full max-w-[1600px] mx-auto flex flex-col lg:flex-row justify-between items-start lg:items-end gap-16 lg:gap-0"
	>
		<!-- Left: Newsletter -->
		<div class="w-full max-w-md">
			<h4 class="text-sm font-serif font-medium mb-0 tracking-wide text-primary dark:text-white">
				Join the Conversation
			</h4>
			<form class="relative border-none outline-none" onsubmit={handleSubmit}>
				<label for="newsletter-email" class="sr-only">Email Address</label>
				<input
					id="newsletter-email"
					type="email"
					placeholder="EMAIL ADDRESS"
					aria-label="Email Address"
					bind:value={email}
					disabled={status === 'loading'}
					class="w-full bg-transparent border-b border-primary dark:border-white py-3 pr-10 text-[10px] font-sans uppercase tracking-[0.15em] placeholder:text-primary/60 dark:placeholder:text-white/60 outline-none focus:outline-none focus:ring-0 focus:shadow-none focus:border-primary dark:focus:border-white disabled:opacity-50"
				/>
				<button
					type="submit"
					class="absolute right-0 top-1/2 -translate-y-1/2 cursor-pointer hover:opacity-60 {TRANSITIONS.opacity} disabled:opacity-30"
					aria-label="Subscribe to newsletter"
					disabled={status === 'loading'}
				>
					{#if status === 'loading'}
						<span class="material-symbols-outlined text-[18px] animate-spin">progress_activity</span
						>
					{:else}
						<svg
							width="18"
							height="18"
							viewBox="0 0 24 24"
							fill="none"
							xmlns="http://www.w3.org/2000/svg"
						>
							<path
								d="M1 12H23M23 12L19 8M23 12L19 16"
								stroke="currentColor"
								stroke-width="1.5"
								stroke-linecap="square"
							/>
						</svg>
					{/if}
				</button>
				{#if message}
					<p
						class="absolute right-8 top-1/2 -translate-y-1/2 text-[10px] uppercase tracking-[0.15em] {status ===
						'success'
							? 'text-green-600 dark:text-green-400'
							: 'text-red-600 dark:text-red-400'} pointer-events-none whitespace-nowrap"
					>
						{message}
					</p>
				{/if}
			</form>
		</div>

		<!-- Right: Links -->
		<div
			class="flex flex-wrap gap-x-8 gap-y-4 items-center justify-start lg:justify-end text-[10px] font-sans uppercase tracking-[0.15em] text-black"
		>
			{#each navItems as link (link.url)}
				<a href={link.url} class="text-black no-underline hover:underline underline-offset-2">
					{link.label}
				</a>
			{/each}

			<button
				type="button"
				class="text-black no-underline hover:underline underline-offset-2 cursor-pointer"
				onclick={openCookieSettings}
			>
				COOKIE SETTINGS
			</button>
		</div>
	</div>
</footer>
