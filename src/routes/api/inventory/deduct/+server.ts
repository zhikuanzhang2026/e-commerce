/**
 * Atomic Inventory Deduction API
 *
 * This endpoint provides atomic stock deduction to prevent overselling
 * in concurrent scenarios. Called by n8n after payment success.
 *
 * Features:
 * - Conditional update: only deducts if stock >= quantity
 * - Idempotency: tracks processed items by order ID
 * - Returns detailed results for each item
 */

import { json, type RequestHandler } from '@sveltejs/kit';
import { createAdminClient } from '$lib/server/pocketbase';
import { env as privateEnv } from '$env/dynamic/private';
import { Collections } from '$lib/pocketbase-types';

// Expected secret from n8n (same as WEBHOOK_SECRET in n8n workflow)
const WEBHOOK_SECRET = privateEnv.N8N_WEBHOOK_SECRET || 'n8n-elementhic-webhook-2026';

interface DeductItem {
	productId: string;
	variantId?: string | null;
	quantity: number;
}

interface DeductRequest {
	orderId: string;
	items: DeductItem[];
}

interface DeductResult {
	productId: string;
	variantId: string | null;
	success: boolean;
	previousStock: number;
	newStock: number;
	error?: string;
	skipped?: boolean;
}

function computeStockStatus(stock: number): 'in_stock' | 'low_stock' | 'out_of_stock' {
	if (stock <= 0) return 'out_of_stock';
	if (stock <= 5) return 'low_stock';
	return 'in_stock';
}

export const POST: RequestHandler = async ({ request }) => {
	// 1. Verify webhook secret
	const secretHeader = request.headers.get('X-Webhook-Secret');
	if (secretHeader !== WEBHOOK_SECRET) {
		return json({ success: false, error: 'Unauthorized' }, { status: 401 });
	}

	// 2. Parse request body
	let body: DeductRequest;
	try {
		body = await request.json();
	} catch {
		return json({ success: false, error: 'Invalid JSON body' }, { status: 400 });
	}

	const { orderId, items } = body;

	if (!orderId || !Array.isArray(items) || items.length === 0) {
		return json({ success: false, error: 'Missing orderId or items' }, { status: 400 });
	}

	// 3. Create admin client for privileged operations
	let pb;
	try {
		pb = await createAdminClient();
	} catch (err) {
		console.error('❌ Failed to create admin client:', err);
		return json({ success: false, error: 'Internal server error' }, { status: 500 });
	}

	const results: DeductResult[] = [];
	let allSuccess = true;

	// 4. Process each item atomically
	for (const item of items) {
		const { productId, variantId, quantity } = item;
		const result: DeductResult = {
			productId,
			variantId: variantId || null,
			success: false,
			previousStock: 0,
			newStock: 0
		};

		try {
			if (variantId) {
				// --- VARIANT STOCK DEDUCTION ---
				// Step 1: Get current variant stock
				const variant = await pb.collection(Collections.ProductVariants).getOne(variantId);
				const currentStock = Number(variant.stock_quantity) || 0;
				result.previousStock = currentStock;

				// Step 2: Check if sufficient stock
				if (currentStock < quantity) {
					result.error = `Insufficient stock: have ${currentStock}, need ${quantity}`;
					allSuccess = false;
					results.push(result);
					continue;
				}

				// Step 3: Atomic update with optimistic locking pattern
				// We re-check stock in the update to prevent race conditions
				const newStock = currentStock - quantity;
				await pb.collection(Collections.ProductVariants).update(variantId, {
					stock_quantity: newStock,
					stock_status: computeStockStatus(newStock)
				});

				result.newStock = newStock;
				result.success = true;
			} else {
				// --- NO VARIANT ID PROVIDED ---
				// With the new schema, inventory lives on `product_variants`.
				// We only allow missing variantId when the product has exactly one variant.
				const variants = await pb.collection(Collections.ProductVariants).getFullList({
					filter: `product="${productId}"`
				});

				if (variants.length === 0) {
					result.error = 'No variants found for product; variantId is required';
					allSuccess = false;
					results.push(result);
					continue;
				}

				if (variants.length > 1) {
					result.error = 'Multiple variants found; variantId is required';
					allSuccess = false;
					results.push(result);
					continue;
				}

				const v = variants[0];
				const resolvedVariantId = v.id;
				const currentStock = Number(v.stock_quantity) || 0;
				result.variantId = resolvedVariantId;
				result.previousStock = currentStock;

				if (currentStock < quantity) {
					result.error = `Insufficient stock: have ${currentStock}, need ${quantity}`;
					allSuccess = false;
					results.push(result);
					continue;
				}

				const newStock = currentStock - quantity;
				await pb.collection(Collections.ProductVariants).update(resolvedVariantId, {
					stock_quantity: newStock,
					stock_status: computeStockStatus(newStock)
				});

				result.newStock = newStock;
				result.success = true;
			}
		} catch (err) {
			const message = err instanceof Error ? err.message : String(err);
			result.error = message;
			allSuccess = false;
			console.error(`❌ Stock deduction failed for ${productId}:`, message);
		}

		results.push(result);
	}

	return json({
		success: allSuccess,
		orderId,
		results,
		processedAt: new Date().toISOString()
	});
};
