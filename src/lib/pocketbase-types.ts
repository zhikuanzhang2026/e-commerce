/**
 * This file was @generated using pocketbase-typegen
 */

import type PocketBase from 'pocketbase';
import type { RecordService } from 'pocketbase';

export enum Collections {
	Authorigins = '_authOrigins',
	Externalauths = '_externalAuths',
	Mfas = '_mfas',
	Otps = '_otps',
	Superusers = '_superusers',
	Categories = 'categories',
	CollectionImages = 'collection_images',
	Coupons = 'coupons',
	GlobalSettings = 'global_settings',
	Navigation = 'navigation',
	OrderItems = 'order_items',
	Orders = 'orders',
	Pages = 'pages',
	ProductVariants = 'product_variants',
	Products = 'products',
	UiAssets = 'ui_assets',
	UiSections = 'ui_sections',
	UserAddresses = 'user_addresses',
	UserLists = 'user_lists',
	Users = 'users'
}

// Alias types for improved usability
export type IsoDateString = string;
export type IsoAutoDateString = string & { readonly autodate: unique symbol };
export type RecordIdString = string;
export type FileNameString = string & { readonly filename: unique symbol };
export type HTMLString = string;

type ExpandType<T> = unknown extends T
	? T extends unknown
		? { expand?: unknown }
		: { expand: T }
	: { expand: T };

// System fields
export type BaseSystemFields<T = unknown> = {
	id: RecordIdString;
	collectionId: string;
	collectionName: Collections;
} & ExpandType<T>;

export type AuthSystemFields<T = unknown> = {
	email: string;
	emailVisibility: boolean;
	username: string;
	verified: boolean;
} & BaseSystemFields<T>;

// Record types for each collection

export type AuthoriginsRecord = {
	collectionRef: string;
	created: IsoAutoDateString;
	fingerprint: string;
	id: string;
	recordRef: string;
	updated: IsoAutoDateString;
};

export type ExternalauthsRecord = {
	collectionRef: string;
	created: IsoAutoDateString;
	id: string;
	provider: string;
	providerId: string;
	recordRef: string;
	updated: IsoAutoDateString;
};

export type MfasRecord = {
	collectionRef: string;
	created: IsoAutoDateString;
	id: string;
	method: string;
	recordRef: string;
	updated: IsoAutoDateString;
};

export type OtpsRecord = {
	collectionRef: string;
	created: IsoAutoDateString;
	id: string;
	password: string;
	recordRef: string;
	sentTo?: string;
	updated: IsoAutoDateString;
};

export type SuperusersRecord = {
	created: IsoAutoDateString;
	email: string;
	emailVisibility?: boolean;
	id: string;
	password: string;
	tokenKey: string;
	updated: IsoAutoDateString;
	verified?: boolean;
};

export type CategoriesRecord = {
	description?: string;
	id: string;
	image?: FileNameString;
	is_visible?: boolean;
	name: string;
	slug: string;
	sort_order?: number;
};

export enum CollectionImagesPositionOptions {
	'left' = 'left',
	'right' = 'right'
}
export type CollectionImagesRecord = {
	active?: boolean;
	id: string;
	image?: FileNameString;
	label?: string;
	link?: string;
	position: CollectionImagesPositionOptions;
	title: string;
};

export enum CouponsTypeOptions {
	'percentage' = 'percentage',
	'fixed_amount' = 'fixed_amount'
}
export type CouponsRecord = {
	code: string;
	expire_date?: IsoDateString;
	id: string;
	is_active: boolean;
	min_order_amount?: number;
	type: CouponsTypeOptions;
	usage_count?: number;
	usage_limit?: number;
	value: number;
};

export type GlobalSettingsRecord = {
	currency_code: string;
	currency_symbol: string;
	icon?: FileNameString;
	id: string;
	maintenance_mode?: boolean;
	shipping_threshold?: number;
	site_name: string;
};

export enum NavigationLocationOptions {
	'header' = 'header',
	'footer' = 'footer',
	'mobile' = 'mobile'
}
export type NavigationRecord = {
	id: string;
	is_visible?: boolean;
	label: string;
	location?: NavigationLocationOptions;
	order?: number;
	parent?: RecordIdString;
	url: string;
};

export type OrderItemsRecord<Tvariant_snap_json = unknown> = {
	id: string;
	image_snap?: string;
	order_id: RecordIdString;
	price_snap: number;
	product_id?: RecordIdString;
	product_title_snap: string;
	quantity: number;
	sku_snap?: string;
	variant_id?: RecordIdString;
	variant_snap_json?: null | Tvariant_snap_json;
};

export enum OrdersStatusOptions {
	'pending' = 'pending',
	'paid' = 'paid',
	'processing' = 'processing',
	'shipped' = 'shipped',
	'delivered' = 'delivered',
	'cancelled' = 'cancelled'
}
export type OrdersRecord<Titems = unknown, Tshipping_address = unknown> = {
	amount_shipping?: number;
	amount_subtotal?: number;
	amount_tax?: number;
	amount_total?: number;
	currency?: string;
	customer_email?: string;
	customer_name?: string;
	id: string;
	items?: null | Titems;
	notes?: string;
	placed_at: IsoAutoDateString;
	placed_at_override?: IsoDateString;
	shipping_address?: null | Tshipping_address;
	status?: OrdersStatusOptions;
	stripe_payment_intent?: string;
	stripe_session_id?: string;
	tracking_carrier?: string;
	tracking_number?: string;
	user?: RecordIdString;
};

export type PagesRecord = {
	content?: HTMLString;
	hero_image?: FileNameString;
	id: string;
	meta_description?: string;
	og_image?: FileNameString;
	slug: string;
	title?: string;
};

export type ProductVariantsRecord = {
	color: string;
	color_swatch?: string;
	gallery_images?: FileNameString[];
	id: string;
	product: RecordIdString;
	size: string;
	sku: string;
	stock_quantity: number;
};
export type ProductsRecord<Tattributes = unknown> = {
	attributes?: null | Tattributes;
	category?: RecordIdString[];
	description?: HTMLString;
	id: string;
	is_featured?: boolean;
	main_image?: FileNameString;
	slug: string;
	stripe_price_id?: string;
	stripe_product_id?: string;
	title: string;
};

export enum UiAssetsGroupOptions {
	'home' = 'home',
	'about' = 'about',
	'cart' = 'cart',
	'wishlist' = 'wishlist',
	'common' = 'common'
}
export type UiAssetsRecord = {
	alt_text?: string;
	description?: string;
	group?: UiAssetsGroupOptions;
	id: string;
	image?: FileNameString;
	key: string;
};

export enum UiSectionsTypeOptions {
	'hero' = 'hero',
	'feature_split' = 'feature_split',
	'product_grid' = 'product_grid',
	'rich_text' = 'rich_text',
	'cta_banner' = 'cta_banner',
	'category_grid' = 'category_grid'
}
export type UiSectionsRecord<Tsettings = unknown> = {
	content?: HTMLString;
	heading?: string;
	id: string;
	image?: FileNameString[];
	is_active?: boolean;
	page?: RecordIdString;
	schedule_end?: IsoDateString;
	schedule_start?: IsoDateString;
	settings?: null | Tsettings;
	sort_order?: number;
	subheading?: string;
	type?: UiSectionsTypeOptions;
	video?: FileNameString;
};

export type UserAddressesRecord = {
	city?: string;
	country?: string;
	id: string;
	label?: string;
	line1?: string;
	line2?: string;
	phone?: string;
	postal_code?: string;
	recipient_name?: string;
	state?: string;
	user?: RecordIdString;
};

export enum UserListsTypeOptions {
	'cart' = 'cart',
	'wishlist' = 'wishlist',
	'save_for_later' = 'save_for_later'
}
export type UserListsRecord<Titems = unknown> = {
	id: string;
	items: null | Titems;
	type: UserListsTypeOptions;
	user: RecordIdString;
};

export type UsersRecord = {
	default_shipping_address?: RecordIdString;
	email: string;
	emailVisibility?: boolean;
	id: string;
	password: string;
	stripe_customer_id?: string;
	tokenKey: string;
	verified?: boolean;
};

// Response types include system fields and match responses from the PocketBase API
export type AuthoriginsResponse<Texpand = unknown> = Required<AuthoriginsRecord> &
	BaseSystemFields<Texpand>;
export type ExternalauthsResponse<Texpand = unknown> = Required<ExternalauthsRecord> &
	BaseSystemFields<Texpand>;
export type MfasResponse<Texpand = unknown> = Required<MfasRecord> & BaseSystemFields<Texpand>;
export type OtpsResponse<Texpand = unknown> = Required<OtpsRecord> & BaseSystemFields<Texpand>;
export type SuperusersResponse<Texpand = unknown> = Required<SuperusersRecord> &
	AuthSystemFields<Texpand>;
export type CategoriesResponse<Texpand = unknown> = Required<CategoriesRecord> &
	BaseSystemFields<Texpand>;
export type CollectionImagesResponse<Texpand = unknown> = Required<CollectionImagesRecord> &
	BaseSystemFields<Texpand>;
export type CouponsResponse<Texpand = unknown> = Required<CouponsRecord> &
	BaseSystemFields<Texpand>;
export type GlobalSettingsResponse<Texpand = unknown> = Required<GlobalSettingsRecord> &
	BaseSystemFields<Texpand>;
export type NavigationResponse<Texpand = unknown> = Required<NavigationRecord> &
	BaseSystemFields<Texpand>;
export type OrderItemsResponse<Tvariant_snap_json = unknown, Texpand = unknown> = Required<
	OrderItemsRecord<Tvariant_snap_json>
> &
	BaseSystemFields<Texpand>;
export type OrdersResponse<
	Titems = unknown,
	Tshipping_address = unknown,
	Texpand = unknown
> = Required<OrdersRecord<Titems, Tshipping_address>> & BaseSystemFields<Texpand>;
export type PagesResponse<Texpand = unknown> = Required<PagesRecord> & BaseSystemFields<Texpand>;
export type ProductVariantsResponse<Texpand = unknown> = Required<ProductVariantsRecord> &
	BaseSystemFields<Texpand>;
export type ProductsResponse<Tattributes = unknown, Texpand = unknown> = Required<
	ProductsRecord<Tattributes>
> &
	BaseSystemFields<Texpand>;
export type UiAssetsResponse<Texpand = unknown> = Required<UiAssetsRecord> &
	BaseSystemFields<Texpand>;
export type UiSectionsResponse<Tsettings = unknown, Texpand = unknown> = Required<
	UiSectionsRecord<Tsettings>
> &
	BaseSystemFields<Texpand>;
export type UserAddressesResponse<Texpand = unknown> = Required<UserAddressesRecord> &
	BaseSystemFields<Texpand>;
export type UserListsResponse<Titems = unknown, Texpand = unknown> = Required<
	UserListsRecord<Titems>
> &
	BaseSystemFields<Texpand>;
export type UsersResponse<Texpand = unknown> = Required<UsersRecord> & AuthSystemFields<Texpand>;

// Types containing all Records and Responses, useful for creating typing helper functions

export type CollectionRecords = {
	_authOrigins: AuthoriginsRecord;
	_externalAuths: ExternalauthsRecord;
	_mfas: MfasRecord;
	_otps: OtpsRecord;
	_superusers: SuperusersRecord;
	categories: CategoriesRecord;
	collection_images: CollectionImagesRecord;
	coupons: CouponsRecord;
	global_settings: GlobalSettingsRecord;
	navigation: NavigationRecord;
	order_items: OrderItemsRecord;
	orders: OrdersRecord;
	pages: PagesRecord;
	product_variants: ProductVariantsRecord;
	products: ProductsRecord;
	ui_assets: UiAssetsRecord;
	ui_sections: UiSectionsRecord;
	user_addresses: UserAddressesRecord;
	user_lists: UserListsRecord;
	users: UsersRecord;
};

export type CollectionResponses = {
	_authOrigins: AuthoriginsResponse;
	_externalAuths: ExternalauthsResponse;
	_mfas: MfasResponse;
	_otps: OtpsResponse;
	_superusers: SuperusersResponse;
	categories: CategoriesResponse;
	collection_images: CollectionImagesResponse;
	coupons: CouponsResponse;
	global_settings: GlobalSettingsResponse;
	navigation: NavigationResponse;
	order_items: OrderItemsResponse;
	orders: OrdersResponse;
	pages: PagesResponse;
	product_variants: ProductVariantsResponse;
	products: ProductsResponse;
	ui_assets: UiAssetsResponse;
	ui_sections: UiSectionsResponse;
	user_addresses: UserAddressesResponse;
	user_lists: UserListsResponse;
	users: UsersResponse;
};

// Utility types for create/update operations

type ProcessCreateAndUpdateFields<T> = Omit<
	{
		// Omit AutoDate fields
		[K in keyof T as Extract<T[K], IsoAutoDateString> extends never
			? K
			: never]: T[K] extends infer U // Convert FileNameString to File
			? U extends FileNameString | FileNameString[]
				? U extends any[]
					? File[]
					: File
				: U
			: never;
	},
	'id'
>;

// Create type for Auth collections
export type CreateAuth<T> = {
	id?: RecordIdString;
	email: string;
	emailVisibility?: boolean;
	password: string;
	passwordConfirm: string;
	verified?: boolean;
} & ProcessCreateAndUpdateFields<T>;

// Create type for Base collections
export type CreateBase<T> = {
	id?: RecordIdString;
} & ProcessCreateAndUpdateFields<T>;

// Update type for Auth collections
export type UpdateAuth<T> = Partial<
	Omit<ProcessCreateAndUpdateFields<T>, keyof AuthSystemFields>
> & {
	email?: string;
	emailVisibility?: boolean;
	oldPassword?: string;
	password?: string;
	passwordConfirm?: string;
	verified?: boolean;
};

// Update type for Base collections
export type UpdateBase<T> = Partial<Omit<ProcessCreateAndUpdateFields<T>, keyof BaseSystemFields>>;

// Get the correct create type for any collection
export type Create<T extends keyof CollectionResponses> =
	CollectionResponses[T] extends AuthSystemFields
		? CreateAuth<CollectionRecords[T]>
		: CreateBase<CollectionRecords[T]>;

// Get the correct update type for any collection
export type Update<T extends keyof CollectionResponses> =
	CollectionResponses[T] extends AuthSystemFields
		? UpdateAuth<CollectionRecords[T]>
		: UpdateBase<CollectionRecords[T]>;

// Type for usage with type asserted PocketBase instance
// https://github.com/pocketbase/js-sdk#specify-typescript-definitions

export type TypedPocketBase = {
	collection<T extends keyof CollectionResponses>(
		idOrName: T
	): RecordService<CollectionResponses[T]>;
} & PocketBase;
