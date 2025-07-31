# Development Deployment Guide

This guide walks you through deploying the DetailChatbot.ai backend to **Render DEV environment**.

## 🚀 Quick Deploy to Render (DEV)

### Step 1: Create Render Account & Services

1. **Go to [Render.com](https://render.com)** and sign up/login
2. **Connect your GitHub repository** 
3. **Create services using `render-dev.yaml`**:
   - Click "New +" → "Blueprint"
   - Connect your repo: `detailchatbot-backend`
   - Use branch: `dev-refactor` 
   - Render will auto-detect `render-dev.yaml`

### Step 2: Configure Environment Variables

In your **Render Dashboard** → **detailchatbot-api-dev** → **Environment**:

#### Required Environment Variables:
```bash
# Database (will be auto-populated by Render when DB is created)
DATABASE_URL=<auto-populated-by-render>

# Security (GENERATE NEW KEYS!)
SECRET_KEY=<generate-new-256-bit-key>
ALGORITHM=HS256

# OpenAI (use your real API key)
OPENAI_API_KEY=sk-proj-your-openai-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Stripe (USE TEST KEYS for dev)
STRIPE_SECRET_KEY=sk_test_your-stripe-test-key
STRIPE_WEBHOOK_SECRET=whsec_test-webhook-secret

# Email (Optional - use Mailtrap for testing)
SMTP_HOST=smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USERNAME=your-mailtrap-username
SMTP_PASSWORD=your-mailtrap-password
SMTP_TLS=true

# App Settings
ENVIRONMENT=development
DEBUG=true
FRONTEND_URL=https://your-frontend-dev.vercel.app

# CORS (allow your dev frontend)
# These are already configured in code for development
```

### Step 3: Generate Secure Keys

**Generate SECRET_KEY** (run locally):
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Get Stripe Test Keys**:
1. Go to [Stripe Dashboard](https://dashboard.stripe.com/test/apikeys)
2. Copy your **Secret Key** (starts with `sk_test_`)
3. Create webhook endpoint for your dev URL
4. Copy **Webhook Secret** (starts with `whsec_`)

### Step 4: Database Setup

The PostgreSQL database will be created automatically via `render-dev.yaml`. After deployment:

1. **Check database connection** in Render logs
2. **Run migrations** (if needed):
   ```bash
   # This should happen automatically, but if needed:
   # Connect to your Render shell and run:
   alembic upgrade head
   ```

### Step 5: Test Deployment

Once deployed, your API will be available at:
```
https://detailchatbot-api-dev.onrender.com
```

**Test endpoints**:
```bash
# Health check
curl https://detailchatbot-api-dev.onrender.com/health

# API docs
https://detailchatbot-api-dev.onrender.com/docs

# Test registration
curl -X POST https://detailchatbot-api-dev.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "TestPass123!"}'
```

## 🔧 Development Workflow

### Making Changes
1. **Push to `dev-refactor` branch**
2. **Render auto-deploys** on git push
3. **Check logs** in Render dashboard
4. **Test changes** at your dev URL

### Monitoring
- **Render Dashboard**: View logs, metrics, environment
- **API Docs**: `https://your-dev-url.onrender.com/docs`
- **Database**: Use Render's built-in database browser

### Debugging
```bash
# View recent logs
# Go to Render Dashboard → Your Service → Logs

# Connect to database (if needed)
# Use connection string from Render dashboard
psql $DATABASE_URL
```

## 🧪 Testing Your Dev API

### Test Authentication Flow:
```bash
# 1. Register user
curl -X POST https://your-dev-url.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@shop.com", "password": "TestPass123!"}'

# 2. Login (get token)
curl -X POST https://your-dev-url.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@shop.com", "password": "TestPass123!"}'

# 3. Create shop (use token from login)
curl -X POST https://your-dev-url.onrender.com/api/v1/shops \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Detailing", "address": "123 Main St", "phone": "555-1234"}'
```

### Test Chat Widget:
```bash
# Get widget (use shop API key from shop creation response)
curl https://your-dev-url.onrender.com/api/v1/widget/dc_pub_YOUR_API_KEY/embed.js

# Test chat
curl -X POST https://your-dev-url.onrender.com/api/v1/chat/dc_pub_YOUR_API_KEY \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, what services do you offer?", "session_id": "test123"}'
```

## ⚠️ Important Notes

### Security:
- **Never use production keys** in dev environment
- **Always use Stripe test mode** for development
- **Regenerate SECRET_KEY** for production deployment

### Database:
- **Dev database** is separate from production
- **Data may be reset** during development
- **No automatic backups** on starter plan

### Performance:
- **Render free tier** may have cold starts (30 seconds)
- **Upgrade to paid plan** for better performance
- **Use paid PostgreSQL** for production

### CORS:
- **Dev environment** allows `localhost` origins
- **Update ALLOWED_ORIGINS** in `config.py` if needed for your frontend

## 🎯 Next Steps

Once your DEV deployment is working:

1. **Build frontend** against this DEV API
2. **Test all features** thoroughly
3. **Iterate quickly** with auto-deploys
4. **Prepare production deployment** when ready

Your dev API will be live at: `https://detailchatbot-api-dev.onrender.com`

Ready to make money! 💰