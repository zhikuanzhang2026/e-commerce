import requests
import sys
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Usage: python3 seed_data.py <pb_url> <admin_email> <admin_pass>
# Example: python3 seed_data.py http://127.0.0.1:8090/_/ admin@example.com 123456


def seed_data(base_url, email, password):
    print(f"🚀 Seeding data to {base_url}...")

    # Authenticate (PB 0.23+ Superusers)
    auth_url = f"{base_url.rstrip('/')}/api/collections/_superusers/auth-with-password"
    try:
        resp = requests.post(
            auth_url, json={"identity": email, "password": password}, verify=False
        )
        resp.raise_for_status()
        token = resp.json()["token"]
        print("✅ Authentication successful.")
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        return

    headers = {"Authorization": f"{token}"}

    # Helper function to get or create
    def ensure_record(collection, check_filter, data):
        list_url = f"{base_url.rstrip('/')}/api/collections/{collection}/records?filter=({check_filter})"
        existing = (
            requests.get(list_url, headers=headers, verify=False)
            .json()
            .get("items", [])
        )
        if existing:
            print(f"  - {collection}: Found existing '{check_filter.split('=')[1]}'")
            return existing[0]

        create_url = f"{base_url.rstrip('/')}/api/collections/{collection}/records"
        created = requests.post(create_url, json=data, headers=headers, verify=False)
        if created.status_code == 200:
            print(f"  ✅ {collection}: Created '{check_filter.split('=')[1]}'")
            return created.json()
        else:
            print(f"  ❌ {collection}: Failed to create. {created.text}")
            return None

    # 1. Categories
    cat_mens = ensure_record(
        "categories",
        "slug='mens-wear'",
        {
            "name": "Men's Wear",
            "slug": "mens-wear",
            "sort_order": 10,
            "is_visible": True,
        },
    )
    cat_womens = ensure_record(
        "categories",
        "slug='womens-wear'",
        {
            "name": "Women's Wear",
            "slug": "womens-wear",
            "sort_order": 20,
            "is_visible": True,
        },
    )

    # 2. Products
    if cat_mens:
        ensure_record(
            "products",
            "slug='essential-tee'",
            {
                "title": "Essential Cotton Tee",
                "slug": "essential-tee",
                "category": cat_mens["id"],
                "stripe_price_id": "price_mock_123",
                # Note: File upload via JSON API is complex, skipping actual binary upload for seed.
                # In real usage, you'd use multipart/form-data.
                "description": "A premium cotton t-shirt.",
            },
        )

    # 3. Global Settings
    ensure_record(
        "global_settings",
        "site_name='ELEMENTHIC'",
        {
            "site_name": "ELEMENTHIC",
            "currency_symbol": "$",
            "currency_code": "USD",
            "shipping_threshold": 200,
        },
    )

    # 4. Navigation
    ensure_record(
        "navigation",
        "url='/shop'",
        {
            "location": "header",
            "label": "Shop",
            "url": "/shop",
            "order": 10,
            "is_visible": True,
        },
    )
    ensure_record(
        "navigation",
        "url='/about'",
        {
            "location": "footer",
            "label": "About Us",
            "url": "/about",
            "order": 10,
            "is_visible": True,
        },
    )

    # 5. Pages
    page_home = ensure_record(
        "pages",
        "slug='home'",
        {"slug": "home", "title": "ELEMENTHIC", "is_published": True},
    )

    # 6. UI Sections (Hero on Home)
    if page_home:
        # Check by heading as we don't have unique slug for sections
        list_url = f"{base_url.rstrip('/')}/api/collections/ui_sections/records?filter=(heading='Welcome to Elementhic')"
        existing = (
            requests.get(list_url, headers=headers, verify=False)
            .json()
            .get("items", [])
        )
        if not existing:
            requests.post(
                f"{base_url.rstrip('/')}/api/collections/ui_sections/records",
                json={
                    "page": page_home["id"],
                    "type": "hero",
                    "heading": "Welcome to Elementhic",
                    "subheading": "Premium generic lifestyle.",
                    "cta_text": "Explore",
                    "cta_link": "/shop",
                    "sort_order": 10,
                    "sort_order": 10,
                    "is_active": True,
                },
                headers=headers,
                verify=False,
            )
            print("  ✅ ui_sections: Created Hero Banner")
        else:
            print("  - ui_sections: Hero Banner exists")

    # 7. Collection Images
    # Using multipart/form-data for image upload mock
    # Since we can't easily upload local binary files without them existing, we'll create records without files first
    # Or rely on admin UI to upload images.

    # Let's clean up existing if any to avoid duplicates logic complexity for this specific case or just check

    ensure_record(
        "collection_images",
        "position='left'",
        {
            "title": "Woman > New Arrivals",
            "position": "left",
            "link": "/shop?gender=womens",
            "active": True,
        },
    )

    ensure_record(
        "collection_images",
        "position='right'",
        {
            "title": "Shop Man",
            "position": "right",
            "link": "/shop?gender=mens",
            "active": True,
        },
    )

    print("\n✨ Seeding complete.")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 seed_data.py <url> <email> <password>")
    else:
        seed_data(sys.argv[1], sys.argv[2], sys.argv[3])
