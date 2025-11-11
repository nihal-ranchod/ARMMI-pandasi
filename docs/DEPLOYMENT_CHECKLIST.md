# AMMINA Platform - Render Deployment Checklist

Use this checklist to deploy your AMMINA platform to Render.com step by step.

## Pre-Deployment Checklist

### 1. GitHub Repository
- [ ] Code is pushed to GitHub
- [ ] Repository is public or Render has access
- [ ] Main branch is up to date
- [ ] Files present: `Dockerfile`, `render.yaml`, `.env.example`

### 2. MongoDB Atlas Setup
- [ ] MongoDB Atlas account created
- [ ] Free M0 cluster created and **Active**
- [ ] Database user created (username & password saved)
- [ ] Network access configured (0.0.0.0/0 allowed)
- [ ] Connection string obtained and saved securely

**Connection string format**:
```
mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/ammina_platform?retryWrites=true&w=majority
```

### 3. OpenAI API Setup
- [ ] OpenAI account created at [platform.openai.com](https://platform.openai.com)
- [ ] API key generated (starts with `sk-proj-...`)
- [ ] Billing configured (credit card added or credits available)
- [ ] API key saved securely

### 4. Generate Security Keys

Run these commands locally and save the outputs:

```bash
# Generate Flask SECRET_KEY
python -c "import secrets; print('SECRET_KEY:', secrets.token_hex(32))"

# Generate ADMIN_REGISTRATION_KEY
python -c "import secrets; print('ADMIN_KEY:', secrets.token_urlsafe(32))"
```

- [ ] `SECRET_KEY` generated and saved
- [ ] `ADMIN_REGISTRATION_KEY` created and saved

## Deployment Steps

### Step 1: Update render.yaml
- [ ] Open [render.yaml](render.yaml)
- [ ] Update `repo:` line with your GitHub username
  ```yaml
  repo: https://github.com/YOUR_USERNAME/ARMMI-pandasi
  ```
- [ ] Save and commit changes
- [ ] Push to GitHub

### Step 2: Create Render Account
- [ ] Go to [render.com](https://render.com)
- [ ] Sign up (free account)
- [ ] Verify email if required
- [ ] Connect GitHub account to Render

### Step 3: Deploy Using Blueprint (Recommended)

#### 3a. Create Blueprint
- [ ] Log in to [Render Dashboard](https://dashboard.render.com)
- [ ] Click **"New +"** → **"Blueprint"**
- [ ] Select your repository: `ARMMI-pandasi`
- [ ] Render detects `render.yaml` automatically
- [ ] Click **"Apply"**
- [ ] Wait for service creation (1-2 minutes)

#### 3b. Configure Environment Variables
- [ ] Go to your new service (e.g., `ammina-platform`)
- [ ] Click **"Environment"** tab
- [ ] Add/verify these variables:

**Required Variables**:
```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/ammina_platform
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxx
SECRET_KEY=<your_generated_secret_key>
ADMIN_REGISTRATION_KEY=<your_generated_admin_key>
FLASK_ENV=production
FLASK_DEBUG=False
SESSION_COOKIE_SECURE=True
```

**Optional Variables** (already set in render.yaml):
```
MONGODB_DB_NAME=ammina_platform
MAX_CONTENT_LENGTH=104857600
MAX_ROWS=1000000
MAX_COLUMNS=1000
QUERY_TIMEOUT=300
MAX_QUERIES_PER_MINUTE=10
CORS_ORIGINS=*
```

- [ ] All required variables set
- [ ] Click **"Save Changes"**

#### 3c. Trigger Deployment
- [ ] Render automatically starts building
- [ ] Monitor **"Logs"** tab for progress
- [ ] Wait for build completion (5-10 minutes first time)
- [ ] Look for: `"Your service is live 🎉"` or similar message

### Step 4: Verify Deployment

#### 4a. Get Your URL
- [ ] Copy your Render URL from dashboard (e.g., `https://ammina-platform.onrender.com`)
- [ ] Save URL for sharing with users

#### 4b. Test Basic Functionality
- [ ] Visit your Render URL in browser
- [ ] Homepage loads without errors
- [ ] No console errors in browser DevTools

#### 4c. Test User Registration
- [ ] Click "Register" or "Sign Up"
- [ ] Create a test account:
  - Username: `test_user`
  - Email: `test@example.com`
  - Password: (any secure password)
- [ ] Registration succeeds
- [ ] Redirected to dashboard/login

#### 4d. Test Login
- [ ] Log in with test account
- [ ] Dashboard loads successfully
- [ ] No errors in Render logs

#### 4e. Test File Upload
- [ ] Navigate to "Datasets" or "Upload"
- [ ] Upload a small CSV or Excel file
- [ ] File uploads successfully
- [ ] Data appears in dataset list
- [ ] Preview shows correct data

#### 4f. Test Natural Language Query
- [ ] Go to "Query" section
- [ ] Select uploaded dataset
- [ ] Ask a simple question (e.g., "How many rows are there?")
- [ ] Query executes successfully
- [ ] Result displays correctly
- [ ] Query appears in history

#### 4g. Verify Database (Optional)
- [ ] Log in to MongoDB Atlas
- [ ] Go to "Browse Collections"
- [ ] See `ammina_platform` database
- [ ] Collections present: `users`, `datasets`, `query_history`
- [ ] Test user data visible

### Step 5: Post-Deployment Configuration

#### 5a. Custom Domain (Optional)
- [ ] Purchase domain (or use existing)
- [ ] In Render: Settings → Custom Domains
- [ ] Click "Add Custom Domain"
- [ ] Follow DNS configuration instructions
- [ ] Wait for SSL certificate (automatic, ~5 minutes)
- [ ] Update `CORS_ORIGINS` if needed

#### 5b. Update CORS Origins (Production)
If using custom domain, update CORS:
- [ ] Go to Environment tab
- [ ] Change `CORS_ORIGINS` from `*` to your domain
  ```
  CORS_ORIGINS=https://yourdomain.com
  ```
- [ ] Save changes (triggers redeploy)

#### 5c. Enable Auto-Deploy
- [ ] Go to Settings tab
- [ ] Find "Auto-Deploy" section
- [ ] Ensure "Auto-Deploy" is enabled for `main` branch
- [ ] Now git pushes will automatically deploy!

#### 5d. Set Up Monitoring (Optional)
- [ ] Configure Render health checks (already set in render.yaml)
- [ ] Set up MongoDB Atlas alerts:
  - Database → Alerts
  - Create alert for storage > 80%
  - Create alert for connection spikes
- [ ] Add your email for notifications

### Step 6: Create Admin Account (if needed)

- [ ] Visit your application URL
- [ ] Go to registration page
- [ ] Enter admin details:
  - Username: `admin` (or your choice)
  - Email: your email
  - **Admin Key**: Enter your `ADMIN_REGISTRATION_KEY`
- [ ] Complete registration
- [ ] Admin account created (verify in database)

## Troubleshooting

### Build Fails
- [ ] Check Render logs for specific error
- [ ] Verify `Dockerfile` syntax
- [ ] Ensure all packages in `requirements.txt` are available
- [ ] Try manual deploy: Render dashboard → Manual Deploy

### Application Won't Start
- [ ] Check Render logs for error messages
- [ ] Verify `MONGODB_URI` is correct
- [ ] Test MongoDB connection from Atlas dashboard
- [ ] Verify `OPENAI_API_KEY` is valid
- [ ] Ensure `SECRET_KEY` is set

### MongoDB Connection Errors
- [ ] Verify cluster is "Active" in Atlas
- [ ] Check Network Access allows `0.0.0.0/0`
- [ ] Confirm database user exists
- [ ] Test connection string format
- [ ] Check for special characters in password (URL encode)

### OpenAI API Errors
- [ ] Verify API key is active
- [ ] Check OpenAI billing/credits
- [ ] Review rate limits
- [ ] Check logs for specific error codes

### Slow Performance
**Expected on Free Tier**:
- Free tier spins down after 15 minutes of inactivity
- Cold starts take ~30-60 seconds
- First request after idle is slow

**Solutions**:
- [ ] Upgrade to Starter tier ($7/month) for always-on
- [ ] Accept cold starts for free tier
- [ ] Use cron job to ping app every 10 minutes (workaround)

## Success Criteria

Your deployment is successful when:
- [ ] ✅ Application URL loads without errors
- [ ] ✅ User registration and login work
- [ ] ✅ File uploads succeed
- [ ] ✅ Natural language queries execute correctly
- [ ] ✅ Query history saves properly
- [ ] ✅ Data persists in MongoDB Atlas
- [ ] ✅ No critical errors in Render logs
- [ ] ✅ SSL certificate active (HTTPS URL)

## Next Steps After Deployment

### Share Your Application
- [ ] Share Render URL with users: `https://your-app.onrender.com`
- [ ] Provide registration instructions
- [ ] Share admin registration key securely (if applicable)

### Monitor Usage
- [ ] Check Render dashboard daily for errors
- [ ] Monitor MongoDB Atlas storage usage
- [ ] Track OpenAI API costs
- [ ] Review query patterns in app logs

### Plan for Scaling
- [ ] Monitor free tier limits:
  - Render: 750 hours/month (always-on not included)
  - MongoDB Atlas: 512MB storage
  - OpenAI: Pay-per-use
- [ ] Plan upgrade path if limits approached

### Maintenance
- [ ] Set reminder to backup MongoDB data (weekly/monthly)
- [ ] Review logs periodically for issues
- [ ] Update dependencies in `requirements.txt` quarterly
- [ ] Rotate `SECRET_KEY` and passwords periodically (6 months)

## Cost Summary (Current Setup)

| Service | Tier | Monthly Cost |
|---------|------|--------------|
| Render Web Service | Free | $0 |
| MongoDB Atlas | M0 Free | $0 |
| OpenAI API | Usage-based | ~$1-5 (varies) |
| **Total** | - | **~$1-5/month** |

**To upgrade**:
- Render Starter: $7/month (always-on, better performance)
- MongoDB M2: $9/month (2GB storage, backups)

## Resources

- **Render Documentation**: [render.com/docs](https://render.com/docs)
- **MongoDB Atlas Setup**: See [MONGODB_SETUP.md](MONGODB_SETUP.md)
- **Environment Variables**: See [.env.example](.env.example)
- **Deployment Guide**: See [README.md](README.md#-deployment)

---

## Support

If you encounter issues:
1. Check Render logs first
2. Verify all environment variables are set correctly
3. Test MongoDB connection in Atlas dashboard
4. Review this checklist for missed steps
5. Check AMMINA application logs for detailed errors

**Need help?** Open an issue on GitHub or check Render community forums.

---

**Date Deployed**: _________________
**Deployed By**: _________________
**Application URL**: _________________
**MongoDB Cluster**: _________________
