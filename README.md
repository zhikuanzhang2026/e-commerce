# ELEMENTHIC | 高端 Headless 电商平台

ELEMENTHIC 是一个基于 **SvelteKit 2 + Svelte 5** 构建的现代化高性能电商平台，采用 **PocketBase** 作为全能后端的 "Vibe" 架构设计。本项目严格遵循 **Apple UX (Minimal Luxury)** 设计风格与 **Spec-Driven Development** 开发范式。

---

## 🏗️ 核心架构 (The "Luxury Vibe" Stack)

项目采用 **三层数据驱动架构 (Three-Tier Data Architecture)**，确保极致的性能与运营灵活性：

| 组件 | 职责 | 存储核心 |
|------|------|----------|
| **SvelteKit 2** | **缝合器 (The Gluer)** | SSR 渲染、服务端业务逻辑 (Server Hooks Auth Sync) 与 Webhook 调度。 |
| **PocketBase** | **全能后端 (CMS + DB)** | 三层存储：核心展示层、运营统计层、JSON 扩展层。 |
| **Stripe** | **财务大脑 (FinGate)** | 价格源头、支付状态机、库存同步引擎、自动税务计算。 |
| **Spec Kit** | **开发管理 (The Spec)** | 通过规范驱动开发，标准化需求、计划与任务流。 |

---

## 🛠️ 技术栈 (Technology Stack)

- **前端**: Svelte 5 (Runes) + Tailwind CSS v4 (CSS-first)
- **状态管理**: TanStack Query v6 (Server Sync) + Svelte 5 Runes
- **表单**: Superforms + Zod (Type-safe Validation)
- **后端**: PocketBase (SQLite / Go) + Rate Limiting
- **支付**: Stripe Connect / Elements / Tax (Automatic VAT/Sales Tax)
- **工作流**: n8n（以实例内工作流为准：`Elementhic Stripe Order`、`Elementhic-Stripe to PocketBase Sync`）
- **测试**: Playwright (E2E) + Vitest (Unit)
- **代码质量**: ESLint 9 + Prettier 3 + Husky + lint-staged
- **开发工具**: OpenCode / Antigravity + GitHub Spec Kit

---

## 🧬 开发范式：规范驱动 (Spec-Driven Development)

本项目采用 GitHub **Spec Kit** 流程，拒绝“感性编程”（Vibe Coding），所有功能迭代（包括 UI、后端逻辑、自动化流）遵循以下链路：

1.  **Constitution (宪法)**: `.specify/memory/constitution.md` 定义了项目的核心原则（如 Svelte 5 强制规范、Apple UX 风格、OCC 库存锁）。
2.  **Specify (规范)**: 建立领域模型，定义系统边界与非功能性需求（安全性、并发性）。
3.  **Plan (计划)**: 确定技术实现方案并进行 AI 架构审计。
4.  **Implement (实现)**: 由 AI 代理（OpenCode）根据拆解的任务清单执行编码。

### 常用指令 (OpenCode Slash Commands)
在 OpenCode 聊天框输入以下指令开始协作：
- `/speckit.specify` - 创建功能规范 (架构&业务导向)
- `/speckit.plan` - 制定技术计划
- `/speckit.tasks` - 拆解具体任务
- `/speckit.implement` - 执行代码实现

### 质量保证指令 (Quality Assurance)
- `npm run lint` - 运行 ESLint 静态代码分析
- `npm run lint:fix` - 自动修复 ESLint 警告/错误
- `npm run format` - 运行 Prettier 格式化代码
- `npm run check` - 运行 svelte-check 类型与模板检查

---

## 📂 项目文档 (Documentation)

| 文档 | 说明 |
|------|------|
| [📜 项目宪法](.specify/memory/constitution.md) | **最高准则**: 包含核心规范、架构原则与代码准则 |
| [🎯 功能规范](specs/) | 包含 [001-UX进化](specs/001-ux-evolution/spec.md), [002-购物车召回](specs/002-cart-recovery/spec.md), [004-订单历史](specs/004-003-order-history/spec.md) 等 |
| [⚡ 原子 API 指南](.agent/docs/atomic-api-guide.md) | 库存扣减与优惠券递增的原子操作 API |
| [🔐 .env.example](./.env.example) | 环境变量配置与安全准则 |

---

## 🧱 数据模型约定（当前）

- `products`：承载商品主信息与 Stripe 映射（`stripe_product_id` / `stripe_price_id`），并作为统一价格来源。
- `product_variants`：承载规格与库存（`sku`、`color`、`size`、`stock_quantity`）及规格媒体（`gallery_images` / `color_swatch`）。
- `price_override` 不再使用（已移除），变体不再参与独立定价。
- `stock_status` 不再落库，运行时由 `stock_quantity` 动态计算。
- 规格媒体按颜色复用：`gallery_images` 只需在同色一个规格记录维护，前端以第一张作为主图并同色回退。
- `sku` 当前按变体唯一管理（建议格式：`<STYLE>-<COLOR>-<SIZE>`）。

---

## 🚀 快速开始

### 1. 安装依赖与工具
```bash
# 克隆与安装
git clone <repo-url>
cd e-commerce
npm install

# （可选）若你要使用 Spec Kit 的 Python/uv 工作流，再安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装 Playwright 浏览器 (用于测试)
npx playwright install
```

### 2. 配置环境变量
```bash
cp .env.example .env
```

### 3. 启动开发服务器
```bash
# 先准备 PocketBase 二进制（仓库默认不内置）
# 1) 从 PocketBase Releases 下载对应系统版本并解压
# 2) 将可执行文件放到项目根目录后授权
chmod +x ./pocketbase

# 启动 PocketBase
./pocketbase serve

# 启动前端
npm run dev
```

### 4. 运行测试
```bash
# 运行单元测试
npm run test

# 运行 E2E 测试 (Checkout Flow)
npm run test:e2e
```

---

## 📊 项目进度 (Roadmap)

> 详细的任务分解见各 Feature 分支下的同步 Spec。

### ✅ Phase 12: 深度工程化重构 (Completed)
- [x] **State Management 2.0**: 引入 TanStack Query v6。
- [x] **Spec-Driven Integration**: 引入 Spec Kit 标准化工作流。

### 🔄 Phase 13: 体验与自动化进化 (In Progress)
- [x] **Core Architecture Audit**: 完成服务端认证 (Hooks) 修复与安全性审计 (npm audit 0 vulnerabilities)。
- [x] **Universal Spec Template**: 升级规范模板，支持领域建模。
- [x] **UX Evolution**: 引入 Apple Spring 动画曲线与 Toast 组件重构。
- [x] **Checkout & Payment**: 完整的 Stripe Elements 支付流程，服务端价格计算与 Webhook 处理。

### ✅ Phase 14: 代码质量与工程化体系 (Completed)
- [x] **Linting & Formatting**: 引入 ESLint 9 与 Prettier 3 统一代码规范。
- [x] **Git Hooks**: 配置 Husky + lint-staged 在提交前强制执行格式化与静态检查。
- [x] **Code Review Guide**: 建立书面审查指南，自动化并标准化代码质量评估。
- [x] **Technical Debt Fix**: 修复 100+ 编译警告与潜在逻辑隐患。
- [x] **Type Safety**: 核心业务逻辑实现 95%+ 的严格类型覆盖（Stripe, Orders, Cart）。

### 🔄 Phase 15: 体验与自动化进化 (In Progress)
- [ ] **002-Cart Recovery**: 建立基于 Stripe Webhook + n8n 的废弃购物车召回系统。

---

## 🎨 设计系统 (Apple UX Style)

项目使用 Tailwind CSS v4，严格遵守 HSL 动态调色与现代排版：

```css
@theme {
    /* 核心原则：高对比度、清晰的层级、丝滑的动画 */
    --font-sans: "Manrope", system-ui, sans-serif;
    --font-display: "Optima", "Cinzel", serif;
    
    /* 动画：优先使用 GPU 加速属性 */
    --ease-apple-spring: cubic-bezier(0.16, 1, 0.3, 1);
}
```

---

## 📜 License

MIT

---

*Built with ❤️ using SvelteKit, Spec Kit, and OpenCode*
