# Quick Start: Deploy AMMINA to Render (You have MongoDB Atlas already!)

Since you already have MongoDB Atlas configured, here's your streamlined deployment guide.

## What You Need (2 minutes prep)

### 1. From MongoDB Atlas
- [ ] Get your connection string:
  1. Go to MongoDB Atlas → Database → Connect
  2. Click "Connect your application"
  3. Copy the connection string
  4. Replace `<password>` with your database password

**Your connection string should look like**:
```
mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/ammina_platform?retryWrites=true&w=majority
```

- [ ] Ensure Network Access allows `0.0.0.0/0` (required for Render)
  - If not: Network Access → Add IP → "Allow Access from Anywhere"

### 2. OpenAI API Key
- [ ] Get from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- [ ] Ensure you have credits/billing configured

### 3. Generate Security Keys

Run these commands locally:
```bash
# Generate Flask SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Generate ADMIN_REGISTRATION_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Save both outputs! You'll need them for Render.

## Deploy to Render (10 minutes)

### Step 1: Update GitHub Repo URL

1. Open [render.yaml](render.yaml)
2. Line 6: Replace `YOUR_GITHUB_USERNAME` with your actual username:
   ```yaml
   repo: https://github.com/your_actual_username/ARMMI-pandasi
   ```
3. Save, commit, and push:
   ```bash
   git add render.yaml
   git commit -m "Configure Render deployment"
   git push origin main
   ```

### Step 2: Create Render Service

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Sign up/login (connect GitHub account)
3. Click **"New +"** → **"Blueprint"**
4. Select repository: `ARMMI-pandasi`
5. Click **"Apply"**

### Step 3: Set Environment Variables

Render creates your service. Now configure it:

1. Go to your service (e.g., `ammina-platform`)
2. Click **"Environment"** tab
3. Add these variables:

**REQUIRED - Set These Now**:
```
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/ammina_platform
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
SECRET_KEY=<paste the generated 64-char hex string>
ADMIN_REGISTRATION_KEY=<paste the generated admin key>
```

**Already configured in render.yaml** (verify these exist):
```
FLASK_ENV=production
FLASK_DEBUG=False
SESSION_COOKIE_SECURE=True
MONGODB_DB_NAME=ammina_platform
```

4. Click **"Save Changes"**

### Step 4: Deploy & Wait

1. Render automatically starts building (watch "Logs" tab)
2. First build takes ~5-10 minutes
3. Look for "Your service is live 🎉"

### Step 5: Test Your App

1. Copy your URL: `https://ammina-platform.onrender.com`
2. Visit in browser
3. Register a test user
4. Upload a CSV file
5. Try a natural language query!

## That's It! 🎉

Your app is now live. The URL is: `https://your-app.onrender.com`

## Important Notes

### Free Tier Behavior
- **Spins down** after 15 minutes of inactivity
- **Cold start** takes ~30-60 seconds on first request
- **Upgrade to Starter** ($7/month) for always-on service

### Auto-Deploy
- Every `git push` to `main` automatically deploys
- Disable in Render settings if you want manual control

### Costs
- **Render**: $0 (free tier) or $7 (Starter)
- **MongoDB Atlas**: $0 (if using free M0 tier)
- **OpenAI API**: Usage-based (~$1-5/month for light use)

## Quick Troubleshooting

### Build fails?
- Check Render logs for specific error
- Verify `Dockerfile` and `requirements.txt` are present

### Can't connect to MongoDB?
- Verify MongoDB Atlas allows `0.0.0.0/0` in Network Access
- Check connection string format and password
- Ensure cluster is "Active" (not paused)

### OpenAI errors?
- Verify API key is valid
- Check billing/credits in OpenAI dashboard

### App won't start?
- Check all 4 required environment variables are set
- Review Render logs for error messages
- Verify `SECRET_KEY` and `ADMIN_REGISTRATION_KEY` are set

## Next Steps

1. **Share your URL** with users
2. **Create admin account** using `ADMIN_REGISTRATION_KEY`
3. **Monitor usage**:
   - Render dashboard for app logs
   - MongoDB Atlas for storage
   - OpenAI dashboard for API costs

## Need More Details?

- Full deployment guide: [README.md](README.md#-deployment)
- MongoDB setup (if needed): [MONGODB_SETUP.md](MONGODB_SETUP.md)
- Complete checklist: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
- Environment variables: [.env.example](.env.example)

---

**Estimated total time**: 15-20 minutes from start to live app!
