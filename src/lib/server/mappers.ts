/**
 * PocketBase Record Mappers
 * 统一的数据映射工具函数，用于将 PocketBase 记录转换为前端类型
 */

import { getFileUrl } from './pocketbase';
import { computeStockStatus } from './stock-status';
import type { Product, Category, ProductVariant } from '$lib/types';
import type {
	ProductsResponse,
	CategoriesResponse,
	ProductVariantsResponse
} from '$lib/pocketbase-types';

// =============================================================================
// Gender Mapping
// =============================================================================

/**
 * Map database gender value to frontend type
 */
export function mapGender(dbGender: string): 'mens' | 'womens' | 'unisex' {
	if (dbGender === 'men' || dbGender === 'mens') return 'mens';
	if (dbGender === 'women' || dbGender === 'womens') return 'womens';
	return 'unisex';
}

// =============================================================================
// Product Mapping
// =============================================================================

/**
 * Map a PocketBase product record to frontend Product type
 */
export function mapRecordToProduct(record: ProductsResponse, categories?: Category[]): Product {
	const collectionId = record.collectionId || 'products';
	const recordId = record.id;

	const mainImage = record.main_image ? getFileUrl(collectionId, recordId, record.main_image) : '';

	// Map Variants from Expanded Relation
	type ProductExpand = { 'product_variants(product)'?: ProductVariantsResponse[] };
	const expandedVariants = (record.expand as unknown as ProductExpand | undefined)?.[
		'product_variants(product)'
	];
	const rawVariants = mapVariantsFromExpand(expandedVariants);

	// Media normalization:
	// For the same (product,color), images are intended to be shared across sizes.
	// Only one "media" variant needs to store the images; others can be blank.
	const mediaByColor = new Map<
		string,
		{
			image?: string;
			galleryImages: string[];
		}
	>();
	for (const v of rawVariants) {
		const galleryImages = Array.isArray(v.galleryImages) ? v.galleryImages.filter(Boolean) : [];
		const image = v.image || galleryImages[0] || undefined;
		if (!image && galleryImages.length === 0) continue;

		const existing = mediaByColor.get(v.color);
		if (!existing) {
			mediaByColor.set(v.color, { image, galleryImages });
			continue;
		}

		const existingGalleryLen = existing.galleryImages?.length || 0;
		if (galleryImages.length > existingGalleryLen) {
			mediaByColor.set(v.color, { image, galleryImages });
			continue;
		}
		if (!existing.image && image) {
			mediaByColor.set(v.color, { image, galleryImages: existing.galleryImages });
		}
	}

	const variants = rawVariants.map((v) => {
		const media = mediaByColor.get(v.color);
		if (!media) return v;

		const hasGallery = Array.isArray(v.galleryImages) && v.galleryImages.length > 0;
		const galleryImages = hasGallery
			? v.galleryImages
			: media.galleryImages.length > 0
				? media.galleryImages
				: v.galleryImages;
		const image = v.image || media.image || galleryImages?.[0] || undefined;

		return {
			...v,
			galleryImages,
			image
		};
	});

	const hasVariants = variants.length > 0;

	// Determine base image(s). With the new schema, galleries live on variants.
	let baseImage = mainImage;
	if (!baseImage) {
		const firstVariant = variants[0];
		baseImage = firstVariant?.image || firstVariant?.galleryImages?.[0] || '';
	}
	const baseImages = baseImage ? [baseImage] : [];

	const totalVariantStock = variants.reduce((sum, v) => sum + (Number(v.stockQuantity) || 0), 0);
	const stockStatus = hasVariants ? computeStockStatus(totalVariantStock) : 'out_of_stock';

	// Handle categoryIds - can be string or array
	const rawCategoryIds = record.category;
	const categoryIds = Array.isArray(rawCategoryIds)
		? rawCategoryIds
		: rawCategoryIds
			? [rawCategoryIds]
			: [];

	// Derive gender from categories since it's no longer a direct field
	let gender: 'mens' | 'womens' | 'unisex' = 'unisex';
	if (categories) {
		if (categories.some((c) => c.slug === 'mens' || c.slug === 'men')) gender = 'mens';
		else if (categories.some((c) => c.slug === 'womens' || c.slug === 'women')) gender = 'womens';
	}

	// Omit attributes from spread to handle null-check manually
	// const { attributes, ...rest } = record;

	return {
		// Base Identity
		id: record.slug || record.id,
		collectionId: collectionId,
		collectionName: record.collectionName,

		// Core Data
		title: record.title,
		slug: record.slug,
		description: record.description,

		// Frontend Specific / Computed
		price: 'Loading...',
		priceValue: 0,
		image: baseImage,
		images: baseImages,

		variants: hasVariants ? variants : undefined,
		categories: categories,
		categoryIds: categoryIds,

		attributes: (record.attributes as Record<string, unknown>) || {},

		// Status Flags
		isFeature: !!record.is_featured,
		hasVariants: hasVariants,
		stockStatus: stockStatus,
		gender: gender,

		stripePriceId: record.stripe_price_id
		// tag: record.tag // Not in PB types yet
	};
}

/**
 * Map expanded variants from PocketBase relation
 */
export function mapVariantsFromExpand(
	expandedVariants: ProductVariantsResponse[] | undefined
): ProductVariant[] {
	if (!expandedVariants) return [];

	return expandedVariants.map((v) => {
		const galleryImages: string[] = Array.isArray(v.gallery_images)
			? v.gallery_images.map((img) => getFileUrl(v.collectionId, v.id, img))
			: [];
		const image = galleryImages[0] || undefined;

		return {
			id: v.id,
			collectionId: v.collectionId,
			collectionName: v.collectionName,

			product: v.product,
			color: v.color,
			colorSwatch: v.color_swatch || undefined,
			size: v.size,
			sku: v.sku,
			galleryImages,
			stockStatus: computeStockStatus(Number(v.stock_quantity) || 0),

			// Mapped
			image,
			stockQuantity: v.stock_quantity
		};
	});
}

// =============================================================================
// Category Mapping
// =============================================================================

/**
 * Map a PocketBase category record to frontend Category type
 */
export function mapRecordToCategory(record: CategoriesResponse): Category {
	return {
		id: record.id,
		collectionId: record.collectionId,
		collectionName: record.collectionName,

		title: record.name,
		name: record.name,
		slug: record.slug,

		// Mapped fields
		image: record.image ? getFileUrl('categories', record.id, record.image) : undefined,
		isVisible: !!record.is_visible,
		sortOrder: record.sort_order || 0
	};
}

/**
 * Map expanded category from product record (single)
 */
export function mapCategoryFromExpand(
	expandedCategory: CategoriesResponse | undefined
): Category | undefined {
	if (!expandedCategory) return undefined;

	return {
		id: expandedCategory.id,
		collectionId: expandedCategory.collectionId,
		collectionName: expandedCategory.collectionName,

		title: expandedCategory.name,
		slug: expandedCategory.slug,

		image: expandedCategory.image
			? getFileUrl('categories', expandedCategory.id, expandedCategory.image)
			: undefined,
		isVisible: !!expandedCategory.is_visible,
		sortOrder: expandedCategory.sort_order || 0
	};
}

/**
 * Map expanded categories from product record (array - for multi-select)
 */
export function mapCategoriesFromExpand(
	expandedCategories: CategoriesResponse | CategoriesResponse[] | undefined
): Category[] {
	if (!expandedCategories) return [];

	// Handle both single object and array
	const categoriesArray = Array.isArray(expandedCategories)
		? expandedCategories
		: [expandedCategories];

	return categoriesArray
		.filter((c) => c != null)
		.map((c) => ({
			id: c.id,
			collectionId: c.collectionId,
			collectionName: c.collectionName,

			title: c.name,
			slug: c.slug,

			image: c.image ? getFileUrl('categories', c.id, c.image) : undefined,
			isVisible: !!c.is_visible,
			sortOrder: c.sort_order || 0
		}));
}
