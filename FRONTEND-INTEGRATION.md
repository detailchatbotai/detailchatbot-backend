# DetailChatbot.ai Frontend Integration Guide

**Complete guide for building the frontend dashboard for DetailChatbot.ai - an AI chatbot system for auto detailing shops.**

## 🎯 Project Overview

**Business Model**: SaaS platform where auto detailing shops pay monthly subscriptions to embed AI chatbots on their websites.

**Revenue Goal**: $5,000/month profit by January 2025

**Current Status**: 
- ✅ Backend API is production-ready and deployed
- ✅ Widget system works and generates revenue-ready embeddable code
- ✅ Stripe billing integration complete
- 🚧 Need frontend dashboard for shop owners

---

## 🏗️ System Architecture

### **Backend API** (Already Built)
- **URL**: `https://detailchatbot-api-dev.onrender.com` (dev) / `https://detailchatbot-api.onrender.com` (prod)
- **Tech**: FastAPI + PostgreSQL + Stripe + OpenAI
- **Documentation**: `/docs` endpoint (Swagger UI)

### **Frontend Needed** (Your Job)
- **Purpose**: Dashboard for shop owners to manage their chatbot
- **Users**: Auto detailing shop owners (B2B SaaS)
- **Tech Stack**: Recommended Next.js 14 + Tailwind CSS + TypeScript

---

## 🔐 Authentication System

### **JWT Token Flow**
```javascript
// 1. User Registration
POST /api/v1/auth/register
{
  "email": "shop@example.com",
  "password": "SecurePass123!"
}

// Response
{
  "message": "User created successfully",
  "user": {
    "id": 1,
    "email": "shop@example.com",
    "is_verified": false
  }
}

// 2. User Login
POST /api/v1/auth/login
{
  "email": "shop@example.com", 
  "password": "SecurePass123!"
}

// Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "shop@example.com",
    "is_verified": true
  }
}

// 3. Authenticated Requests
Headers: {
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### **Token Management**
- **Access Token**: 30 minutes (use for API calls)
- **Refresh Token**: 7 days (use to get new access tokens)
- **Storage**: localStorage for dev, httpOnly cookies for prod

---

## 🏪 Shop Management System

### **Shop Creation Flow**
```javascript
// Create Shop (after login)
POST /api/v1/shops
Headers: { "Authorization": "Bearer ACCESS_TOKEN" }
{
  "name": "Premium Auto Detailing",
  "address": "123 Main St, City, ST 12345", 
  "phone": "(555) 123-4567",
  "primary_color": "#007bff",
  "secondary_color": "#6c757d",
  "greeting_message": "Welcome! How can we help make your car shine?"
}

// Response
{
  "id": 1,
  "name": "Premium Auto Detailing",
  "address": "123 Main St, City, ST 12345",
  "phone": "(555) 123-4567", 
  "public_api_key": "dc_pub_abc123...",
  "private_api_key": "dc_pri_xyz789...",
  "primary_color": "#007bff",
  "secondary_color": "#6c757d",
  "greeting_message": "Welcome! How can we help make your car shine?",
  "plan_id": 1,
  "subscription_status": "trial",
  "created_at": "2024-01-01T12:00:00Z"
}
```

### **API Keys Explained**
- **Public Key** (`dc_pub_...`): Safe to show in UI, used in widget embed code
- **Private Key** (`dc_pri_...`): Secret, used for admin operations, hide in UI

---

## 🛠️ Service Management

### **Services CRUD**
```javascript
// Add Service
POST /api/v1/services
Headers: { "Authorization": "Bearer ACCESS_TOKEN" }
{
  "name": "Interior Detailing",
  "description": "Complete interior cleaning and protection", 
  "price": 150.00,
  "duration_minutes": 90,
  "is_active": true,
  "is_addon": false
}

// Get Services
GET /api/v1/services
Headers: { "Authorization": "Bearer ACCESS_TOKEN" }

// Response: Array of services
[
  {
    "id": 1,
    "name": "Interior Detailing",
    "description": "Complete interior cleaning and protection",
    "price": 150.00,
    "duration_minutes": 90,
    "is_active": true,
    "is_addon": false,
    "shop_id": 1
  }
]
```

---

## 💳 Subscription & Billing

### **Available Plans**
```javascript
// Get Plans
GET /api/v1/plans

// Response
[
  {
    "id": 1,
    "name": "Starter",
    "price_monthly": 19.99,
    "price_yearly": 199.99,
    "max_chats_per_month": 500,
    "max_services": 5,
    "features": ["Basic AI", "Email Support"],
    "stripe_price_id_monthly": "price_1234...",
    "stripe_price_id_yearly": "price_5678..."
  },
  {
    "id": 2, 
    "name": "Pro",
    "price_monthly": 39.99,
    "price_yearly": 399.99,
    "max_chats_per_month": 2000,
    "max_services": 25,
    "features": ["Advanced AI", "Analytics", "Priority Support"],
    "stripe_price_id_monthly": "price_1Rq3WB8qw5OT74PHFTOf5dub",
    "stripe_price_id_yearly": "price_1Rq3WB8qw5OT74PHFTOf5dub_yearly"
  }
]
```

### **Subscription Flow**
```javascript
// Create Stripe Checkout Session
POST /api/v1/plans/subscribe
Headers: { "Authorization": "Bearer ACCESS_TOKEN" }
{
  "plan_id": 2,
  "billing_cycle": "monthly", // or "yearly"
  "success_url": "https://yourdashboard.com/success",
  "cancel_url": "https://yourdashboard.com/pricing"
}

// Response
{
  "checkout_url": "https://checkout.stripe.com/pay/cs_test_...",
  "session_id": "cs_test_..."
}

// Redirect user to checkout_url
window.location.href = checkout_url;
```

### **Usage Tracking**
```javascript
// Get Current Usage
GET /api/v1/plans/usage
Headers: { "Authorization": "Bearer ACCESS_TOKEN" }

// Response
{
  "current_plan": {
    "name": "Pro",
    "max_chats_per_month": 2000,
    "max_services": 25
  },
  "usage": {
    "chats_this_month": 450,
    "chats_remaining": 1550,
    "services_created": 8,
    "services_remaining": 17,
    "usage_percentage": 22.5
  },
  "billing_cycle_end": "2024-01-31T23:59:59Z"
}
```

### **Account Deletion**
```javascript
// Delete user account and all associated data
DELETE /api/v1/auth/delete-account
Headers: { "Authorization": "Bearer ACCESS_TOKEN" }

// Response
{
  "message": "Account deleted successfully"
}

// This will permanently delete:
// - User account
// - All shops owned by the user  
// - All services for those shops
// - All chat sessions and messages
// - Any active subscriptions (should cancel in Stripe too)
```

---

## 🤖 Widget Integration System

### **Get Widget Embed Code**
```javascript
// This is what you show shop owners in their dashboard
const embedCode = `<script src="https://detailchatbot-api-dev.onrender.com/api/v1/widget/${shop.public_api_key}/embed.js"></script>`;

// ⚠️ IMPORTANT: Your backend already handles everything!
// - Widget generation: ✅ Done
// - Chat API: ✅ /api/v1/chat/{shop_api_key} exists  
// - AI integration: ✅ OpenAI already connected
// - Configuration: ✅ Auto-configured from shop data

// NO CDN needed! Your API serves the widget directly.
// NO separate chat/message endpoint needed! Use existing chat endpoint.

// Widget customization options
GET /api/v1/widget/{public_api_key}/config

// Response
{
  "shop_name": "Premium Auto Detailing",
  "primary_color": "#007bff", 
  "secondary_color": "#6c757d",
  "greeting_message": "Welcome! How can we help?",
  "theme_options": ["light", "dark"],
  "position_options": ["bottom-right", "bottom-left"]
}
```

### **Widget Preview**
Create an iframe or preview component showing how the widget looks:
```html
<!-- Widget Preview in Dashboard -->
<iframe 
  src="/widget-preview?api_key=dc_pub_abc123&theme=light&position=bottom-right"
  width="400" 
  height="600"
  frameborder="0">
</iframe>
```

---

## 📊 Analytics & Chat History

### **Chat Analytics** 
```javascript
// Get Chat Statistics
GET /api/v1/analytics/chats?period=30days
Headers: { "Authorization": "Bearer ACCESS_TOKEN" }

// Response
{
  "total_chats": 1247,
  "total_sessions": 892,
  "average_messages_per_session": 4.2,
  "popular_topics": [
    {"topic": "pricing", "count": 234},
    {"topic": "services", "count": 189},
    {"topic": "booking", "count": 156}
  ],
  "daily_stats": [
    {"date": "2024-01-01", "chats": 45, "sessions": 32},
    {"date": "2024-01-02", "chats": 52, "sessions": 38}
  ]
}
```

### **Chat History**
```javascript
// Get Recent Chat Sessions
GET /api/v1/chat/history?limit=50
Headers: { "Authorization": "Bearer ACCESS_TOKEN" }

// Response
{
  "sessions": [
    {
      "session_id": "session_abc123",
      "created_at": "2024-01-15T14:30:00Z",
      "message_count": 6,
      "customer_ip": "192.168.1.1",
      "last_message": "Thanks! I'll call to book an appointment.",
      "messages": [
        {
          "message": "What services do you offer?",
          "is_from_customer": true,
          "created_at": "2024-01-15T14:30:00Z"
        },
        {
          "message": "We offer interior detailing, exterior detailing, and full detail packages...",
          "is_from_customer": false,
          "created_at": "2024-01-15T14:30:15Z"
        }
      ]
    }
  ]
}
```

---

## 🎨 Frontend UI Components Needed

### **1. Authentication Pages**
- [ ] Login page with email/password
- [ ] Register page with email/password/shop info
- [ ] Password reset flow
- [ ] Email verification

### **2. Dashboard Layout**
- [ ] Sidebar navigation
- [ ] Header with user menu
- [ ] Responsive design (mobile-friendly)
- [ ] Loading states and error handling

### **3. Shop Management** 
- [ ] Shop profile editing
- [ ] Branding customization (colors, greeting)
- [ ] API keys display (with copy buttons)
- [ ] Shop settings form

### **4. Service Management**
- [ ] Services list/table
- [ ] Add service form (name, description, price, duration)
- [ ] Edit/delete services
- [ ] Bulk actions

### **5. Widget Integration**
- [ ] Embed code generator
- [ ] Copy-to-clipboard functionality
- [ ] Widget preview/demo
- [ ] Theme and position customization

### **6. Subscription Management**
- [ ] Current plan display
- [ ] Usage metrics (progress bars)
- [ ] Plan comparison table
- [ ] Upgrade/downgrade buttons
- [ ] Billing history

### **7. Analytics Dashboard**
- [ ] Chat volume charts
- [ ] Popular topics
- [ ] Usage trends
- [ ] Chat history viewer

### **8. Settings**
- [ ] Account settings
- [ ] Notification preferences
- [ ] Billing information
- [ ] API documentation links

---

## 🔧 Frontend Development Setup

### **Recommended Tech Stack**
```json
{
  "framework": "Next.js 14 (App Router)",
  "styling": "Tailwind CSS",
  "language": "TypeScript", 
  "state": "Zustand or React Query",
  "forms": "React Hook Form + Zod",
  "ui": "shadcn/ui or Headless UI",
  "charts": "Recharts or Chart.js",
  "icons": "Lucide React"
}
```

### **Environment Variables**
```bash
# .env.local
NEXT_PUBLIC_API_URL=https://detailchatbot-api-dev.onrender.com/api/v1
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
NEXTAUTH_SECRET=your-nextauth-secret
NEXTAUTH_URL=http://localhost:3000
```

### **API Client Setup**
```typescript
// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

class ApiClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  setToken(token: string) {
    this.token = token;
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { Authorization: `Bearer ${this.token}` }),
        ...options.headers,
      },
    };

    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  }

  // Auth methods
  async login(email: string, password: string) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async register(userData: RegisterData) {
    return this.request('/auth/register', {
      method: 'POST', 
      body: JSON.stringify(userData),
    });
  }

  // Shop methods
  async createShop(shopData: CreateShopData) {
    return this.request('/shops', {
      method: 'POST',
      body: JSON.stringify(shopData),
    });
  }

  async getShops() {
    return this.request('/shops');
  }

  // Service methods
  async getServices() {
    return this.request('/services');
  }

  async createService(serviceData: CreateServiceData) {
    return this.request('/services', {
      method: 'POST',
      body: JSON.stringify(serviceData),
    });
  }

  // Plans methods
  async getPlans() {
    return this.request('/plans');
  }

  async subscribe(planId: number, billingCycle: 'monthly' | 'yearly') {
    return this.request('/plans/subscribe', {
      method: 'POST',
      body: JSON.stringify({ plan_id: planId, billing_cycle: billingCycle }),
    });
  }
}

export const apiClient = new ApiClient(API_BASE_URL!);
```

---

## 🚀 User Flows

### **New User Onboarding**
1. **Landing Page** → Sign Up
2. **Register** → Email verification  
3. **Create Shop** → Business details form
4. **Add Services** → Service creation wizard
5. **Get Widget Code** → Copy embed script
6. **Choose Plan** → Stripe checkout
7. **Dashboard** → Manage everything

### **Existing User Experience**
1. **Login** → Dashboard
2. **View Analytics** → Chat metrics, usage
3. **Manage Services** → CRUD operations
4. **Widget Settings** → Customize appearance  
5. **Billing** → Upgrade, view usage
6. **Support** → Help docs, contact

---

## 💰 Revenue-Critical Features

### **Must-Have for Launch** (Week 1-2)
- [ ] User registration/login
- [ ] Shop creation
- [ ] Service management
- [ ] Widget embed code display
- [ ] Basic subscription flow

### **Important for Growth** (Week 3-4)
- [ ] Usage analytics
- [ ] Plan upgrade flow
- [ ] Widget customization
- [ ] Chat history viewer
- [ ] Responsive design

### **Nice-to-Have** (Later)
- [ ] Advanced analytics
- [ ] A/B testing
- [ ] White-label options
- [ ] API documentation
- [ ] Multi-shop management

---

## 🎯 Success Metrics

**Primary KPIs:**
- **User Registrations** → Signups per day
- **Shop Creations** → Conversion from signup
- **Widget Deployments** → Active installations
- **Subscription Conversions** → Trial to paid
- **Monthly Recurring Revenue** → $5K target

**Secondary KPIs:**
- **Daily Active Users** → Dashboard engagement
- **Feature Adoption** → Service creation, customization
- **Support Tickets** → User experience issues
- **Churn Rate** → Subscription cancellations

---

## 🔗 Essential Links

- **API Documentation**: https://detailchatbot-api-dev.onrender.com/docs
- **Live API Base**: https://detailchatbot-api-dev.onrender.com/api/v1
- **Widget Example**: https://detailchatbot-api-dev.onrender.com/api/v1/widget/dc_pub_UFB2TgviE0ftW1PqbMdtfumQmZIT3O6z/embed.js
- **Stripe Dashboard**: https://dashboard.stripe.com
- **Target Customer**: Auto detailing shop owners (local businesses, $100K-500K revenue)

---

## 📞 Business Context

**Target Market**: 50,000+ auto detailing shops in US
**Average Customer**: Small business, needs digital lead generation
**Pain Point**: 80% rely on word-of-mouth, missing online opportunities  
**Value Prop**: "Turn website visitors into customers with AI chat"
**Pricing**: $19.99-$79.99/month (SaaS model)
**Goal**: Build, launch, and hit $5K MRR by January 2025

**This is a real business with real revenue potential. Build it right, ship it fast, and let's make money!** 💰🚀

---

*Last updated: January 2025 - Ready for frontend development*