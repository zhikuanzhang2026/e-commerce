# ELEMENTHIC CMS 使用手册

> **Version:** 3.0 (Balanced Architecture)
> **Last Updated:** 2026-01-23
> **Backend:** PocketBase
> **Admin URL:** `https://pb.elementhic.com/_/`

---

## 📖 目录

1. [快速上手](#-快速上手)
2. [Site 模块 - 站点配置](#-site-模块---站点配置)
   - [Global Settings (全局配置)](#1-global-settings-全局配置)
   - [Navigation (导航菜单)](#2-navigation-导航菜单)
3. [Content 模块 - 页面内容](#-content-模块---页面内容)
   - [Pages (页面元数据)](#3-pages-页面元数据)
   - [UI Sections (页面区块)](#4-ui-sections-页面区块)
   - [UI Assets / Media Library (资源库)](#5-ui-assets-静态资源库)
4. [Commerce 模块 - 电商核心](#-commerce-模块---电商核心)
   - [Categories (商品分类)](#6-categories-商品分类)
   - [Products (商品)](#7-products-商品)
   - [Product Variants (SKU 管理)](#8-product-variants-商品规格库存)
   - [Orders (订单记录)](#9-orders-订单记录)
5. [System 模块 - 用户与权限](#-system-模块---用户与权限)
   - [Users (用户)](#10-users-用户)
   - [User Addresses (收货地址)](#11-user-addresses-收货地址)
   - [User Lists (购物车/收藏夹)](#12-user-lists-购物车收藏夹)
6. [区块类型详解](#-区块类型详解)
7. [集合关系图](#-集合关系图)
8. [常见问题](#-常见问题)

---

## 🚀 快速上手

### 登录后台

1. 访问 **PocketBase Admin UI**: `https://pb.elementhic.com/_/`
2. 使用管理员账号登录
3. 左侧菜单即为所有集合（Collections）

### 核心操作

| 操作 | 位置 | 说明 |
|:---|:---|:---|
| **添加记录** | 集合页面 → "New Record" | 创建新数据 |
| **编辑记录** | 点击记录行 | 修改现有数据 |
| **删除记录** | 记录详情 → 右上角 "Delete" | ⚠️ 不可恢复 |
| **搜索/筛选** | 集合页面顶部搜索框 | 按字段搜索 |

### 发布流程

1. 在后台修改/添加数据
2. 保存后，前端**自动更新**（无需手动部署）
3. 如未生效，请刷新浏览器清除缓存

---

## 🔄 混合驱动 (Stripe ↔ PB) 同步逻辑

系统采用 **Stripe 主导财务，PocketBase 主导内容** 的混合驱动模式。

### 1. 自动镜像逻辑
*   **创建**: 在 Stripe Dashboard 创建新商品后，系统会通过 Webhook 自动在 PB 创建一个同名记录，并自动相互关联 ID。
*   **同步**: Stripe 中的 `Active/Archived` 状态会影响 PB 的可售状态（当前由 `product_variants.stock_status` 驱动）。
*   **删除**: Stripe 中删除商品后，PB 记录将自动标记为 `out_of_stock` 以保持数据完整性。

### 2. ID 绑定规则
| 系统 | 位置 | 说明 |
|:---|:---|:---|
| **Stripe** | `metadata.pb_product_id` | 存储 PocketBase 的原始记录 ID。 |
| **PocketBase** | `stripe_price_id` | 存储 Stripe 默认价格 ID，用于发起结账。 |

### 3. 操作建议流
1.  **开店**: 先在 Stripe Dashboard 创建商品，设定价格。
2.  **装修**: 等待 1-2 秒后，在 PocketBase 中找到自动生成的记录，上传高清大图并编写富文本详情。
3.  **上/下架**: 统一在 Stripe Dashboard 操作开关。

---

## 🏗️ Site 模块 - 站点配置

### 1. Global Settings (全局配置)

**集合名称:** `global_settings`  
**用途:** 存储网站的基础信息，如名称、货币、运费政策等。

> ⚠️ **重要更新 (v2.3):** 图片字段已移除，现统一通过 `ui_assets` 集合管理。

#### 字段说明

| 字段名 | 类型 | 必填 | 示例值 | 说明 |
|:---|:---|:---|:---|:---|
| `site_name` | Text | ✅ | `ELEMENTHIC` | 网站名称，显示在标题栏和 Logo 处 |
| `currency_symbol` | Text | ✅ | `$` | 货币符号 |
| `currency_code` | Text | ✅ | `USD` | 货币代码（ISO 4217） |
| `shipping_threshold` | Number | ✅ | `300` | 免邮金额门槛（单位：美元） |
| `maintenance_mode` | Bool | ❌ | `false` | 开启后网站显示维护页面 |

#### 使用示例

```
site_name: ELEMENTHIC
currency_symbol: $
currency_code: USD
shipping_threshold: 300
maintenance_mode: false
```

---

### 2. Navigation (导航菜单)

**集合名称:** `navigation`  
**用途:** 管理网站的导航栏、页脚链接等。

#### 字段说明

| 字段名 | 类型 | 必填 | 示例值 | 说明 |
|:---|:---|:---|:---|:---|
| `location` | Select | ✅ | `header` | 菜单位置：`header`(顶部)、`footer`(底部)、`mobile`(移动端) |
| `label` | Text | ✅ | `COLLECTIONS` | 显示的文字 |
| `url` | Text | ✅ | `/shop` | 点击后跳转的链接 |
| `order` | Number | ✅ | `10` | 排序权重（数字越小越靠前） |
| `parent` | Relation | ❌ | - | 父菜单（用于创建二级下拉菜单） |
| `is_visible` | Bool | ❌ | `true` | 是否显示 |

> ⚠️ **注意**: `navigation` 集合现仅负责管理按钮显示的文字（Label）。页面的实际 H1 大标题统一由 `pages` 集合中的 `title` 字段驱动。

---

## 🎨 Content 模块 - 页面内容

### 3. Pages (页面元数据)

**集合名称:** `pages`  
**用途:** 定义网站的各个页面及其 SEO 信息，是**页面标题（H1）和元数据**的唯一事实来源。

#### 字段说明

| 字段名 | 类型 | 必填 | 示例值 | 说明 |
|:---|:---|:---|:---|:---|
| `slug` | Text | ✅ | `about` | 页面 URL 标识（需唯一）。 |
| `title` | Text | ✅ | `About Us` | 页面标题。前端将此值作为 `<h1>` 和浏览器标签标题展示。 |
| `meta_description` | Text | ❌ | `Learn about our story...` | 搜索引擎描述（SEO）。 |
| `og_image` | File | ❌ | (上传图片) | 社交分享时显示的图片。 |
| `content` | Editor | ❌ | (富文本) | 页面正文内容（Markdown/HTML）。 |

#### 💡 核心逻辑：标题与元数据驱动
系统采用 **Slug 匹配机制**。当访问商店或合辑页面时，程序会根据查询参数（gender/category）自动寻找对应的 Page 记录。

#### 预设页面

| slug | 说明 | 对应 URL |
|:---|:---|:---|
| `home` | 首页 | `/` |
| `about` | 关于我们 | `/about` |
| `contact` | 联系我们 | `/contact` |
| `journal` | 日志/博客 | `/journal` |
| `privacy-policy` | 隐私政策 | `/privacy-policy` |
| `terms` | 服务条款 | `/terms` |
| `shipping-returns` | 运输与退换 | `/returns` |

---

### 4. UI Sections (页面区块)

**集合名称:** `ui_sections`  
**用途:** 定义页面上的可视化区块（如 Hero 大图、分类网格等）。

> 💡 **核心概念:** 每个区块都有一个 `type`，前端会根据 `type` 自动选择对应的组件进行渲染。

#### 字段说明

| 字段名 | 类型 | 必填 | 示例值 | 说明 |
|:---|:---|:---|:---|:---|
| `page` | Relation | ✅ | → `home` | 所属页面 |
| `type` | Select | ✅ | `hero` | 区块类型（见下方详解） |
| `heading` | Text | ❌ | `ELEMENTHIC FOR YOUR LIVING` | 主标题 |
| `subheading` | Text | ❌ | `Core Collection 2024` | 副标题 |
| `content` | Editor | ❌ | (富文本) | 正文内容 |
| `image` | File | ❌ | (多文件上传) | 区块图片。如果是 Hero 类型，第一张为背景，多张则自动形成幻灯片。 |
| `video` | File | ❌ | (上传视频) | 视频背景文件 (MP4/WebM)。优先于图片显示。 |
| `settings` | JSON | ❌ | `{ "actions": [...], "external": {...} }` | **核心配置字段** |
| `sort_order` | Number | ✅ | `10` | 排序权重（越小越靠前） |
| `is_active` | Bool | ❌ | `True` | 是否显示 |
| `schedule_start` | Date | ❌ | - | 自动上线时间 |
| `schedule_end` | Date | ❌ | - | 自动下线时间 |

---

### 5. UI Assets (静态资源库)

**集合名称:** `ui_assets`  
**用途:** 存储网站各处使用的静态图片/图标资源。

#### 字段说明

| 字段名 | 类型 | 必填 | 示例值 | 说明 |
|:---|:---|:---|:---|:---|
| `key` | Text | ✅ | `hero_category_mens` | **唯一标识符**，代码中通过此 Key 引用 |
| `group` | Select | ✅ | `home` | 分组（Home, About, Cart 等） |
| `image` | File | ✅ | `upload.jpg` | **直接上传图片文件** |
| `alt_text` | Text | ❌ | `Men's Collection` | 图片 Alt 描述 |

---

## 🛍️ Commerce 模块 - 电商核心

### 6. Categories (商品分类)

**集合名称:** `categories`  
**用途:** 定义商品的分类体系。

#### 字段说明

| 字段名 | 类型 | 必填 | 示例值 | 说明 |
|:---|:---|:---|:---|:---|
| `name` | Text | ✅ | `Tops` | 分类名称 |
| `slug` | Text | ✅ | `tops` | URL 路径（**必须唯一**，已建索引） |
| `description` | Text | ❌ | `T-shirts, Shirts...` | 分类描述 |
| `image` | File | ❌ | (上传图片) | 分类封面图 |
| `sort_order` | Number | ✅ | `10` | 排序权重 |
| `is_visible` | Bool | ❌ | `True` | 是否启用在前端显示 |

---

### 7. Products (商品)

**集合名称:** `products`  
**用途:** 存储所有商品的通用信息（展示层）。

> ⚠️ **架构更新 (v3.0):** 
> 1. `colors`, `sizes`, `shipping_info` 字段已**移除**。
> 2. `attributes` JSON 字段用于存储非核心属性。
> 3. 库存和具体 SKU 管理在 `product_variants` 集合。

#### 字段说明

| 字段名 | 类型 | 必填 | 示例值 | 说明 |
|:---|:---|:---|:---|:---|
| `title` | Text | ✅ | `Heavyweight Hoodie` | 商品名称 |
| `slug` | Text | ✅ | `heavyweight-hoodie` | URL 标识 |
| `category` | Relation | ✅ | → `ready-to-wear` | 所属分类 |
| `stripe_price_id` | Text | ✅ | `price_1ABC...` | Stripe Price ID (基础价格) |
| `main_image` | File | ✅ | (上传图片) | 商品主图 |
| `gallery_images` | (Moved) | - | - | 已迁移到 `product_variants.gallery_images` |
| `description` | Editor | ❌ | (富文本) | 商品描述 |
| `attributes` | JSON | ❌ | `{"material": "Cotton"}` | 商品属性 (材质、版型等) |
| `is_featured` | Bool | ❌ | `true` | 是否在首页推荐 |
| `has_variants` | (Removed) | - | - | 由是否存在 `product_variants` 自动推导 |
| `stock_status` | (Moved) | - | - | 已迁移到 `product_variants.stock_status` |

---

### 8. Product Variants (商品规格/库存)

**集合名称:** `product_variants`  
**用途:** 存储具体规格的 SKU、价格和库存（强关联模式）。

> ✅ **媒体去重规则（强烈建议）**
> - 同一商品同一颜色的图片通常不随尺码变化。
> - 只在该颜色组的 **一个** 规格记录上上传 `main_image`/`gallery_images`（推荐最小尺码）。
> - 其他尺码记录保持媒体字段为空，前端会自动回退到同色媒体。

#### 字段说明

| 字段名 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| `product` | Relation | ✅ | 关联的主商品 |
| `sku` | Text | ✅ | 变体唯一 SKU（建议：`<STYLE>-<COLOR>-<SIZE>`，用于订单/发货/对账） |
| `color` | Text | ✅ | 颜色标签（前端展示名，如 Midnight Navy） |
| `color_swatch` | Text | ❌ | 色块颜色（Hex/CSS，例如 #111111） |
| `size` | Text | ✅ | 尺寸 (如 M, L, XL) |
| `price_override` | Number | ❌ | **规格特价** (若留空则使用商品基础价格) |
| `stock_status` | Select | ❌ | `in_stock` | 库存状态 (由 `stock_quantity` 推导，可脚本校准) |
| `stock_quantity` | Number | ✅ | **当前库存** (Source of Truth) |
| `main_image` | File | ❌ | 规格主图（可选，用于该规格的首图/封面） |
| `gallery_images` | File | ❌ | 规格画廊（多图，用于商品详情轮播） |

---

### 9. Orders (订单记录)

**集合名称:** `orders`  
**用途:** 记录用户的订单信息。

> ⚠️ **快照原则**: 订单的 `items` 字段是下单时刻的 **JSON 快照**。即使商品后续改名或涨价，此快照**永不改变**。前端只通过此 JSON 渲染历史订单。

#### 字段说明

| 字段名 | 类型 | 说明 |
|:---|:---|:---|
| `user` | Relation | 下单用户 |
| `items` | JSON | **Snapshot** (Product Info + Price + Variant) |
| `status` | Select | 订单状态 (pending, paid, shipped, etc.) |
| `shipping_address` | JSON | **Snapshot** (Address + Recipient) |
| `amount_total` | Number | 总金额（单位：美分） |
| `tracking_number` | Text | 快递单号 |

---

## 👤 System 模块 - 用户与权限

### 10. Users (用户)

**集合名称:** `users`  
**类型:** Auth Collection（PocketBase 内置）

扩展字段：
- `display_name`, `avatar`, `stripe_customer_id`, `default_shipping_address`

---

### 11. User Addresses (收货地址)

**集合名称:** `user_addresses`  
**用途:** 存储用户的收货地址。

#### 字段说明

| 字段名 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| `user` | Relation | ✅ | 所属用户 |
| `label` | Text | ❌ | 标签 (Home, Office) |
| `recipient_name` | Text | ✅ | 收件人姓名 |
| `line1`, `city`, `postal_code`, `country` | Text | ✅ | 地址详情 |

---

### 12. User Lists (购物车/收藏夹)

**集合名称:** `user_lists`  
**用途:** 统一存储用户的购物车和愿望单数据。

> ℹ️ **说明:** 替代了旧版的 `carts` 和 `wishlists` 集合。

#### 字段说明

| 字段名 | 类型 | 必填 | 说明 |
|:---|:---|:---|:---|
| `user` | Relation | ✅ | 所属用户 |
| `type` | Select | ✅ | `cart` 或 `wishlist` |
| `items` | JSON | ✅ | 商品列表 |

#### Items JSON 结构 (Lite)
```json
[
  {
    "productId": "prod_123",
    "variantId": "var_456",
    "quantity": 2
  }
]
```
*注意：不存价格，价格需实时查询。*

---

## 📝 更新日志

| 版本 | 日期 | 更新内容 |
|:---|:---|:---|
| v3.0 | 2026-01-23 | **架构平衡重构**: 合并 User Lists；Products 引入 attributes JSON；强化 Order 快照机制；增加 content_ops AI 接口。 |
| v2.7 | 2026-01-23 | 架构解耦: 明确 navigation 与 pages 职责。 |
| v1.0 | 2025-12-01 | 初始版本。 |

---

> 📧 **技术支持:** support@elementhic.com
