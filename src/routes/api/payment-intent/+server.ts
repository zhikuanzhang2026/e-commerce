import { stripe } from '$lib/server/stripe';
import { resolveCheckoutProductWithClient } from '$lib/server/products';
import { validateAndApplyCouponWithClient } from '$lib/server/coupons';
import { STRIPE } from '$lib/constants';
import { Collections } from '$lib/pocketbase-types';
import type { RequestHandler } from './$types';
import type Stripe from 'stripe';
import { apiHandler } from '$lib/server/api-handler';
import type { ShippingAddress, CartItem } from '$lib/types';
import { withAdmin } from '$lib/server/admin';

/**
 * Helper: Find or create a Stripe Customer
 */
async function getOrCreateStripeCustomer(email: string, name: string, address: ShippingAddress) {
	if (!email) return null;

	try {
		// 1. Search for existing customer by email
		const existingCustomers = await stripe.customers.search({
			query: `email:'${email}'`,
			limit: 1
		});

		const addressParam = address
			? {
					line1: address.line1,
					line2: address.line2 || '',
					city: address.city,
					state: address.state,
					postal_code: address.postalCode,
					country: address.country
				}
			: undefined;

		if (existingCustomers.data.length > 0) {
			const customer = existingCustomers.data[0];
			// Update address if provided (to ensure tax calculation is accurate)
			if (addressParam) {
				await stripe.customers.update(customer.id, {
					name: name,
					address: addressParam,
					shipping: {
						name: name,
						address: addressParam
					}
				});
			}
			return customer.id;
		}

		// 2. Create new customer
		const newCustomer = await stripe.customers.create({
			email: email,
			name: name,
			address: addressParam,
			shipping: addressParam
				? {
						name: name,
						address: addressParam
					}
				: undefined
		});
		return newCustomer.id;
	} catch (e) {
		console.error('Failed to get/create Stripe customer:', e);
		return null;
	}
}

/**
 * Helper: Calculate tax using Stripe Tax API
 */
async function calculateTax(
	items: Array<{ id: string; title: string; quantity: number; priceCents: number }>,
	shippingAddress: ShippingAddress,
	currency: string
): Promise<{ taxAmountCents: number; calculationId: string | null }> {
	if (!shippingAddress || !shippingAddress.country) {
		return { taxAmountCents: 0, calculationId: null };
	}

	try {
		const lineItems = items.map((item) => ({
			amount: item.priceCents * item.quantity,
			quantity: item.quantity,
			reference: item.id,
			tax_behavior: 'exclusive' as const,
			tax_code: 'txcd_99999999'
		}));

		const taxCalculation = await stripe.tax.calculations.create({
			currency: currency.toLowerCase(),
			line_items: lineItems,
			customer_details: {
				address: {
					line1: shippingAddress.line1 || '',
					line2: shippingAddress.line2 || '',
					city: shippingAddress.city || '',
					state: shippingAddress.state || '',
					postal_code: shippingAddress.postalCode || '',
					country: shippingAddress.country || 'US'
				},
				address_source: 'shipping'
			}
		});

		return {
			taxAmountCents: taxCalculation.tax_amount_exclusive || 0,
			calculationId: taxCalculation.id
		};
	} catch (e: unknown) {
		console.error('Tax calculation failed:', e instanceof Error ? e.message : String(e));
		return { taxAmountCents: 0, calculationId: null };
	}
}

export const POST: RequestHandler = apiHandler(async ({ request }) => {
	const { items, couponCode, shippingInfo, customerInfo, shippingOptionId } = await request.json();

	if (!items || !Array.isArray(items) || items.length === 0) {
		throw { status: 400, message: 'Invalid items' };
	}

	return withAdmin(async (pb) => {
		// Calculate total amount on the server side (in cents)
		// SECURITY: Fetch price from DB instead of trusting client
		let amount = 0;
		const orderItemsForWebhook: Array<{
			id: string;
			productId: string;
			variantId: string | null;
			title: string;
			price: number; // cents
			quantity: number;
			skuSnap?: string;
			color: string;
			size: string;
			image: string;
		}> = [];
		const itemsWithPrice: Array<{
			id: string;
			productId: string;
			title: string;
			quantity: number;
			priceCents: number;
		}> = [];

		for (const rawItem of items as CartItem[]) {
			const itemId = typeof rawItem?.id === 'string' ? rawItem.id : '';
			const quantity =
				typeof rawItem?.quantity === 'number' ? rawItem.quantity : Number(rawItem?.quantity);
			const variantIdRaw = typeof rawItem?.variantId === 'string' ? rawItem.variantId.trim() : '';
			const variantId = variantIdRaw.length > 0 ? variantIdRaw : null;

			if (!itemId) {
				throw { status: 400, message: 'Invalid item id' };
			}
			if (!Number.isFinite(quantity) || quantity <= 0) {
				throw { status: 400, message: `Invalid quantity for item: ${itemId}` };
			}

			const resolved = await resolveCheckoutProductWithClient(pb, itemId);
			if (!resolved) {
				throw {
					status: 400,
					message: `Item not available: ${itemId}. Please remove it from your cart.`
				};
			}

			const { product, recordId } = resolved;
			const variant = variantId ? product.variants?.find((v) => v.id === variantId) : undefined;

			// Variants: enforce selection + validate ownership.
			if (product.hasVariants && !variantId) {
				throw {
					status: 400,
					message: `Please select a variant for ${product.title}.`
				};
			}
			if (variantId && !variant) {
				throw {
					status: 400,
					message: `Invalid variant selected for ${product.title}. Please remove it from your cart.`
				};
			}

			// Stock check (best-effort pre-check; final deduction must be idempotent on webhook).
			if (variant) {
				const stockQty = Number(variant.stockQuantity || 0);
				if (stockQty < quantity) {
					throw {
						status: 400,
						message: `Item out of stock: ${product.title}. Please remove it from your cart.`
					};
				}
			} else if (product.stockStatus === 'out_of_stock') {
				throw {
					status: 400,
					message: `Item out of stock: ${product.title}. Please remove it from your cart.`
				};
			}

			const unitPrice =
				typeof variant?.priceOverride === 'number' ? variant.priceOverride : product.priceValue;
			const priceCents = Math.round(unitPrice * 100);
			if (!Number.isFinite(priceCents) || priceCents <= 0) {
				throw {
					status: 400,
					message: `Invalid price for item: ${product.title}. Please remove it from your cart.`
				};
			}

			amount += priceCents * quantity;

			const color = variant?.color || rawItem.color || 'Standard';
			const size = variant?.size || rawItem.size || 'Generic';
			const image = variant?.image || product.image || rawItem.image || '';

			itemsWithPrice.push({
				id: itemId,
				productId: recordId,
				title: product.title,
				quantity,
				priceCents
			});

			orderItemsForWebhook.push({
				id: itemId,
				productId: recordId,
				variantId,
				title: product.title,
				price: priceCents,
				quantity,
				skuSnap: variant?.sku,
				color,
				size,
				image
			});
		}

		const subtotal = amount;
		const shippingOption = typeof shippingOptionId === 'string' ? shippingOptionId : 'standard';
		const shippingAmountCents = shippingOption === 'express' ? 2500 : 0;

		// Apply Coupon Logic
		if (couponCode) {
			const couponResult = await validateAndApplyCouponWithClient(pb, couponCode, amount);
			if (couponResult.valid && couponResult.discountCents > 0) {
				amount = Math.max(STRIPE.MIN_CHARGE_CENTS, amount - couponResult.discountCents);
			}
		}

		const discountAppliedCents = Math.max(0, subtotal - amount);

		if (amount < STRIPE.MIN_CHARGE_CENTS) {
			throw { status: 400, message: 'Amount too small' };
		}

		const currency = customerInfo?.currency || 'usd';
		if (!STRIPE.SUPPORTED_CURRENCIES.includes(currency.toUpperCase())) {
			throw { status: 400, message: 'Unsupported currency' };
		}

		// --- Step 1: Resolve Customer ---
		let customerId: string | null = null;
		if (customerInfo?.userId) {
			try {
				const userRecord = await pb.collection(Collections.Users).getOne(customerInfo.userId);
				const existing = (userRecord as unknown as { stripe_customer_id?: string })
					.stripe_customer_id;
				if (typeof existing === 'string' && existing.length > 0) {
					customerId = existing;
				}
			} catch {
				// Ignore and fall back to email search.
			}
		}

		if (!customerId && customerInfo?.email && shippingInfo) {
			customerId = await getOrCreateStripeCustomer(
				customerInfo.email,
				customerInfo.name || 'Guest',
				shippingInfo
			);
		}

		// Persist Stripe customer ID for logged-in users.
		if (customerInfo?.userId && customerId) {
			try {
				await pb.collection(Collections.Users).update(customerInfo.userId, {
					stripe_customer_id: customerId
				});
			} catch {
				// Non-fatal: continue checkout even if we can't store it.
			}
		}

		// --- Step 2: Calculate Tax ---
		let taxAmountCents = 0;
		let taxCalculationId: string | null = null;

		if (shippingInfo) {
			console.log('[PaymentIntent] Calculating tax', {
				country: shippingInfo.country
			});
			const taxResult = await calculateTax(itemsWithPrice, shippingInfo, currency);
			taxAmountCents = taxResult.taxAmountCents;
			taxCalculationId = taxResult.calculationId;
		}

		const totalAmount = amount + taxAmountCents + shippingAmountCents;

		// Optional: capture the user's cart record id so n8n can delete it without listing user_lists.
		let cartRecordId = '';
		if (customerInfo?.userId) {
			try {
				const pbAny = pb as unknown as {
					filter?: (query: string, params: Record<string, unknown>) => string;
				};
				const filter = pbAny.filter
					? pbAny.filter('user = {:userId} && type = {:type}', {
							userId: customerInfo.userId,
							type: 'cart'
						})
					: `user="${customerInfo.userId}" && type="cart"`;
				const cart = await pb.collection(Collections.UserLists).getFirstListItem(filter, {
					fields: 'id'
				});
				cartRecordId = cart.id;
			} catch {
				// Ignore (cart might not exist or read might fail); do not block checkout.
			}
		}

		// --- Step 3: Build order data for n8n webhook ---
		// Store complete order info in metadata so n8n can create the order
		const orderData = {
			placed_at_override: new Date().toISOString(),
			cart_record_id: cartRecordId,
			user_id: customerInfo?.userId || '',
			customer_email: customerInfo?.email || '',
			customer_name: customerInfo?.name || 'Guest',
			items: orderItemsForWebhook,
			amount_subtotal: subtotal,
			amount_shipping: shippingAmountCents,
			amount_tax: taxAmountCents,
			amount_total: totalAmount,
			currency: currency.toLowerCase(),
			shipping_address: shippingInfo || {},
			coupon_code: couponCode || ''
		};

		// --- Step 4: Create PaymentIntent ---
		// NOTE: Order creation is handled by n8n webhook on payment_intent.succeeded
		const orderDataString = JSON.stringify(orderData);
		const maxMetadataLen = 500;
		const orderDataParts: string[] = [];
		for (let i = 0; i < orderDataString.length; i += maxMetadataLen) {
			orderDataParts.push(orderDataString.slice(i, i + maxMetadataLen));
		}

		const params: Stripe.PaymentIntentCreateParams = {
			amount: totalAmount,
			currency: currency.toLowerCase(),
			automatic_payment_methods: {
				enabled: true
			},
			metadata: {
				// Summary for Stripe Dashboard
				items_summary: orderItemsForWebhook
					.map((i) => `${i.quantity}x ${i.title}`)
					.join(', ')
					.substring(0, 500),
				// Full order data for n8n (JSON encoded, split into parts to fit metadata limits)
				order_data_parts: String(orderDataParts.length),
				...Object.fromEntries(
					orderDataParts.map((part, index) => [`order_data_part_${index + 1}`, part])
				),
				// Individual fields for easy n8n access
				user_id: customerInfo?.userId || '',
				cart_record_id: cartRecordId,
				placed_at_override: orderData.placed_at_override,
				coupon_code: couponCode || '',
				tax_calculation_id: taxCalculationId || ''
			}
		};

		if (customerId) {
			params.customer = customerId;
		}

		console.log('[PaymentIntent] Creating intent (order will be created by n8n webhook)');
		const paymentIntent = await stripe.paymentIntents.create(params);

		return {
			clientSecret: paymentIntent.client_secret,
			subtotalAmount: subtotal / 100,
			discountAmount: discountAppliedCents / 100,
			shippingAmount: shippingAmountCents / 100,
			taxAmount: taxAmountCents / 100,
			totalAmount: totalAmount / 100
		};
	});
});
