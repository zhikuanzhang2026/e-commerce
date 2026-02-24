<script lang="ts">
	import { page } from '$app/stores';
	import { useCart } from '$lib/stores/cart.svelte';
	import { useWishlist } from '$lib/stores/wishlist.svelte';
	import ProductListGrid from '$lib/components/shop/ProductListGrid.svelte';
	import RemoteImage from '$lib/components/ui/RemoteImage.svelte';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { MESSAGES } from '$lib/messages';
	import { fade } from 'svelte/transition';
	import { COLORS } from '$lib/constants';

	const cart = useCart();
	const wishlist = useWishlist();

	let { data } = $props();
	let product = $derived(data.product);
	let relatedProducts = $derived(data.related);

	let selectedSize = $state('');
	let selectedColor = $state('');
	let currentImageIndex = $state(0);

	const DEFAULT_SIZE_ORDER = ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL', 'O/S'] as const;
	function getSizeRank(sizeLabel: string) {
		const normalized = String(sizeLabel || '')
			.trim()
			.toUpperCase();
		const idx = DEFAULT_SIZE_ORDER.indexOf(normalized as (typeof DEFAULT_SIZE_ORDER)[number]);
		return idx === -1 ? Number.POSITIVE_INFINITY : idx;
	}

	// UI States
	let isAdding = $state(false);
	let sizeError = $state(false);

	// Derived Colors (from variants or attributes)
	let derivedColors = $derived(
		product.variants?.length
			? ([...new Set(product.variants.map((v) => v.color).filter((c) => !!c))] as string[])
			: (product.attributes?.colors as string[]) || []
	);

	let colorSwatchByLabel = $derived.by(() => {
		const map = new Map<string, string>();
		for (const v of product.variants ?? []) {
			const label = (v.color || '').trim();
			if (!label || map.has(label)) continue;
			const swatch = (v.colorSwatch || '').trim();
			if (swatch) map.set(label, swatch);
		}
		return map;
	});

	// Derived available sizes for selected color
	let availableSizes = $derived.by(() => {
		if (!product.variants || product.variants.length === 0)
			return (product.attributes?.sizes as string[]) || [];

		return product.variants
			.filter((v) => v.color === selectedColor)
			.map((v) => ({
				size: v.size,
				stock: v.stockQuantity
			}))
			.sort((a, b) => {
				const aRank = getSizeRank(a.size);
				const bRank = getSizeRank(b.size);
				if (aRank !== bRank) return aRank - bRank;

				const aNum = Number(a.size);
				const bNum = Number(b.size);
				const aNumOk = Number.isFinite(aNum);
				const bNumOk = Number.isFinite(bNum);
				if (aNumOk && bNumOk && aNum !== bNum) return aNum - bNum;
				if (aNumOk !== bNumOk) return aNumOk ? -1 : 1;

				return String(a.size).localeCompare(String(b.size));
			});
	});

	// Reset state when product changes
	$effect(() => {
		if (product) {
			selectedColor = derivedColors?.[0] || '';
			selectedSize = '';
			sizeError = false;
			currentImageIndex = 0;
		}
	});

	// Dynamic Image Gallery Logic
	// Variant galleries live on `product_variants.gallery_images`.
	let sortedImages = $derived.by(() => {
		const defaultImages = product.images || [];
		const dedupeImages = (images: Array<string | undefined>) => [
			...new Set(images.filter((img): img is string => !!img))
		];

		if (!selectedColor) return defaultImages;

		const variantsForColor = (product.variants || []).filter((v) => v.color === selectedColor);
		if (variantsForColor.length === 0) return defaultImages;

		const exactVariant = selectedSize
			? variantsForColor.find((v) => v.size === selectedSize)
			: undefined;
		const variant = exactVariant || variantsForColor[0];

		const variantGallery = variant?.galleryImages?.filter(Boolean) ?? [];
		const variantImage = variant?.image;

		if (variantGallery.length > 0) {
			// Ensure a dedicated variant image (if any) is included.
			return dedupeImages([variantImage, ...variantGallery]);
		}

		if (variantImage) {
			return [variantImage];
		}

		const colorFallbackImages = dedupeImages(
			variantsForColor.flatMap((v) => [v.image, ...(v.galleryImages || [])])
		);
		if (colorFallbackImages.length > 0) return colorFallbackImages;

		return defaultImages;
	});

	// Scroll to top when images change (implying a variant switch)
	let galleryContainer: HTMLElement;
	$effect(() => {
		// Trigger dependency on sortedImages
		if (sortedImages && galleryContainer) {
			galleryContainer.scrollTop = 0;
			// For mobile
			galleryContainer.scrollLeft = 0;
			currentImageIndex = 0;
		}
	});

	function handleGalleryScroll(e: UIEvent) {
		const target = e.target as HTMLElement;
		const width = target.clientWidth;
		currentImageIndex = Math.round(target.scrollLeft / width);
	}

	$effect(() => {
		if (!selectedColor || !selectedSize || !product.variants?.length) return;

		const existsInColor = product.variants.some(
			(v) => v.color === selectedColor && v.size === selectedSize
		);

		if (!existsInColor) {
			selectedSize = '';
		}
	});

	function addToBag() {
		if (!selectedSize) {
			sizeError = true;
			// Removed redundant toast, visual shake is enough
			setTimeout(() => (sizeError = false), 1000);
			return;
		}

		const variant = product.variants?.find(
			(v) => v.color === selectedColor && v.size === selectedSize
		);
		if (variant && (variant.stockQuantity || 0) <= 0) {
			toastStore.error(MESSAGES.ERROR.OUT_OF_STOCK);
			return;
		}

		isAdding = true;
		setTimeout(() => {
			cart.addItem(product, selectedColor, selectedSize);
			toastStore.success(MESSAGES.SUCCESS.ADDED_TO_BAG(product.title));
			isAdding = false;
		}, 500);
	}

	let jsonLd = $derived(
		JSON.stringify({
			'@context': 'https://schema.org/',
			'@type': 'Product',
			name: product.title,
			image: [product.image, ...(product.images || [])],
			description: product.description,
			sku: product.id,
			brand: {
				'@type': 'Brand',
				name: data.settings.siteName
			},
			offers: {
				'@type': 'Offer',
				url: $page.url.href,
				priceCurrency: 'USD',
				price: product.priceValue || 0,
				availability:
					product.stockStatus === 'out_of_stock'
						? 'https://schema.org/OutOfStock'
						: 'https://schema.org/InStock'
			}
		})
	);

	// Color Mapping Helper
	function getColorStyle(colorLabel: string) {
		const swatch = colorSwatchByLabel.get(colorLabel);
		if (swatch) return swatch;

		const c = colorLabel.toLowerCase();
		// Special overrides for better visibility/style
		if (c === 'black') return '#111111';
		if (c === 'white') return '#ffffff';
		if (c === 'grey' || c === 'gray') return '#888888';
		if (c === 'navy') return '#000080';

		// Allow raw CSS color values as a fallback (hex, rgb(), hsl(), oklch(), etc.)
		if (/^#([0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})$/i.test(colorLabel)) return colorLabel;
		if (/^(rgb|hsl|oklch|oklab)\(/i.test(colorLabel)) return colorLabel;

		// Safe visual fallback if no swatch is configured.
		return '#e5e5e5';
	}
</script>

<svelte:head>
	<title>{product.title} | {data.settings.siteName}</title>
	<meta name="description" content={product.description} />
	<meta property="og:image" content={product.image} />
	{@html `<script type="application/ld+json">${jsonLd}</script>`}
</svelte:head>

<div
	class="max-w-[1800px] mx-auto pt-24 pb-20 bg-background-light dark:bg-background-dark min-h-screen"
>
	<div class="lg:flex lg:gap-12 xl:gap-24">
		<!-- Left Column: Vertical Gallery -->
		<div class="lg:w-[60%] xl:w-[65%] flex flex-col gap-1 relative">
			<!-- Mobile: Horizontal Scroll Snap -->
			<div
				bind:this={galleryContainer}
				onscroll={handleGalleryScroll}
				class="flex lg:hidden overflow-x-auto snap-x snap-mandatory gap-1 scrollbar-hide relative"
			>
				{#each sortedImages as image, i (image)}
					<div class="shrink-0 w-full snap-center">
						<div class="aspect-[3/4] w-full relative">
							<RemoteImage
								src={image}
								alt="{product.title} view {i + 1}"
								className="w-full h-full object-cover"
								priority={i === 0}
							/>
						</div>
					</div>
				{/each}
			</div>

			<!-- Mobile Image Counter Badge REMOVED -->

			<!-- Mobile Pagination Bars -->
			{#if sortedImages.length > 1}
				<div class="lg:hidden flex justify-center gap-2 mt-4 px-4">
					{#each sortedImages as _, i}
						<div
							class="h-[2px] transition-all duration-300 rounded-full {i === currentImageIndex
								? 'bg-primary dark:bg-white w-8'
								: 'bg-primary/20 dark:bg-white/20 w-8'}"
						></div>
					{/each}
				</div>
			{/if}

			<!-- Desktop: Vertical Stack -->
			<div class="hidden lg:flex flex-col gap-1 w-full pl-6 md:pl-12">
				{#each sortedImages as image, i (image)}
					<div class="w-full relative">
						<RemoteImage
							src={image}
							alt="{product.title} view {i + 1}"
							className="w-full h-auto object-cover"
							priority={i <= 1}
						/>
					</div>
				{/each}
			</div>
		</div>

		<!-- Right Column: Sticky Product Info -->
		<div class="lg:w-[40%] xl:w-[35%] px-6 md:px-12 lg:px-0 lg:pr-12 mt-8 lg:mt-0">
			<div class="sticky top-24 lg:max-w-[400px]">
				<!-- Header Info -->
				<div class="mb-8 space-y-4">
					{#if product.categories && product.categories.length > 0}
						<div
							class="text-[10px] font-sans font-medium uppercase tracking-[0.2em] text-primary/50 dark:text-white/50 flex flex-wrap gap-2"
						>
							{#each product.categories as cat, i}
								<span>{cat.name}{i < product.categories.length - 1 ? ' ·' : ''}</span>
							{/each}
						</div>
					{/if}

					<h1 class="font-display text-3xl md:text-4xl text-primary dark:text-white leading-tight">
						{product.title}
					</h1>

					<div class="text-base font-sans text-primary dark:text-white">
						{product.price}
					</div>
				</div>

				<!-- Selectors -->
				<div class="mb-8 space-y-8">
					<!-- Colors -->
					{#if derivedColors && derivedColors.length > 0}
						<div class="space-y-3">
							<div class="flex flex-wrap gap-2">
								{#each derivedColors as color}
									<button
										class="w-10 h-10 rounded-full border border-gray-200 dark:border-white/20 flex items-center justify-center transition-all hover:scale-110 cursor-pointer {selectedColor ===
										color
											? 'ring-1 ring-offset-2 ring-primary dark:ring-white'
											: ''}"
										style="background-color: {getColorStyle(color)}"
										onclick={() => {
											selectedColor = color;
											selectedSize = '';
											sizeError = false;
										}}
										aria-label="Select color {color}"
									></button>
								{/each}
							</div>
						</div>
					{/if}

					<!-- Sizes -->
					<div class="space-y-3">
						<div class="grid grid-cols-4 gap-2">
							{#each availableSizes as item}
								{@const sizeLabel = (typeof item === 'string' ? item : item.size) || ''}
								{@const isOutOfStock = typeof item === 'object' && (item.stock || 0) <= 0}
								<button
									class="h-10 border text-[11px] font-sans font-medium transition-all {isOutOfStock
										? 'bg-transparent border-black text-black opacity-30 cursor-not-allowed pointer-events-none'
										: selectedSize === sizeLabel
											? 'bg-primary text-white border-black dark:bg-white dark:text-primary cursor-pointer'
											: 'border-black text-primary dark:text-white hover:bg-primary hover:text-white dark:hover:bg-white dark:hover:text-primary cursor-pointer'} {sizeError &&
									!selectedSize
										? 'animate-shake'
										: ''}"
									disabled={isOutOfStock}
									onclick={() => {
										selectedSize = sizeLabel;
										sizeError = false;
									}}
								>
									{sizeLabel}
								</button>
							{/each}
						</div>
						<div class="flex justify-end mt-3">
							<button
								class="text-[10px] uppercase tracking-[0.15em] text-primary dark:text-white hover:underline underline-offset-4 cursor-pointer"
								>Size Guide</button
							>
						</div>
					</div>
				</div>

				<!-- Actions -->
				<div class="flex gap-3 mb-10">
					<button
						onclick={addToBag}
						disabled={isAdding}
						class="flex-1 h-[46px] text-[11px] font-sans font-medium uppercase tracking-[0.2em] transition-all flex items-center justify-center cursor-pointer border {selectedSize
							? 'bg-primary text-white border-primary hover:opacity-90 dark:bg-white dark:text-primary dark:border-white'
							: 'bg-transparent text-primary border-primary hover:bg-primary hover:text-white dark:text-white dark:border-white dark:hover:bg-white dark:hover:text-primary'}"
					>
						{#if isAdding}
							<span
								class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"
							></span>
						{:else}
							ADD TO BAG
						{/if}
					</button>
					<button
						class="w-[46px] h-[46px] border border-primary dark:border-white flex items-center justify-center transition-colors hover:bg-primary hover:text-white dark:hover:bg-white dark:hover:text-primary group cursor-pointer"
						onclick={() => wishlist.toggle(product)}
						aria-label="Add to wishlist"
					>
						<span
							class="material-symbols-outlined text-[24px] font-light {wishlist.has(product.id)
								? 'font-fill'
								: ''}">favorite</span
						>
					</button>
				</div>

				<!-- Accordions / Info -->
				<div class="space-y-0">
					<!-- Description -->
					<div class="py-4">
						<div
							class="prose prose-sm dark:prose-invert max-w-none text-primary/80 dark:text-white/80 leading-relaxed"
						>
							<!-- eslint-disable-next-line svelte/no-at-html-tags -->
							{@html product.description}
						</div>
					</div>

					<!-- Material -->
					<details class="group py-4 cursor-pointer">
						<summary class="flex justify-between items-center list-none outline-none">
							<span class="text-[10px] uppercase tracking-[0.15em] font-medium"
								>Material & Care</span
							>
							<!-- Ultra-thin Vector Icon -->
							<svg
								width="18"
								height="18"
								viewBox="0 0 24 24"
								fill="none"
								xmlns="http://www.w3.org/2000/svg"
								class="transition-transform duration-300 group-open:rotate-45"
							>
								<path
									d="M12 4V20M4 12H20"
									stroke="currentColor"
									stroke-width="1"
									stroke-linecap="butt"
								/>
							</svg>
						</summary>
						<div class="pt-4 text-sm text-primary/70 dark:text-white/70 leading-relaxed">
							<ul class="list-disc pl-4 space-y-1">
								<ul class="list-disc pl-4 space-y-1">
									<!-- Attributes: details (array) -->
									{#if product.attributes?.details && Array.isArray(product.attributes.details)}
										{#each product.attributes.details as detail}
											<li>{detail}</li>
										{/each}
									{/if}

									<!-- Attributes: material (string) -->
									{#if product.attributes?.material}
										<li>{product.attributes.material}</li>
									{/if}

									<!-- Attributes: care (string) - New! -->
									{#if product.attributes?.care}
										<li>{product.attributes.care}</li>
									{/if}
								</ul>
							</ul>
						</div>
					</details>

					<!-- Shipping -->
					<details class="group py-4 cursor-pointer">
						<summary class="flex justify-between items-center list-none outline-none">
							<span class="text-[10px] uppercase tracking-[0.15em] font-medium"
								>Shipping & Returns</span
							>
							<!-- Ultra-thin Vector Icon -->
							<svg
								width="18"
								height="18"
								viewBox="0 0 24 24"
								fill="none"
								xmlns="http://www.w3.org/2000/svg"
								class="transition-transform duration-300 group-open:rotate-45"
							>
								<path
									d="M12 4V20M4 12H20"
									stroke="currentColor"
									stroke-width="1"
									stroke-linecap="butt"
								/>
							</svg>
						</summary>
						<div class="pt-4 text-sm text-primary/70 dark:text-white/70 leading-relaxed">
							<p>
								{product.attributes?.shipping ||
									'Free express shipping on all orders over $300. Returns accepted within 14 days.'}
							</p>
						</div>
					</details>
				</div>
			</div>
		</div>
	</div>

	<!-- Related Products -->
	{#if relatedProducts && relatedProducts.length > 0}
		<section class="max-w-[1600px] mx-auto px-6 md:px-12 mt-32 mb-16">
			<h3 class="font-display text-2xl mb-8 text-center uppercase tracking-widest">
				You May Also Like
			</h3>
			<ProductListGrid
				products={relatedProducts}
				variant="card"
				gridClass="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-12"
				cardWrapperClass=""
			/>
		</section>
	{/if}
</div>

<style>
	/* Hide scrollbar but keep functionality */
	.scrollbar-hide::-webkit-scrollbar {
		display: none;
	}
	.scrollbar-hide {
		-ms-overflow-style: none;
		scrollbar-width: none;
	}

	@keyframes shake {
		0%,
		100% {
			transform: translateX(0);
		}
		25% {
			transform: translateX(-4px);
		}
		75% {
			transform: translateX(4px);
		}
	}
	.animate-shake {
		animation: shake 0.3s cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
	}

	/* Font Fill for icons */
	.font-fill {
		font-variation-settings: 'FILL' 1;
	}

	details > summary::-webkit-details-marker {
		display: none;
	}
</style>
